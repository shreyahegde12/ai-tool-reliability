import unittest
import os

from src.modules.MiniAgent import ToolEnvironment
from src.modules.reliability_controller import ReliabilityController


ENABLED = {
    "enabled": True,
    "require_inspection_before_patch": True,
    "require_verification_before_submit": True,
    "auto_rollback_on_regression": True,
    "block_repeated_failed_patch": True,
    "force_final_verification": True,
    "selective_rollback": True,
}


class ReliabilityControllerTests(unittest.TestCase):
    def setUp(self):
        self.controller = ReliabilityController(ENABLED)
        self.patch = {
            "router_name": "r1.cfg",
            "search": "router bgp 65002",
            "replace": "router bgp 65001",
        }

    def check(self, tool, params=None, inspected=(), pending=(), prefill=False):
        return self.controller.before_tool(
            tool,
            params or {},
            inspected_routers=inspected,
            pending_patches=pending,
            context_prefill=prefill,
        )

    def test_read_only_tools_are_not_guarded(self):
        decision = self.check("inspect_config", {"router_name": "r1.cfg"})
        self.assertTrue(decision.allowed)
        self.assertEqual(self.controller.get_summary()["actions_checked"], 0)

    def test_patch_requires_inspection(self):
        decision = self.check("apply_patch", self.patch)
        self.assertFalse(decision.allowed)
        self.assertEqual(decision.reason, "router_not_inspected")

        decision = self.check(
            "apply_patch", self.patch, inspected={"r1.cfg"}
        )
        self.assertTrue(decision.allowed)

    def test_evidence_alignment_nudges_once_per_unflagged_router(self):
        self.controller = ReliabilityController(
            {**ENABLED, "evidence_alignment": True}
        )
        self.controller.set_diagnosis_evidence(
            [("r2.cfg", "bgp_local_asn_mismatch")]
        )
        decision = self.check("apply_patch", self.patch, inspected={"r1.cfg"})
        self.assertFalse(decision.allowed)
        self.assertEqual(decision.decision, "evidence_nudge")
        self.assertIn("r2.cfg", decision.feedback)

        decision = self.check("apply_patch", self.patch, inspected={"r1.cfg"})
        self.assertTrue(decision.allowed)
        summary = self.controller.get_summary()
        self.assertEqual(summary["evidence_nudges"], 1)
        self.assertEqual(summary["actions_rejected"], 0)

    def test_evidence_alignment_allows_flagged_or_after_inspection(self):
        self.controller = ReliabilityController(
            {**ENABLED, "evidence_alignment": True}
        )
        self.controller.set_diagnosis_evidence(
            [("r1.cfg", "link_subnet_mismatch"), ("r2.cfg", "duplicate_address")]
        )
        decision = self.check("apply_patch", self.patch, inspected={"r1.cfg"})
        self.assertTrue(decision.allowed)

        other = dict(self.patch, router_name="r3.cfg")
        decision = self.check(
            "apply_patch", other, inspected={"r2.cfg", "r3.cfg"}
        )
        self.assertTrue(decision.allowed)

    def test_evidence_alignment_inactive_without_findings_or_flag(self):
        self.controller = ReliabilityController(
            {**ENABLED, "evidence_alignment": True}
        )
        decision = self.check("apply_patch", self.patch, inspected={"r1.cfg"})
        self.assertTrue(decision.allowed)

        self.controller = ReliabilityController(ENABLED)
        self.controller.set_diagnosis_evidence(
            [("r2.cfg", "bgp_local_asn_mismatch")]
        )
        decision = self.check("apply_patch", self.patch, inspected={"r1.cfg"})
        self.assertTrue(decision.allowed)

    def test_prefilled_config_counts_as_visible(self):
        decision = self.check("apply_patch", self.patch, prefill=True)
        self.assertTrue(decision.allowed)

    def test_no_op_patch_is_rejected(self):
        patch = dict(self.patch)
        patch["replace"] = patch["search"] + "  "
        decision = self.check(
            "apply_patch", patch, inspected={"r1.cfg"}
        )
        self.assertFalse(decision.allowed)
        self.assertEqual(decision.reason, "no_op_patch")

    def test_submit_requires_current_state_verification(self):
        self.controller.mark_patch_applied()
        decision = self.check("submit", pending=[self.patch])
        self.assertFalse(decision.allowed)
        self.assertEqual(decision.decision, "require_verification")

        verification = {"side_effects": 0}
        self.controller.evaluate_verification(verification, [self.patch])
        decision = self.check("submit")
        self.assertTrue(decision.allowed)

    def test_regressing_patch_is_remembered(self):
        decision = self.controller.evaluate_verification(
            {"side_effects": 2},
            [{
                "router": self.patch["router_name"],
                "search": self.patch["search"],
                "replace": self.patch["replace"],
            }],
        )
        self.assertEqual(decision.decision, "selective_rollback")
        self.controller.mark_failed_patches([{
            "router": self.patch["router_name"],
            "search": self.patch["search"],
            "replace": self.patch["replace"],
        }])

        repeated = self.check(
            "apply_patch", self.patch, inspected={"r1.cfg"}
        )
        self.assertFalse(repeated.allowed)
        self.assertEqual(repeated.reason, "repeated_failed_patch")


