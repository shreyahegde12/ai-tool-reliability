import unittest

from src.modules.MiniAgent import ToolEnvironment
from src.modules.diagnosis_engine import diagnose, parse_router_config


def router(name, asn, loopback, links, peers=(), networks=(), statics=()):
    """Build a minimal Cisco-IOS config for tests."""
    lines = [
        f"hostname {name}",
        "interface Loopback0",
        f" ip address {loopback} 255.255.255.255",
        "!",
    ]
    for ifname, address, mask, extra in links:
        lines += [f"interface {ifname}", f" ip address {address} {mask}"]
        lines += [f" {item}" for item in extra]
        lines.append("!")
    for prefix, mask in statics:
        lines.append(f"ip route {prefix} {mask} Loopback100")
    lines += [f"router bgp {asn}"]
    for ip, remote_as in peers:
        lines.append(f" neighbor {ip} remote-as {remote_as}")
    lines.append(" address-family ipv4")
    for prefix, mask in networks:
        lines.append(f"  network {prefix} mask {mask}")
    lines += [" exit-address-family", "!"]
    return "\n".join(lines)


TOPOLOGY = {
    "nodes": [{"id": "a", "hostname": "a"}, {"id": "b", "hostname": "b"}],
    "links": [{
        "nodes": ["a", "b"],
        "interfaces": [
            {"node": "a", "name": "Gi0/0"},
            {"node": "b", "name": "Gi0/0"},
        ],
    }],
}
MASK31 = "255.255.255.254"


def network(a_asn=65001, b_remote=65001, a_mask=MASK31, a_extra=(),
            a_networks=(("10.200.0.0", "255.255.255.0"),)):
    return {
        "a.cfg": router(
            "a", a_asn, "10.180.0.1",
            [("Gi0/0", "10.181.0.0", a_mask, list(a_extra))],
            peers=[("10.181.0.1", 65002)],
            networks=a_networks,
            statics=[("10.200.0.0", "255.255.255.0")],
        ),
        "b.cfg": router(
            "b", 65002, "10.180.0.2",
            [("Gi0/0", "10.181.0.1", MASK31, [])],
            peers=[("10.181.0.0", b_remote)],
        ),
    }


class ParserTests(unittest.TestCase):
    def test_parses_bgp_and_interfaces(self):
        model = parse_router_config("a.cfg", network()["a.cfg"])
        self.assertEqual(model.bgp_asn, 65001)
        self.assertEqual(model.neighbors["10.181.0.1"].remote_as, 65002)
        self.assertEqual(str(model.interfaces["Gi0/0"].address), "10.181.0.0/31")
        self.assertEqual(len(model.bgp_networks), 1)

    def test_unindented_continuation_stays_in_block(self):
        config = "router ospf 1\n router-id 1.1.1.1\nnetwork 10.0.0.0 0.0.0.1 area 0\n!"
        model = parse_router_config("r.cfg", config)
        self.assertEqual(len(model.ospf_networks), 1)


class DiagnosisTests(unittest.TestCase):
    def top(self, configs):
        report = diagnose(configs, TOPOLOGY)
        self.assertTrue(report.hypotheses, "expected at least one hypothesis")
        return report.hypotheses[0]

    def test_clean_network_has_no_findings(self):
        self.assertEqual(diagnose(network(), TOPOLOGY).hypotheses, [])

    def test_remote_as_mismatch_blames_configuring_router(self):
        top = self.top(network(b_remote=65009))
        self.assertEqual(top.router, "b.cfg")
        self.assertEqual(top.primary_check, "bgp_remote_as_mismatch")

    def test_mask_mismatch_suggests_matching_mask(self):
        # A single link has no majority mask, so both ends are suspects.
        report = diagnose(network(a_mask="255.255.255.252"), TOPOLOGY)
        by_router = {h.router: h for h in report.hypotheses}
        self.assertEqual(set(by_router), {"a.cfg", "b.cfg"})
        self.assertEqual(by_router["a.cfg"].primary_check, "link_subnet_mismatch")
        self.assertIn(MASK31, by_router["a.cfg"].findings[0].suggested_fix)

    def test_mask_mismatch_blames_deviating_mask_with_majority(self):
        configs = network(a_mask="255.255.255.252")
        configs["c.cfg"] = router(
            "c", 65003, "10.180.0.3",
            [("Gi0/0", "10.181.0.4", MASK31, []), ("Gi0/1", "10.181.0.5", MASK31, [])],
        )
        topology = {
            "nodes": TOPOLOGY["nodes"] + [{"id": "c", "hostname": "c"}],
            "links": TOPOLOGY["links"] + [{
                "nodes": ["c", "c"],
                "interfaces": [
                    {"node": "c", "name": "Gi0/0"},
                    {"node": "c", "name": "Gi0/1"},
                ],
            }],
        }
        top = diagnose(configs, topology).hypotheses[0]
        self.assertEqual((top.router, top.primary_check), ("a.cfg", "link_subnet_mismatch"))

    def test_shutdown_link_interface(self):
        top = self.top(network(a_extra=["shutdown"]))
        self.assertEqual((top.router, top.primary_check), ("a.cfg", "interface_shutdown"))

    def test_locally_originated_prefix_not_advertised(self):
        configs = network(a_networks=(("10.201.0.0", "255.255.255.0"),))
        top = self.top(configs)
        self.assertEqual(top.primary_check, "bgp_prefix_not_advertised")

    def test_duplicate_address_flags_both_routers(self):
        configs = network()
        configs["b.cfg"] = configs["b.cfg"].replace("10.180.0.2", "10.180.0.1")
        routers = {
            h.router for h in diagnose(configs, TOPOLOGY).hypotheses
            if h.primary_check == "duplicate_address"
        }
        self.assertEqual(routers, {"a.cfg", "b.cfg"})

    def test_neighbor_shutdown(self):
        configs = network()
        configs["b.cfg"] = configs["b.cfg"].replace(
            " address-family ipv4", " neighbor 10.181.0.0 shutdown\n address-family ipv4", 1
        )
        top = self.top(configs)
        self.assertEqual((top.router, top.primary_check), ("b.cfg", "bgp_neighbor_shutdown"))

    def test_prompt_mentions_router_and_fix(self):
        text = diagnose(network(b_remote=65009), TOPOLOGY).to_prompt()
        self.assertIn("b.cfg", text)
        self.assertIn("suggested fix", text)


