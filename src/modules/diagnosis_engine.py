"""Deterministic, evidence-based fault localization for router configurations.

The engine parses Cisco-IOS configurations into a structured model and runs
cross-device consistency checks (BGP peering, link addressing, interface state,
OSPF adjacency and prefix origination). Findings are ranked per router and
returned as hypotheses with evidence and a suggested repair direction.

It uses only information the repair agent is allowed to see: the faulty
configurations, the topology and (optionally) the violated specifications.
It never reads ground-truth configurations or fault annotations.
"""

from __future__ import annotations

import ipaddress
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional, Tuple

from src.utils.context_utils.dependency_retrieval import (
    _router_index,
    rank_dependency_routers,
)

# Severity weights used to rank routers. Higher means more likely root cause.
CHECK_WEIGHTS = {
    "bgp_local_asn_mismatch": 10.0,
    "duplicate_address": 9.0,
    "bgp_remote_as_mismatch": 8.0,
    "bgp_neighbor_unknown_ip": 7.0,
    "link_subnet_mismatch": 7.0,
    "interface_shutdown": 7.0,
    "ospf_link_not_enabled": 6.0,
    "bgp_prefix_not_advertised": 6.0,
    "bgp_session_not_reciprocated": 3.0,
    "bgp_neighbor_shutdown": 8.0,
}

_TOP_LEVEL_HEADERS = (
    "interface ", "router ", "ip ", "hostname", "route-map", "access-list",
    "line ", "end", "control-plane", "banner", "service ", "boot", "snmp",
)


# --------------------------------------------------------------------------- #
#                              Configuration model                            #
# --------------------------------------------------------------------------- #
@dataclass
class Interface:
    name: str
    address: Optional[ipaddress.IPv4Interface] = None
    shutdown: bool = False
    ospf_enabled: bool = False


@dataclass
class BgpNeighbor:
    ip: str
    remote_as: Optional[int] = None
    peer_group: Optional[str] = None
    line: str = ""


@dataclass
class RouterModel:
    name: str
    interfaces: Dict[str, Interface] = field(default_factory=dict)
    bgp_asn: Optional[int] = None
    bgp_line: str = ""
    peer_groups: Dict[str, Optional[int]] = field(default_factory=dict)
    neighbors: Dict[str, BgpNeighbor] = field(default_factory=dict)
    bgp_networks: List[ipaddress.IPv4Network] = field(default_factory=list)
    ospf_networks: List[ipaddress.IPv4Network] = field(default_factory=list)
    has_ospf: bool = False
    static_local_prefixes: List[Tuple[ipaddress.IPv4Network, str]] = field(
        default_factory=list
    )
    # 'neighbor X shutdown' lines, keyed by neighbor IP or peer-group name.
    neighbor_shutdown: Dict[str, str] = field(default_factory=dict)

    def effective_remote_as(self, neighbor: BgpNeighbor) -> Optional[int]:
        if neighbor.remote_as is not None:
            return neighbor.remote_as
        if neighbor.peer_group:
            return self.peer_groups.get(neighbor.peer_group)
        return None

    def ospf_covers(self, interface: Interface) -> bool:
        if interface.ospf_enabled:
            return True
        if interface.address is None:
            return False
        return any(interface.address.ip in net for net in self.ospf_networks)


def _is_ip(value: str) -> bool:
    try:
        ipaddress.IPv4Address(value)
    except ValueError:
        return False
    return True


def _blocks(config: str) -> Iterable[Tuple[str, List[str]]]:
    """Yield (header, body_lines) for each top-level configuration block.

    Bodies end at a bare ``!`` or the next recognised top-level header, so
    unindented continuation lines (present in some generated configs) stay
    inside their block.
    """
    header: Optional[str] = None
    body: List[str] = []
    for raw in config.splitlines():
        line = raw.rstrip()
        if not line.strip():
            continue
        top_level = not raw[:1].isspace()
        if top_level and line == "!":
            if header is not None:
                yield header, body
            header, body = None, []
            continue
        if top_level and line.startswith(_TOP_LEVEL_HEADERS):
            if header is not None:
                yield header, body
            header, body = line, []
            continue
        if header is not None:
            body.append(line.strip())
    if header is not None:
        yield header, body


