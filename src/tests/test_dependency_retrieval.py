import json
import unittest
from unittest.mock import patch
from src.modules.MiniAgent import MiniAgent

from src.utils.context_utils.dependency_retrieval import (
    rank_dependency_routers,
    spec_dependency_at_k,
)
from src.utils.context_utils.sampling_registry import VALID_SAMPLING_REGISTRY


class DependencyRetrievalTests(unittest.TestCase):
    def setUp(self):
        self.configs = {
            "src.cfg": "hostname src\nrouter bgp 65001\n",
            "mid.cfg": "hostname mid\n",
            "dst.cfg": "hostname dst\ninterface Loopback0\n ip address 10.0.0.1 255.255.255.0\n",
            "isolated.cfg": "hostname isolated\n",
        }
        self.topology = {
            "nodes": [
                {"id": "0", "hostname": "src"},
                {"id": "1", "hostname": "mid"},
                {"id": "2", "hostname": "dst"},
                {"id": "3", "hostname": "isolated"},
            ],
            "links": [
                {"nodes": ["0", "1"]},
                {"nodes": ["1", "2"]},
            ],
        }
        self.broken_specs = [
            "reachability,src,10.0.0.0/24,,,broken_removed",
            "reachability,isolated,192.0.2.0/24,,,intact",
        ]

    def test_ranks_source_owner_and_path_ahead_of_unrelated_router(self):
        ranked = rank_dependency_routers(self.configs, self.topology, self.broken_specs, 0)
        order = [router for router, _ in ranked]

        self.assertEqual(set(order), {"src.cfg", "mid.cfg", "dst.cfg"})
        self.assertEqual(order[0], "src.cfg")
        self.assertNotIn("isolated.cfg", order)
        self.assertIn("dst.cfg", order)
        self.assertIn("mid.cfg", order)

    def test_sampling_registry_exposes_spec_dependency(self):
        self.assertIs(VALID_SAMPLING_REGISTRY["spec_dependency"], spec_dependency_at_k)

    def test_neighbor_hops_are_optional(self):
        topology = json.loads(json.dumps(self.topology))
        topology["links"].append({"nodes": ["0", "3"]})

        without_neighbors = rank_dependency_routers(
            self.configs, topology, self.broken_specs, neighbor_hops=0
        )
        with_neighbors = rank_dependency_routers(
            self.configs, topology, self.broken_specs, neighbor_hops=1
        )

        self.assertNotIn("isolated.cfg", dict(without_neighbors))
        self.assertIn("isolated.cfg", dict(with_neighbors))

    def test_retrieval_obeys_budget_and_reports_all_routers(self):
        with patch(
            "src.utils.context_utils.dependency_retrieval.token_counter",
            side_effect=lambda text, model=None: len(text),
        ):
            selected, included, excluded = spec_dependency_at_k(
                original_configs={},
                final_configs=self.configs,
                topology=self.topology,
                preds=self.broken_specs,
                max_context_tokens=50,
                dependency_neighbor_hops=0,
            )

        self.assertLessEqual(sum(len(text) for text in selected.values()), 30)
        self.assertIn("src.cfg", included)
        self.assertIn("isolated.cfg", excluded)
        self.assertEqual(set(included) | set(excluded), set(self.configs))

    def test_no_broken_spec_returns_no_ranked_routers(self):
        ranked = rank_dependency_routers(
            self.configs,
            self.topology,
            ["reachability,isolated,192.0.2.0/24,,,intact"],
        )

        self.assertEqual(ranked, [])

    def test_agent_context_counts_only_visible_routers(self):
        sample = {
            "faulty_configs": {
                "r1.cfg": "hostname r1",
                "r2.cfg": "hostname r2",
                "r3.cfg": "hostname r3",
            },
            "selected_configs": {
                "r2.cfg": "hostname r2",
            },
            "original_configs": {
                "r1.cfg": "hostname r1",
                "r2.cfg": "hostname r2",
                "r3.cfg": "hostname r3",
            },
        }

        agent = MiniAgent.__new__(MiniAgent)
        with patch("src.modules.MiniAgent.token_counter", return_value=2):
            summary = agent._summarize_agent_task_context(sample)

        self.assertEqual(summary["node_count"], 3)
        self.assertEqual(summary["node_count_retrieved"], 1)
        self.assertEqual(summary["lines_of_code_total"], 3)
        self.assertEqual(summary["lines_of_code_retrieved"], 1)
        self.assertEqual(summary["selected_routers"], ["r2.cfg"])
        self.assertEqual(summary["selected_config_tokens"], 2)


if __name__ == "__main__":
    unittest.main()