class DiagnoseToolTests(unittest.TestCase):
    def make_env(self, configs, enabled=True):
        return ToolEnvironment(
            faulty_configs=configs,
            original_configs={},
            full_faulty_configs=configs,
            topology=TOPOLOGY,
            violated_specs=[],
            specification_csv_path=None,
            original_specs=[],
            net_env=None,
            evaluator=lambda **kwargs: {},
            evaluator_kwargs={},
            diagnosis_config={"enabled": enabled},
        )

    def test_tool_disabled_by_default(self):
        env = self.make_env(network(b_remote=65009), enabled=False)
        self.assertIn("Unknown tool", env.execute_tool("diagnose", {}))

    def test_tool_reflects_agent_patches(self):
        env = self.make_env(network(b_remote=65009))
        self.assertIn("bgp_remote_as_mismatch", env.execute_tool("diagnose", {}))
        env.execute_tool("inspect_config", {"router_name": "b.cfg"})
        env.execute_tool("apply_patch", {
            "router_name": "b.cfg",
            "search": "remote-as 65009",
            "replace": "remote-as 65001",
        })
        self.assertIn("no cross-device", env.execute_tool("diagnose", {}))
        self.assertEqual(len(env.diagnosis_history), 2)

    def make_partial_env(self, expand):
        full = network(b_remote=65009)
        return ToolEnvironment(
            faulty_configs={"a.cfg": full["a.cfg"]},
            original_configs={},
            full_faulty_configs=full,
            topology=TOPOLOGY,
            violated_specs=[],
            specification_csv_path=None,
            original_specs=[],
            net_env=None,
            evaluator=lambda **kwargs: {},
            evaluator_kwargs={},
            diagnosis_config={"enabled": True, "expand_context": expand},
        )

    def test_expand_context_adds_unretrieved_diagnosed_router(self):
        env = self.make_partial_env(expand=True)
        report = env.execute_tool("diagnose", {})
        self.assertIn("Added to your workspace", report)
        self.assertEqual(env.diagnosis_added_routers, ["b.cfg"])
        self.assertIn("b.cfg", env.current_configs)
        self.assertIn("b.cfg", env.checkpoint_configs)

        env.execute_tool("inspect_config", {"router_name": "b.cfg"})
        result = env.execute_tool("apply_patch", {
            "router_name": "b.cfg",
            "search": "remote-as 65009",
            "replace": "remote-as 65001",
        })
        self.assertTrue(result.startswith("Patch applied"))
        self.assertEqual(env.patched_routers, {"b.cfg"})

        env.execute_tool("diagnose", {})
        self.assertEqual(env.diagnosis_added_routers, ["b.cfg"])

    def test_expand_context_off_keeps_retrieved_set(self):
        env = self.make_partial_env(expand=False)
        report = env.execute_tool("diagnose", {})
        self.assertNotIn("Added to your workspace", report)
        self.assertNotIn("b.cfg", env.current_configs)


if __name__ == "__main__":
    unittest.main()