def parse_router_config(name: str, config: str) -> RouterModel:
    """Parse the subset of Cisco IOS needed by the consistency checks."""
    model = RouterModel(name=name)
    for header, body in _blocks(config):
        tokens = header.split()
        if tokens[0] == "interface" and len(tokens) > 1:
            interface = Interface(name=tokens[1])
            for line in body:
                parts = line.split()
                if parts[:2] == ["ip", "address"] and len(parts) >= 4:
                    try:
                        interface.address = ipaddress.IPv4Interface(
                            f"{parts[2]}/{parts[3]}"
                        )
                    except ValueError:
                        pass
                elif parts == ["shutdown"]:
                    interface.shutdown = True
                elif parts[:2] == ["ip", "ospf"] and "area" in parts:
                    interface.ospf_enabled = True
            model.interfaces[interface.name] = interface
        elif tokens[:2] == ["router", "ospf"]:
            model.has_ospf = True
            for line in body:
                parts = line.split()
                if parts[0] == "network" and len(parts) >= 3:
                    try:
                        wildcard = ipaddress.IPv4Address(parts[2])
                        mask = ipaddress.IPv4Address(int(wildcard) ^ 0xFFFFFFFF)
                        model.ospf_networks.append(
                            ipaddress.IPv4Network(f"{parts[1]}/{mask}", strict=False)
                        )
                    except ValueError:
                        pass
        elif tokens[:2] == ["router", "bgp"] and len(tokens) > 2:
            model.bgp_asn = int(tokens[2]) if tokens[2].isdigit() else None
            model.bgp_line = header
            for line in body:
                _parse_bgp_line(model, line)
        elif tokens[:2] == ["ip", "route"] and len(tokens) >= 5:
            if tokens[4].lower().startswith("loopback"):
                try:
                    model.static_local_prefixes.append((
                        ipaddress.IPv4Network(f"{tokens[2]}/{tokens[3]}"),
                        header,
                    ))
                except ValueError:
                    pass
    return model


def _parse_bgp_line(model: RouterModel, line: str) -> None:
    parts = line.split()
    if parts[0] == "network" and len(parts) >= 4 and parts[2] == "mask":
        try:
            model.bgp_networks.append(
                ipaddress.IPv4Network(f"{parts[1]}/{parts[3]}")
            )
        except ValueError:
            pass
        return
    if parts[0] != "neighbor" or len(parts) < 3:
        return
    target, keyword = parts[1], parts[2]
    if keyword == "shutdown":
        model.neighbor_shutdown[target] = line
        return
    if not _is_ip(target):
        if keyword == "peer-group" and len(parts) == 3:
            model.peer_groups.setdefault(target, None)
        elif keyword == "remote-as" and len(parts) > 3 and parts[3].isdigit():
            model.peer_groups[target] = int(parts[3])
        return
    neighbor = model.neighbors.setdefault(target, BgpNeighbor(ip=target))
    if keyword == "remote-as" and len(parts) > 3 and parts[3].isdigit():
        neighbor.remote_as = int(parts[3])
        neighbor.line = line
    elif keyword == "peer-group" and len(parts) > 3:
        neighbor.peer_group = parts[3]
        neighbor.line = neighbor.line or line


# --------------------------------------------------------------------------- #
#                                   Findings                                  #
# --------------------------------------------------------------------------- #
@dataclass
class Finding:
    router: str
    check: str
    evidence: str
    suggested_fix: str

    @property
    def weight(self) -> float:
        return CHECK_WEIGHTS.get(self.check, 1.0)


@dataclass
class Hypothesis:
    router: str
    score: float
    findings: List[Finding]

    @property
    def primary_check(self) -> str:
        return max(self.findings, key=lambda f: f.weight).check


