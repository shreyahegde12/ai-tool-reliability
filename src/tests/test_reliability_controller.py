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
