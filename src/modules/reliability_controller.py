"""Policy enforcement for risky MiniAgent tool calls.

The controller is intentionally independent of the LLM and Batfish.  It
checks state-changing actions before execution and consumes structured
verification results afterwards.  This keeps reliability decisions
deterministic, auditable, and easy to disable for baseline experiments.
"""

from dataclasses import dataclass
from datetime import datetime
import math
from typing import Any, Dict, Iterable, List, Mapping, Optional, Set, Tuple


@dataclass(frozen=True)
class ReliabilityDecision:
    """Result of a reliability-policy check."""

    allowed: bool
    decision: str
    reason: str
    feedback: str = ""


def _config_value(config: Any, name: str, default: Any) -> Any:
    """Read a value from a dict-like or attribute-based config object."""
    if config is None:
        return default
    if isinstance(config, Mapping):
        return config.get(name, default)
    return getattr(config, name, default)


class ReliabilityController:
    """Deterministic guard for patching, verification, and submission."""

    def __init__(self, config: Optional[Any] = None):
        self.enabled = bool(_config_value(config, "enabled", False))
        self.require_inspection = bool(_config_value(
            config, "require_inspection_before_patch", True
        ))
        self.require_verified_submit = bool(_config_value(
            config, "require_verification_before_submit", True
        ))
        self.auto_rollback = bool(_config_value(
            config, "auto_rollback_on_regression", True
        ))
        self.block_repeated_failed_patch = bool(_config_value(
            config, "block_repeated_failed_patch", True
        ))
        self.force_final_verification = bool(_config_value(
            config, "force_final_verification", True
        ))
        self.selective_rollback = bool(_config_value(
            config, "selective_rollback", True
        ))
        # Evidence alignment: before the first patch on a router that the
        # deterministic diagnosis did not flag, ask the agent to look at the
        # flagged routers first.  It is a one-time nudge per router, not a
        # block, because the diagnosis can be wrong.
        self.evidence_alignment = bool(_config_value(
            config, "evidence_alignment", False
        ))
        self.evidence_top_k = int(_config_value(config, "evidence_top_k", 3))

        # Net-benefit acceptance: accept a verification if the number of
        # newly fixed specs exceeds regressions by at least this ratio.
        # "strict" (the default) means zero tolerance — any regression
        # triggers rollback.  A float like 2.0 means "accept when
        # fixed_delta >= 2 * regression_delta".
        nb = _config_value(config, "net_benefit_ratio", "strict")
        if isinstance(nb, str) and nb.lower() == "strict":
            self.net_benefit_ratio: Optional[float] = None  # strict mode
        else:
            self.net_benefit_ratio = float(nb)
            if (
                not math.isfinite(self.net_benefit_ratio)
                or self.net_benefit_ratio <= 0
            ):
                raise ValueError(
                    "net_benefit_ratio must be 'strict' or a positive "
                    "finite number"
                )

        self.current_state_verified = False
        self.checkpoint_verified = False
        self.checkpoint_fixed: int = 0
        self.checkpoint_not_fixed: int = 0
        self.checkpoint_side_effects: int = 0
        self.checkpoint_score: float = 0.0
        self.failed_patch_fingerprints: Set[str] = set()
        self.flagged_routers: List[Tuple[str, str]] = []
        self.evidence_nudged_routers: Set[str] = set()
        self.decision_log = []

    def set_diagnosis_evidence(
        self,
        flagged: Iterable[Tuple[str, str]],
    ) -> None:
        """Store the latest diagnosis as ranked (router, check) pairs."""
        self.flagged_routers = list(flagged)[: self.evidence_top_k]

    def _evidence_nudge(
        self,
        router_name: str,
        inspected: Set[str],
        context_prefill: bool,
    ) -> Optional[str]:
        """Return nudge feedback if this patch ignores the diagnosis."""
        if not self.evidence_alignment or not self.flagged_routers:
            return None
        flagged_names = {router for router, _ in self.flagged_routers}
        if (
            router_name in flagged_names
            or router_name in self.evidence_nudged_routers
        ):
            return None
        if not context_prefill and flagged_names & inspected:
            return None
        self.evidence_nudged_routers.add(router_name)
        evidence = ", ".join(
            f"{router} ({check})" for router, check in self.flagged_routers
        )
        return (
            f"Reliability check paused this patch: '{router_name}' was not "
            f"flagged by the deterministic diagnosis, which points to: "
            f"{evidence}. Inspect the flagged router(s) first. If you still "
            "believe this router is the cause, explain why and resubmit the "
            "same patch; it will be allowed."
        )

    def initialise_checkpoint_metrics(self, *, not_fixed: int) -> None:
        """Seed metrics for the known faulty input without marking it verified."""
        self.checkpoint_fixed = 0
        self.checkpoint_not_fixed = max(0, int(not_fixed))
        self.checkpoint_side_effects = 0
        self.checkpoint_score = 0.0

    @staticmethod
    def _patch_fingerprint(params: Mapping[str, Any]) -> str:
        return "\x1f".join(
            str(params.get(field, ""))
            for field in ("router_name", "search", "replace")
        )

    @staticmethod
    def _normalise_patch_text(text: Any) -> str:
        return "\n".join(
            line.rstrip() for line in str(text or "").split("\n")
        ).strip()

    def _record(
        self,
        tool: str,
        decision: str,
        reason: str,
    ) -> None:
        self.decision_log.append({
            "tool": tool,
            "decision": decision,
            "reason": reason,
            "timestamp": datetime.now().isoformat(),
        })

    def before_tool(
        self,
        tool_name: str,
        params: Mapping[str, Any],
        *,
        inspected_routers: Iterable[str],
        pending_patches: Iterable[Mapping[str, Any]],
        context_prefill: bool = False,
    ) -> ReliabilityDecision:
        """Check a risky tool call before the environment executes it."""
        if not self.enabled or tool_name not in {"apply_patch", "submit"}:
            return ReliabilityDecision(True, "execute", "not_guarded")

        if tool_name == "apply_patch":
            router_name = str(params.get("router_name", ""))
            inspected = set(inspected_routers)

            if (
                self.require_inspection
                and not context_prefill
                and router_name not in inspected
            ):
                reason = "router_not_inspected"
                self._record(tool_name, "reject", reason)
                return ReliabilityDecision(
                    False,
                    "reject",
                    reason,
                    (
                        f"Reliability check rejected this patch: '{router_name}' "
                        "must be inspected before modification. Call "
                        "inspect_config for this router, then reconsider the patch."
                    ),
                )

            search = self._normalise_patch_text(params.get("search", ""))
            replace = self._normalise_patch_text(params.get("replace", ""))
            if search and search == replace:
                reason = "no_op_patch"
                self._record(tool_name, "reject", reason)
                return ReliabilityDecision(
                    False,
                    "reject",
                    reason,
                    "Reliability check rejected this patch: it makes no change.",
                )

            nudge = self._evidence_nudge(router_name, inspected, context_prefill)
            if nudge:
                reason = "unflagged_router"
                self._record(tool_name, "evidence_nudge", reason)
                return ReliabilityDecision(False, "evidence_nudge", reason, nudge)

            fingerprint = self._patch_fingerprint(params)
            if (
                self.block_repeated_failed_patch
                and fingerprint in self.failed_patch_fingerprints
            ):
                reason = "repeated_failed_patch"
                self._record(tool_name, "reject", reason)
                return ReliabilityDecision(
                    False,
                    "reject",
                    reason,
                    (
                        "Reliability check rejected this patch because the same "
                        "change previously introduced regressions. Revise the patch."
                    ),
                )

            self._record(tool_name, "execute", "patch_preconditions_passed")
            return ReliabilityDecision(
                True, "execute", "patch_preconditions_passed"
            )

        pending = list(pending_patches)
        if self.require_verified_submit and (
            pending or not self.current_state_verified
        ):
            reason = (
                "unverified_changes" if pending else "no_verified_current_state"
            )
            self._record(tool_name, "require_verification", reason)
            return ReliabilityDecision(
                False,
                "require_verification",
                reason,
                (
                    "Reliability check blocked submission: the current network "
                    "state has not been verified. Call verify before submitting."
                ),
            )

        self._record(tool_name, "execute", "verified_state")
        return ReliabilityDecision(True, "execute", "verified_state")

    def mark_patch_applied(self) -> None:
        """Mark the working state dirty after a patch succeeds."""
        if self.enabled:
            self.current_state_verified = False

    def evaluate_verification(
        self,
        verification_entry: Mapping[str, Any],
        pending_patches: Iterable[Mapping[str, Any]],
    ) -> ReliabilityDecision:
        """Classify a completed verification and choose any enforcement action.

        In strict mode (``net_benefit_ratio is None``), any regression
        triggers a rollback — the v2 behaviour.

        In net-benefit mode, the controller compares the *change* in fixed
        and regressed specs since the last checkpoint.  A verification is
        accepted when::

            fixed_delta >= net_benefit_ratio * regression_delta

        where ``fixed_delta = fixed - checkpoint_fixed`` and
        ``regression_delta = side_effects - checkpoint_side_effects``.
        A ratio of 1.0 means "accept whenever we fix at least as many as
        we break".  2.0 means "fix twice as many as we break".
        """
        if not self.enabled:
            return ReliabilityDecision(True, "observe", "controller_disabled")

        fixed = int(verification_entry.get("fixed", 0) or 0)
        not_fixed = int(verification_entry.get("not_fixed", 0) or 0)
        side_effects = int(verification_entry.get("side_effects", 0) or 0)

        # Compute deltas relative to the last committed checkpoint.
        fixed_delta = fixed - self.checkpoint_fixed
        regression_delta = side_effects - self.checkpoint_side_effects

        if not self.auto_rollback:
            # Rollback disabled — observe only.
            self.current_state_verified = False
            self._record("verify", "observe", "regressions_not_enforced")
            return ReliabilityDecision(
                True, "observe", "regressions_not_enforced"
            )

        accepted, acceptance_reason = self.assess_candidate(
            fixed=fixed,
            not_fixed=not_fixed,
            side_effects=side_effects,
        )
        if accepted:
            decision = (
                "accept" if side_effects == 0 else "accept_net_benefit"
            )
            self._accept_checkpoint(fixed, not_fixed, side_effects)
            self._record("verify", decision, acceptance_reason)
            feedback = ""
            if decision == "accept_net_benefit":
                feedback = (
                    f"Verification produced {fixed_delta:+d} additional "
                    f"fix(es) and {regression_delta:+d} additional "
                    "regression(s) while preserving or improving the repair "
                    f"score. Net benefit accepted (ratio "
                    f"{self.net_benefit_ratio})."
                )
            return ReliabilityDecision(
                True,
                decision,
                acceptance_reason,
                feedback,
            )

        # Regression exceeds tolerance — roll back.
        reason = "verification_regression"
        decision = (
            "selective_rollback"
            if self.selective_rollback and list(pending_patches)
            else "auto_rollback"
        )
        self._record("verify", decision, reason)
        return ReliabilityDecision(
            False,
            decision,
            reason,
            (
                "Reliability controller rejected the unverified transaction "
                f"because verification found {side_effects} regression(s) "
                f"(delta +{regression_delta} from checkpoint)."
            ),
        )

    @staticmethod
    def _repair_score(
        fixed: int,
        not_fixed: int,
        side_effects: int,
    ) -> float:
        denominator = fixed + not_fixed + side_effects
        return fixed / denominator if denominator > 0 else 0.0

    def assess_candidate(
        self,
        *,
        fixed: int,
        not_fixed: int,
        side_effects: int,
        baseline_fixed: Optional[int] = None,
        baseline_not_fixed: Optional[int] = None,
        baseline_side_effects: Optional[int] = None,
    ) -> tuple[bool, str]:
        """Return whether a verified candidate improves the trusted state."""
        base_fixed = (
            self.checkpoint_fixed
            if baseline_fixed is None
            else baseline_fixed
        )
        base_not_fixed = (
            self.checkpoint_not_fixed
            if baseline_not_fixed is None
            else baseline_not_fixed
        )
        base_side_effects = (
            self.checkpoint_side_effects
            if baseline_side_effects is None
            else baseline_side_effects
        )
        base_score = self._repair_score(
            base_fixed, base_not_fixed, base_side_effects
        )
        candidate_score = self._repair_score(
            fixed, not_fixed, side_effects
        )
        if candidate_score + 1e-12 < base_score:
            return False, "repair_score_decreased"

        fixed_delta = fixed - base_fixed
        regression_delta = side_effects - base_side_effects

        if side_effects == 0:
            return True, "zero_regressions_score_preserved"
        if self.net_benefit_ratio is None:
            return False, "strict_regression_rejection"
        if regression_delta <= 0:
            return True, "score_preserved_without_new_regressions"
        if fixed_delta >= self.net_benefit_ratio * regression_delta:
            return True, (
                "net_benefit_accepted:"
                f"+{fixed_delta}fixed/-{regression_delta}regressed"
            )
        return False, "net_benefit_ratio_not_met"

    def _accept_checkpoint(
        self,
        fixed: int,
        not_fixed: int,
        side_effects: int,
    ) -> None:
        """Update internal checkpoint tracking after accepting a state."""
        self.current_state_verified = True
        self.checkpoint_verified = True
        self.checkpoint_fixed = fixed
        self.checkpoint_not_fixed = not_fixed
        self.checkpoint_side_effects = side_effects
        self.checkpoint_score = self._repair_score(
            fixed, not_fixed, side_effects
        )

    def mark_failed_patches(
        self,
        patches: Iterable[Mapping[str, Any]],
    ) -> None:
        """Remember patches rejected by verification and restore state status."""
        if not self.enabled:
            return
        for patch in patches:
            params = {
                "router_name": patch.get("router", ""),
                "search": patch.get("search", ""),
                "replace": patch.get("replace", ""),
            }
            self.failed_patch_fingerprints.add(
                self._patch_fingerprint(params)
            )
        self.current_state_verified = self.checkpoint_verified
        # Scores revert to the checkpoint's values after a rollback.
        # (checkpoint_fixed / checkpoint_side_effects are already correct
        #  because _accept_checkpoint only updates them on success.)

    def mark_selective_recovery(
        self,
        *,
        retained: int,
        rejected: int,
        verified: bool,
        fixed: int = 0,
        not_fixed: int = 0,
        side_effects: int = 0,
    ) -> None:
        """Record completion of a selective rollback transaction."""
        if not self.enabled:
            return
        self.current_state_verified = verified
        if verified:
            self.checkpoint_verified = True
            self.checkpoint_fixed = fixed
            self.checkpoint_not_fixed = not_fixed
            self.checkpoint_side_effects = side_effects
            self.checkpoint_score = self._repair_score(
                fixed, not_fixed, side_effects
            )
        self._record(
            "verify",
            "selective_commit",
            f"retained_{retained}_rejected_{rejected}",
        )

    def record_final_verification(self, decision: str, reason: str) -> None:
        """Add an end-of-run enforcement event to the audit trail."""
        if self.enabled:
            self._record("finalize", decision, reason)

    def mark_rollback(self) -> None:
        """Synchronise controller state after an explicit rollback."""
        if self.enabled:
            self.current_state_verified = self.checkpoint_verified

    def get_summary(self) -> Dict[str, Any]:
        """Return aggregate enforcement metrics and the audit log."""
        return {
            "enabled": self.enabled,
            "net_benefit_ratio": self.net_benefit_ratio,
            "checkpoint_score": self.checkpoint_score,
            "evidence_alignment": self.evidence_alignment,
            "evidence_nudges": sum(
                1
                for item in self.decision_log
                if item["decision"] == "evidence_nudge"
            ),
            "actions_checked": len(self.decision_log),
            "actions_rejected": sum(
                1
                for item in self.decision_log
                if item["decision"] in {"reject", "require_verification"}
            ),
            "submissions_blocked": sum(
                1
                for item in self.decision_log
                if item["tool"] == "submit"
                and item["decision"] == "require_verification"
            ),
            "net_benefit_accepted": sum(
                1
                for item in self.decision_log
                if item["decision"] == "accept_net_benefit"
            ),
            "automatic_rollbacks": sum(
                1
                for item in self.decision_log
                if item["decision"] in {"auto_rollback", "selective_rollback"}
            ),
            "selective_rollbacks": sum(
                1
                for item in self.decision_log
                if item["decision"] == "selective_commit"
            ),
            "forced_final_verifications": sum(
                1
                for item in self.decision_log
                if item["tool"] == "finalize"
                and item["decision"] == "forced_verification"
            ),
            "decision_log": list(self.decision_log),
        }