@dataclass
class DiagnosisReport:
    hypotheses: List[Hypothesis]
    checked_routers: int

    def ranked_routers(self) -> List[str]:
        return [h.router for h in self.hypotheses]

    def to_prompt(self, top_k: int = 3, max_evidence: int = 3) -> str:
        """Render a compact, LLM-readable diagnosis summary."""
        if not self.hypotheses:
            return (
                "Deterministic diagnosis: no cross-device configuration "
                f"inconsistencies found across {self.checked_routers} routers. "
                "The fault may be in policy (ACLs, route-maps) or require "
                "verification feedback to localize."
            )
        lines = [
            "Deterministic diagnosis (consistency checks across "
            f"{self.checked_routers} routers). Ranked root-cause hypotheses:"
        ]
        for rank, hypothesis in enumerate(self.hypotheses[:top_k], start=1):
            lines.append(
                f"{rank}. {hypothesis.router} — {hypothesis.primary_check} "
                f"(score {hypothesis.score:.1f})"
            )
            seen = set()
            shown = 0
            for finding in sorted(hypothesis.findings, key=lambda f: -f.weight):
                key = (finding.check, finding.suggested_fix)
                if key in seen:
                    continue
                seen.add(key)
                lines.append(f"   evidence: {finding.evidence}")
                lines.append(f"   suggested fix: {finding.suggested_fix}")
                shown += 1
                if shown >= max_evidence:
                    break
        lines.append(
            "Treat these as hypotheses: inspect the router, apply the smallest "
            "fix, then verify."
        )
        return "\n".join(lines)


