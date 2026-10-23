"""Policy enforcement for risky MiniAgent tool calls.

The controller is intentionally independent of the LLM and Batfish.  It
checks state-changing actions before execution and consumes structured
verification results afterwards.  This keeps reliability decisions
deterministic, auditable, and easy to disable for baseline experiments.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Iterable, Mapping, Optional, Set


@dataclass(frozen=True)
class ReliabilityDecision:
    """Result of a reliability-policy check."""

    allowed: bool
    decision: str
    reason: str
    feedback: str = ""


def _config_value(config: Any, name: str, default: bool) -> bool:
    """Read a boolean from a dict-like or attribute-based config object."""
    if config is None:
        return default
    if isinstance(config, Mapping):
        return bool(config.get(name, default))
    return bool(getattr(config, name, default))


class ReliabilityController:
    """Deterministic guard for patching, verification, and submission."""

    def __init__(self, config: Optional[Any] = None):
        self.enabled = _config_value(config, "enabled", False)
        self.require_inspection = _config_value(
            config, "require_inspection_before_patch", True
        )
        self.require_verified_submit = _config_value(
            config, "require_verification_before_submit", True
        )
        self.auto_rollback = _config_value(
            config, "auto_rollback_on_regression", True
        )
        self.block_repeated_failed_patch = _config_value(
            config, "block_repeated_failed_patch", True
        )
        self.force_final_verification = _config_value(
            config, "force_final_verification", True
        )
        self.selective_rollback = _config_value(
            config, "selective_rollback", True
        )

        self.current_state_verified = False
        self.checkpoint_verified = False
        self.failed_patch_fingerprints: Set[str] = set()
        self.decision_log = []

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
        """Classify a completed verification and choose any enforcement action."""
        if not self.enabled:
            return ReliabilityDecision(True, "observe", "controller_disabled")

        side_effects = int(verification_entry.get("side_effects", 0) or 0)
        if side_effects > 0 and self.auto_rollback:
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
                    f"because verification found {side_effects} regression(s)."
                ),
            )

        if side_effects == 0:
            self.current_state_verified = True
            self.checkpoint_verified = True
            self._record("verify", "accept", "zero_regressions")
            return ReliabilityDecision(True, "accept", "zero_regressions")

        self.current_state_verified = False
        self._record("verify", "observe", "regressions_not_enforced")
        return ReliabilityDecision(True, "observe", "regressions_not_enforced")

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

    def mark_selective_recovery(
        self,
        *,
        retained: int,
        rejected: int,
        verified: bool,
    ) -> None:
        """Record completion of a selective rollback transaction."""
        if not self.enabled:
            return
        self.current_state_verified = verified
        if verified:
            self.checkpoint_verified = True
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
