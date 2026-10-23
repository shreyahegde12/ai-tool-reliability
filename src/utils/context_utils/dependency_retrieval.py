"""Specification- and topology-guided router-level context retrieval."""

from __future__ import annotations

import csv
import ipaddress
import json
import logging
import re
from collections import deque
from pathlib import Path
from typing import Any

from src.utils.context_utils.sampling_methods import (
    _format_topology_text,
    _resolve_context_token_budget,
)
from src.utils.token_counter import token_counter

logger = logging.getLogger(__name__)

_SPEC_COLUMNS = (
    "predicate_type",
    "node",
    "prefix",
    "waypoint",
    "num_routes",
    "sources",
)
_IPV4_WITH_MASK = re.compile(
    r"(?<![\d.])((?:\d{1,3}\.){3}\d{1,3})\s+(\d{1,3}(?:\.\d{1,3}){3})(?![\d.])"
)
_CIDR = re.compile(r"(?<![\d.])(?:\d{1,3}\.){3}\d{1,3}/\d{1,2}(?!\d)")


def _rows_from_specs(preds: Any) -> list[dict[str, str]]:
    """Normalize Cornetto's CSV-row strings or mapping rows."""
    if preds is None:
        return []
    if isinstance(preds, str):
        values: list[Any] = preds.splitlines()
    elif isinstance(preds, (list, tuple)):
        values = list(preds)
    else:
        values = [preds]

    rows: list[dict[str, str]] = []
    for value in values:
        if isinstance(value, dict):
            row = {str(key): str(item or "") for key, item in value.items()}
        else:
            cells = next(csv.reader([str(value)]))
            if cells and cells[0].strip().lower() == _SPEC_COLUMNS[0]:
                continue
            row = {
                column: cells[index].strip() if index < len(cells) else ""
                for index, column in enumerate(_SPEC_COLUMNS)
            }
        if "broken" in row.get("sources", "").lower() and row.get("prefix"):
            rows.append(row)
    return rows


def _network_for_prefix(value: str) -> ipaddress.IPv4Network | None:
    try:
        network = ipaddress.ip_network(value.strip(), strict=False)
    except ValueError:
        return None
    return network if isinstance(network, ipaddress.IPv4Network) else None


def _config_mentions_prefix(config: str, prefix: ipaddress.IPv4Network) -> bool:
    """Match a prefix directly or an interface/network statement inside it."""
    if str(prefix) in config:
        return True

    for value in _CIDR.findall(config):
        network = _network_for_prefix(value)
        if network == prefix:
            return True

    for address, mask in _IPV4_WITH_MASK.findall(config):
        try:
            network = ipaddress.ip_network(f"{address}/{mask}", strict=False)
        except ValueError:
            continue
        if network == prefix:
            return True
    return False


def _router_index(
    final_configs: dict[str, str], topology: Any
) -> tuple[dict[str, str], dict[str, set[str]]]:
    """Map topology identifiers/hostnames to config keys and build adjacency."""
    if isinstance(topology, str):
        try:
            topology = json.loads(topology)
        except json.JSONDecodeError:
            return {}, {}
    if not isinstance(topology, dict):
        return {}, {}

    config_by_name: dict[str, str] = {}
    for config_name in final_configs:
        config_by_name[config_name.lower()] = config_name
        config_by_name[Path(config_name).stem.lower()] = config_name

    def config_for(name: Any) -> str | None:
        return config_by_name.get(str(name).lower())

    node_to_router: dict[str, str] = {}
    topology_nodes = topology.get("nodes", [])
    if isinstance(topology_nodes, dict):
        topology_nodes = [
            dict(value, id=key) if isinstance(value, dict)
            else {"id": key, "hostname": value}
            for key, value in topology_nodes.items()
        ]
    for node in topology_nodes:
        if not isinstance(node, dict):
            continue
        node_id = str(node.get("id", node.get("hostname", "")))
        router = config_for(node.get("hostname", node_id)) or config_for(node_id)
        if router:
            node_to_router[node_id] = router
            node_to_router[str(node.get("hostname", node_id))] = router

    adjacency: dict[str, set[str]] = {name: set() for name in final_configs}
    for link in topology.get("links", []) or []:
        if not isinstance(link, dict):
            continue
        endpoints = link.get("nodes") or []
        if len(endpoints) != 2:
            continue
        left = node_to_router.get(str(endpoints[0])) or config_for(endpoints[0])
        right = node_to_router.get(str(endpoints[1])) or config_for(endpoints[1])
        if left and right and left != right:
            adjacency.setdefault(left, set()).add(right)
            adjacency.setdefault(right, set()).add(left)
    return node_to_router, adjacency