class DiagnosisEngine:
    """Run consistency checks and rank routers as root-cause candidates."""

    def __init__(
        self,
        configs: Dict[str, str],
        topology: Any = None,
        violated_specs: Any = None,
    ):
        self.configs = configs
        self.topology = topology
        self.violated_specs = violated_specs
        self.models = {
            name: parse_router_config(name, text)
            for name, text in configs.items()
        }
        self.ip_owner: Dict[str, Tuple[str, str]] = {}
        self.ip_owners_all: Dict[str, List[Tuple[str, str]]] = defaultdict(list)
        for name, model in self.models.items():
            for interface in model.interfaces.values():
                if interface.address is not None:
                    ip = str(interface.address.ip)
                    self.ip_owner.setdefault(ip, (name, interface.name))
                    self.ip_owners_all[ip].append((name, interface.name))
        self.findings: List[Finding] = []

    # ------------------------------------------------------------------ #
    def run(self) -> DiagnosisReport:
        self.findings = []
        self._check_duplicate_addresses()
        self._check_bgp_peering()
        self._check_neighbor_shutdown()
        if self.topology is not None:
            self._check_links()
        self._check_prefix_origination()
        return self._rank()

    # ------------------------------------------------------------------ #
    def _check_duplicate_addresses(self) -> None:
        for ip, owners in self.ip_owners_all.items():
            routers = sorted({router for router, _ in owners})
            if len(routers) < 2:
                continue
            listing = ", ".join(f"{r} {i}" for r, i in owners)
            for router in routers:
                self.findings.append(Finding(
                    router,
                    "duplicate_address",
                    f"{ip} is configured on multiple routers ({listing})",
                    f"give {router} its own unique address "
                    "(and matching router-id / OSPF network) if it is the "
                    "router that should not own " + ip,
                ))

    def _check_bgp_peering(self) -> None:
        # Votes: what every peer believes router X's ASN to be.
        votes: Dict[str, Counter] = defaultdict(Counter)
        statements: List[Tuple[str, BgpNeighbor, str, Optional[int]]] = []
        for name, model in self.models.items():
            if model.bgp_asn is None:
                continue
            for neighbor in model.neighbors.values():
                owner = self.ip_owner.get(neighbor.ip)
                if owner is None:
                    self.findings.append(Finding(
                        name,
                        "bgp_neighbor_unknown_ip",
                        f"{name}: 'neighbor {neighbor.ip}' matches no interface "
                        "address in the network",
                        f"correct the neighbor address on {name}",
                    ))
                    continue
                expected = model.effective_remote_as(neighbor)
                if expected is not None:
                    votes[owner[0]][expected] += 1
                statements.append((name, neighbor, owner[0], expected))

                peer = self.models[owner[0]]
                own_ips = {
                    str(i.address.ip) for i in model.interfaces.values()
                    if i.address is not None
                }
                if peer.bgp_asn is not None and not own_ips & set(peer.neighbors):
                    self.findings.append(Finding(
                        name,
                        "bgp_session_not_reciprocated",
                        f"{name} peers with {owner[0]} ({neighbor.ip}) but "
                        f"{owner[0]} has no neighbor statement back",
                        f"add the matching neighbor on {owner[0]} or remove it on {name}",
                    ))

        # Routers whose own local ASN is the likely fault (>= 2 peers agree).
        local_asn_suspects = set()
        for router, counter in votes.items():
            asn, count = counter.most_common(1)[0]
            local = self.models[router].bgp_asn
            if local is not None and asn != local and count >= 2:
                local_asn_suspects.add(router)
                self.findings.append(Finding(
                    router,
                    "bgp_local_asn_mismatch",
                    f"{router}: '{self.models[router].bgp_line}' but "
                    f"{count}/{sum(counter.values())} peers expect AS {asn}",
                    f"change the local ASN on {router} to {asn} "
                    "(and any peer-group remote-as that assumed the old ASN)",
                ))

        for name, neighbor, owner, expected in statements:
            local = self.models[owner].bgp_asn
            if expected is None or local is None or expected == local:
                continue
            if owner in local_asn_suspects:
                continue  # Explained by the owner's local-ASN finding.
            self.findings.append(Finding(
                name,
                "bgp_remote_as_mismatch",
                f"{name}: neighbor {neighbor.ip} ({owner}) configured with "
                f"remote-as {expected}, but {owner} runs AS {local}",
                f"set remote-as {local} for neighbor {neighbor.ip} on {name}",
            ))

    def _check_neighbor_shutdown(self) -> None:
        for name, model in self.models.items():
            if model.bgp_asn is None:
                continue
            for target, line in model.neighbor_shutdown.items():
                self.findings.append(Finding(
                    name,
                    "bgp_neighbor_shutdown",
                    f"{name}: '{line}' administratively disables the session",
                    f"remove 'neighbor {target} shutdown' on {name}",
                ))

    def _check_links(self) -> None:
        node_to_router, _ = _router_index(self.configs, self.topology)
        topology = self.topology if isinstance(self.topology, dict) else {}
        link_prefixlens: Counter = Counter()
        for link in topology.get("links", []) or []:
            for end in link.get("interfaces", []) or []:
                router = node_to_router.get(str(end.get("node")))
                interface = self.models.get(router, RouterModel("")).interfaces.get(
                    end.get("name")
                ) if router else None
                if interface is not None and interface.address is not None:
                    link_prefixlens[interface.address.network.prefixlen] += 1
        for link in topology.get("links", []) or []:
            ends = []
            for end in link.get("interfaces", []) or []:
                router = node_to_router.get(str(end.get("node")))
                if router is None or router not in self.models:
                    break
                interface = self.models[router].interfaces.get(end.get("name"))
                ends.append((router, end.get("name"), interface))
            if len(ends) != 2:
                continue
            (r1, n1, i1), (r2, n2, i2) = ends

            for router, iname, interface in ends:
                if interface is not None and interface.shutdown:
                    other = r2 if router == r1 else r1
                    self.findings.append(Finding(
                        router,
                        "interface_shutdown",
                        f"{router} {iname} (link to {other}) is shut down",
                        f"remove 'shutdown' from {iname} on {router}",
                    ))

            if i1 is None or i2 is None or i1.address is None or i2.address is None:
                continue
            if i1.address.network != i2.address.network:
                p1, p2 = i1.address.network.prefixlen, i2.address.network.prefixlen
                mask_only = p1 != p2 and (
                    i1.address.ip in i2.address.network
                    or i2.address.ip in i1.address.network
                )
                if mask_only:
                    # Blame the side whose mask deviates from the network's
                    # usual point-to-point mask.
                    ranked_lens = link_prefixlens.most_common(2)
                    if len(ranked_lens) > 1 and ranked_lens[0][1] == ranked_lens[1][1]:
                        suspects = ends  # No majority mask: cannot attribute.
                    else:
                        usual = ranked_lens[0][0]
                        suspects = [
                            e for e in ends
                            if e[2].address.network.prefixlen != usual
                        ] or ends
                else:
                    # Blame the side whose address no BGP peer references.
                    referenced = {
                        n.ip for m in self.models.values() for n in m.neighbors.values()
                    }
                    suspects = [
                        e for e in ends if str(e[2].address.ip) not in referenced
                    ] or ends
                for router, iname, interface in suspects:
                    peer = i2 if interface is i1 else i1
                    if mask_only:
                        fix = (
                            f"on {router} {iname}, change the mask to "
                            f"{peer.address.netmask} (/{peer.address.network.prefixlen}) "
                            "to match the other end of the link"
                        )
                    else:
                        fix = f"fix the address of {iname} on {router}"
                    self.findings.append(Finding(
                        router,
                        "link_subnet_mismatch",
                        f"link {r1} {n1} {i1.address} <-> {r2} {n2} {i2.address} "
                        "are in different subnets",
                        fix,
                    ))
                continue

            m1, m2 = self.models[r1], self.models[r2]
            if m1.has_ospf and m2.has_ospf:
                c1, c2 = m1.ospf_covers(i1), m2.ospf_covers(i2)
                if c1 != c2:
                    router, iname, interface = (r2, n2, i2) if c1 else (r1, n1, i1)
                    other = r1 if c1 else r2
                    self.findings.append(Finding(
                        router,
                        "ospf_link_not_enabled",
                        f"OSPF runs on {other}'s side of the {r1}<->{r2} link "
                        f"but not on {router} {iname} ({interface.address})",
                        f"enable OSPF on {iname} of {router}",
                    ))

    def _check_prefix_origination(self) -> None:
        for name, model in self.models.items():
            if model.bgp_asn is None or not model.bgp_networks:
                continue
            for prefix, line in model.static_local_prefixes:
                if prefix not in model.bgp_networks:
                    self.findings.append(Finding(
                        name,
                        "bgp_prefix_not_advertised",
                        f"{name} originates {prefix} locally ('{line}') but "
                        "has no BGP network statement for it",
                        f"add 'network {prefix.network_address} mask "
                        f"{prefix.netmask}' under router bgp on {name}",
                    ))

    # ------------------------------------------------------------------ #
    def _rank(self) -> DiagnosisReport:
        by_router: Dict[str, List[Finding]] = defaultdict(list)
        for finding in self.findings:
            by_router[finding.router].append(finding)

        relevance: Dict[str, float] = {}
        if self.violated_specs is not None and self.topology is not None:
            ranked = rank_dependency_routers(
                self.configs, self.topology, self.violated_specs, neighbor_hops=0
            )
            top = ranked[0][1] if ranked else 0.0
            relevance = {r: s / top for r, s in ranked} if top else {}

        hypotheses = []
        for router, findings in by_router.items():
            # Diminishing returns for repeated evidence of the same kind.
            per_check: Dict[str, int] = Counter(f.check for f in findings)
            score = sum(
                CHECK_WEIGHTS.get(check, 1.0) * (1 + 0.25 * (count - 1))
                for check, count in per_check.items()
            )
            # Specification relevance is a tiebreaker, not a primary signal.
            score += 2.0 * relevance.get(router, 0.0)
            hypotheses.append(Hypothesis(router, score, findings))
        hypotheses.sort(key=lambda h: (-h.score, h.router))
        return DiagnosisReport(hypotheses, checked_routers=len(self.models))


def diagnose(
    configs: Dict[str, str],
    topology: Any = None,
    violated_specs: Any = None,
) -> DiagnosisReport:
    """Convenience wrapper: build an engine and return its report."""
    return DiagnosisEngine(configs, topology, violated_specs).run()