class NetBenefitControllerTests(unittest.TestCase):
    """Tests for the net-benefit acceptance mode."""

    def setUp(self):
        self.config = {
            **ENABLED,
            "net_benefit_ratio": 1.0,
        }
        self.controller = ReliabilityController(self.config)

    def test_net_benefit_accepts_when_fixes_exceed_regressions(self):
        # Checkpoint starts at 0 fixed, 0 regressions.
        decision = self.controller.evaluate_verification(
            {"fixed": 5, "side_effects": 2},
            [{"router": "r1.cfg", "search": "a", "replace": "b"}],
        )
        self.assertTrue(decision.allowed)
        self.assertEqual(decision.decision, "accept_net_benefit")
        self.assertEqual(self.controller.checkpoint_fixed, 5)
        self.assertEqual(self.controller.checkpoint_side_effects, 2)

    def test_net_benefit_rejects_when_regressions_exceed_fixes(self):
        decision = self.controller.evaluate_verification(
            {"fixed": 1, "side_effects": 3},
            [{"router": "r1.cfg", "search": "a", "replace": "b"}],
        )
        self.assertFalse(decision.allowed)
        self.assertIn("rollback", decision.decision)

    def test_net_benefit_uses_delta_from_checkpoint(self):
        # Accept first verification: 5 fixed, 1 regression.
        self.controller.evaluate_verification(
            {"fixed": 5, "not_fixed": 5, "side_effects": 1}, []
        )
        self.assertEqual(self.controller.checkpoint_fixed, 5)
        self.assertEqual(self.controller.checkpoint_side_effects, 1)

        # Second verification: 8 fixed, 3 regressions.
        # Delta: +3 fixed, +2 regressions → net benefit (3 >= 1.0 * 2).
        decision = self.controller.evaluate_verification(
            {"fixed": 8, "not_fixed": 2, "side_effects": 3},
            [{"router": "r2.cfg", "search": "x", "replace": "y"}],
        )
        self.assertTrue(decision.allowed)
        self.assertEqual(decision.decision, "accept_net_benefit")

    def test_net_benefit_rejects_when_delta_insufficient(self):
        # Accept: 5 fixed, 1 regression.
        self.controller.evaluate_verification(
            {"fixed": 5, "side_effects": 1}, []
        )

        # Next: 6 fixed, 4 regressions. Delta: +1 fixed, +3 reg → reject.
        decision = self.controller.evaluate_verification(
            {"fixed": 6, "side_effects": 4},
            [{"router": "r2.cfg", "search": "x", "replace": "y"}],
        )
        self.assertFalse(decision.allowed)

    def test_net_benefit_ratio_2_requires_double(self):
        controller = ReliabilityController({
            **ENABLED,
            "net_benefit_ratio": 2.0,
        })
        # 3 fixed, 2 regressions — ratio 1.5, below 2.0.
        decision = controller.evaluate_verification(
            {"fixed": 3, "side_effects": 2}, [{"router": "r1.cfg"}]
        )
        self.assertFalse(decision.allowed)

        # 4 fixed, 2 regressions — ratio 2.0, exactly meets threshold.
        controller2 = ReliabilityController({
            **ENABLED,
            "net_benefit_ratio": 2.0,
        })
        decision = controller2.evaluate_verification(
            {"fixed": 4, "side_effects": 2}, [{"router": "r1.cfg"}]
        )
        self.assertTrue(decision.allowed)

    def test_strict_mode_rejects_any_regression(self):
        controller = ReliabilityController(ENABLED)  # no net_benefit_ratio
        decision = controller.evaluate_verification(
            {"fixed": 10, "side_effects": 1},
            [{"router": "r1.cfg"}],
        )
        self.assertFalse(decision.allowed)

    def test_zero_regressions_always_accepted(self):
        decision = self.controller.evaluate_verification(
            {"fixed": 5, "not_fixed": 5, "side_effects": 0}, []
        )
        self.assertTrue(decision.allowed)
        self.assertEqual(decision.decision, "accept")

    def test_zero_regressions_cannot_discard_previous_repairs(self):
        self.controller.evaluate_verification(
            {"fixed": 5, "not_fixed": 5, "side_effects": 0}, []
        )
        decision = self.controller.evaluate_verification(
            {"fixed": 4, "not_fixed": 6, "side_effects": 0},
            [{"router": "r2.cfg"}],
        )
        self.assertFalse(decision.allowed)
        self.assertEqual(decision.reason, "verification_regression")

    def test_existing_regressions_do_not_block_later_improvement(self):
        self.controller.evaluate_verification(
            {"fixed": 5, "not_fixed": 5, "side_effects": 2}, []
        )
        decision = self.controller.evaluate_verification(
            {"fixed": 7, "not_fixed": 3, "side_effects": 2},
            [{"router": "r2.cfg"}],
        )
        self.assertTrue(decision.allowed)
        self.assertEqual(decision.decision, "accept_net_benefit")

    def test_invalid_net_benefit_ratio_is_rejected(self):
        for value in (0, -1, float("inf"), float("nan")):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    ReliabilityController({
                        **ENABLED,
                        "net_benefit_ratio": value,
                    })

    def test_summary_tracks_net_benefit_accepted(self):
        self.controller.evaluate_verification(
            {"fixed": 5, "side_effects": 2}, []
        )
        summary = self.controller.get_summary()
        self.assertEqual(summary["net_benefit_accepted"], 1)
        self.assertEqual(summary["net_benefit_ratio"], 1.0)