def _shortest_path(
    adjacency: dict[str, set[str]], source: str, target: str
) -> list[str]:
    queue = deque([(source, [source])])
    seen = {source}
    while queue:
        router, path = queue.popleft()
        if router == target:
            return path
        for neighbor in sorted(adjacency.get(router, ())):
            if neighbor not in seen:
                seen.add(neighbor)
                queue.append((neighbor, [*path, neighbor]))
    return []


def rank_dependency_routers(
    final_configs: dict[str, str],
    topology: Any,
    preds: Any,
    neighbor_hops: int = 1,
) -> list[tuple[str, float]]:
    """Rank routers by their relationship to failed predicates and paths.

    Sources, routers configuring the failed destination prefix, and routers on
    their shortest topology paths are prioritized. Optional neighboring hops
    receive progressively lower scores. Scores are deterministic for a given
    input and are intended for retrieval ordering, not calibrated probabilities.
    """
    if neighbor_hops < 0:
        raise ValueError("neighbor_hops must be non-negative")

    node_to_router, adjacency = _router_index(final_configs, topology)
    aliases = {name.lower(): name for name in final_configs}
    aliases.update({Path(name).stem.lower(): name for name in final_configs})

    def resolve_router(label: str) -> str | None:
        return aliases.get(label.lower()) or node_to_router.get(label)

    scores: dict[str, float] = {}
    expansion_seeds: set[str] = set()
    for row in _rows_from_specs(preds):
        prefix = _network_for_prefix(row["prefix"])
        if prefix is None:
            logger.debug("Skipping unparsable specification prefix %r", row["prefix"])
            continue

        source = resolve_router(row.get("node", ""))
        if source:
            scores[source] = scores.get(source, 0.0) + 100.0
            expansion_seeds.add(source)

        owners = [
            name for name, config in final_configs.items()
            if _config_mentions_prefix(config, prefix)
        ]
        for owner in owners:
            scores[owner] = scores.get(owner, 0.0) + 50.0
            expansion_seeds.add(owner)
            if source:
                path = _shortest_path(adjacency, source, owner)
                for distance, router in enumerate(path):
                    scores[router] = scores.get(router, 0.0) + max(10.0, 30.0 - 5.0 * distance)
                    expansion_seeds.add(router)

        waypoint = resolve_router(row.get("waypoint", ""))
        if waypoint:
            scores[waypoint] = scores.get(waypoint, 0.0) + 35.0
            expansion_seeds.add(waypoint)

    frontier = set(expansion_seeds)
    visited = set(expansion_seeds)
    for hop in range(1, neighbor_hops + 1):
        next_frontier: set[str] = set()
        weight = 20.0 / hop
        for router in sorted(frontier):
            for neighbor in adjacency.get(router, ()):
                if neighbor not in visited:
                    visited.add(neighbor)
                    next_frontier.add(neighbor)
                    scores[neighbor] = scores.get(neighbor, 0.0) + weight
        frontier = next_frontier

    return sorted(scores.items(), key=lambda item: (-item[1], item[0]))


def spec_dependency_at_k(
    original_configs: dict[str, str],
    final_configs: dict[str, str],
    topology: Any,
    preds: Any,
    **kwargs: Any,
) -> tuple[dict[str, str], list[str], list[str]]:
    """Retrieve ranked router configurations within Cornetto's token budget."""
    del original_configs  # Do not use repair labels, which are absent publicly.
    model = kwargs.get("model_name")
    if kwargs.get("max_context_tokens", "full") == "full":
        config_budget, original_budget = _resolve_context_token_budget(model, kwargs)
        topology_budget = token_counter(_format_topology_text(topology))
        preds_text = "\n".join(preds) if isinstance(preds, list) else str(preds)
        preds_budget = token_counter(preds_text)
        network_budget = max(0, int((original_budget - topology_budget - preds_budget) * 0.9))
        max_tokens = min(config_budget, network_budget)
    else:
        max_tokens, _ = _resolve_context_token_budget(model, kwargs)

    neighbor_hops = int(kwargs.get("dependency_neighbor_hops", 1))
    ranked = rank_dependency_routers(final_configs, topology, preds, neighbor_hops)
    logger.info("Specification/topology retrieval ranking: %s", ranked)

    selected: dict[str, str] = {}
    included: list[str] = []
    excluded: list[str] = []
    token_total = 0
    for router, score in ranked:
        config = final_configs[router]
        count = token_counter(config, model)
        if token_total + count <= max_tokens:
            selected[router] = config
            included.append(router)
            token_total += count
        else:
            excluded.append(router)
            logger.debug("Excluded %s (score %.1f): context budget exceeded", router, score)

    excluded.extend(router for router in final_configs if router not in included and router not in excluded)
    logger.info(
        "Dependency retrieval selected %d/%d routers (%d tokens; budget %s)",
        len(included), len(final_configs), token_total, max_tokens,
    )
    return selected, included, excluded