class ReliabilityEnvironmentTests(unittest.TestCase):
    def make_environment(self, side_effects):
        return ToolEnvironment(
            faulty_configs={"r1.cfg": "hostname r1\nrouter bgp 65002\n"},
            original_configs={"r1.cfg": "hostname r1\nrouter bgp 65001\n"},
            full_faulty_configs={
                "r1.cfg": "hostname r1\nrouter bgp 65002\n"
            },
            topology={},
            violated_specs=["reachability,r1,10.0.0.0/24,,,broken_removed"],
            specification_csv_path=None,
            original_specs=[],
            net_env=lambda **kwargs: ["processed"],
            evaluator=lambda **kwargs: {
                "summary": {
                    "fixed": 1,
                    "not_fixed": 0,
                    "side_effects": side_effects,
                    "fix_rate": 1.0,
                },
                "results": {},
            },
            evaluator_kwargs={},
            reliability_config=ENABLED,
        )

    def test_regression_automatically_restores_checkpoint(self):
        env = self.make_environment(side_effects=1)
        self.assertEqual(
            env.reliability_controller.checkpoint_not_fixed, 1
        )
        env.execute_tool("inspect_config", {"router_name": "r1.cfg"})
        env.execute_tool(
            "apply_patch",
            {
                "router_name": "r1.cfg",
                "search": "router bgp 65002",
                "replace": "router bgp 65001",
            },
        )

        observation = env.execute_tool("verify", {})

        self.assertIn("Selective rollback retained 0", observation)
        self.assertIn("router bgp 65002", env.current_configs["r1.cfg"])
        self.assertEqual(env.pending_patches, [])
        self.assertEqual(
            env.transaction_history[-1]["status"], "full_rollback"
        )
        self.assertEqual(
            env.get_summary()["reliability"]["automatic_rollbacks"], 1
        )

    def test_verified_state_can_be_submitted(self):
        env = self.make_environment(side_effects=0)
        blocked = env.execute_tool("submit", {})
        self.assertIn("blocked submission", blocked)

        env.execute_tool("verify", {})
        submitted = env.execute_tool("submit", {})
        self.assertEqual(submitted, ToolEnvironment.SUBMIT_SIGNAL)

    def test_finalization_verifies_last_step_patch(self):
        env = self.make_environment(side_effects=0)
        env.execute_tool("inspect_config", {"router_name": "r1.cfg"})
        env.execute_tool(
            "apply_patch",
            {
                "router_name": "r1.cfg",
                "search": "router bgp 65002",
                "replace": "router bgp 65001",
            },
        )

        observation = env.finalize_reliability_state()

        self.assertIn("Checkpoint updated", observation)
        self.assertEqual(env.pending_patches, [])
        summary = env.get_summary()["reliability"]
        self.assertEqual(summary["forced_final_verifications"], 1)

    def test_selective_rollback_keeps_safe_patch_only(self):
        def read_configs(local_scenario_path):
            config_dir = os.path.join(local_scenario_path, "configs")
            contents = []
            for name in sorted(os.listdir(config_dir)):
                with open(os.path.join(config_dir, name)) as config_file:
                    contents.append(config_file.read())
            return "\n".join(contents)

        env = ToolEnvironment(
            faulty_configs={
                "r1.cfg": "hostname r1\nvalue old\n",
                "r2.cfg": "hostname r2\nvalue old\n",
            },
            original_configs={},
            full_faulty_configs={
                "r1.cfg": "hostname r1\nvalue old\n",
                "r2.cfg": "hostname r2\nvalue old\n",
            },
            topology={},
            violated_specs=[],
            specification_csv_path=None,
            original_specs=[],
            net_env=read_configs,
            evaluator=lambda **kwargs: {
                "summary": {
                    "fixed": int("safe" in kwargs["compared_spec"]),
                    "not_fixed": 0,
                    "side_effects": int("unsafe" in kwargs["compared_spec"]),
                    "fix_rate": 1.0,
                },
                "results": {},
            },
            evaluator_kwargs={},
            reliability_config=ENABLED,
        )
        for router in ("r1.cfg", "r2.cfg"):
            env.execute_tool("inspect_config", {"router_name": router})
        env.execute_tool("apply_patch", {
            "router_name": "r1.cfg",
            "search": "value old",
            "replace": "value safe",
        })
        env.execute_tool("apply_patch", {
            "router_name": "r2.cfg",
            "search": "value old",
            "replace": "value unsafe",
        })

        observation = env.execute_tool("verify", {})

        self.assertIn("retained 1 safe patch", observation)
        self.assertIn("value safe", env.current_configs["r1.cfg"])
        self.assertIn("value old", env.current_configs["r2.cfg"])
        transaction = env.transaction_history[-1]
        self.assertEqual(transaction["retained_patch_ids"], [1])
        self.assertEqual(transaction["rejected_patch_ids"], [2])


if __name__ == "__main__":
    unittest.main()
