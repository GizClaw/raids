"""Offline checks for dual-Seed Giztest generation; no Runtime or credentials."""
import tempfile
import unittest
from pathlib import Path

import yaml

import function_chat
import generate


class FunctionChatTests(unittest.TestCase):
    def test_device_generator_keeps_both_profiles_and_workflow_policy(self):
        for workflow in ("general-assistant", "function-assistant"):
            with tempfile.TemporaryDirectory(prefix="function-giztest-") as directory:
                count = generate.generate(directory, repeat=1, case_filter="screen-exact,peer-isolation", workflow_name=workflow)
                self.assertEqual(4, count)
                paths = list(Path(directory).glob("*.yaml"))
                self.assertEqual(4, len(paths))
                for path in paths:
                    doc = yaml.safe_load(path.read_text())
                    create = next(step for step in doc["steps"] if step["id"] == "create")
                    self.assertEqual(workflow, create["rpc"]["request"]["workflow_name"])
                    if workflow == "function-assistant":
                        names = create["rpc"]["request"]["toolkit"]["tool_names"]["value"]
                        self.assertEqual(9, len(names))
                        self.assertNotIn("web.search", names)

    def test_function_scope_uses_native_calls_not_acknowledgement_words(self):
        for workflow in ("general-assistant", "function-assistant"):
            with tempfile.TemporaryDirectory(prefix="function-scope-") as directory:
                self.assertEqual(2, generate.generate(directory, repeat=1, case_filter="workspace-narrowing", workflow_name=workflow))
                for path in Path(directory).glob("*.yaml"):
                    doc = yaml.safe_load(path.read_text())
                    steps = {step["id"]: step for step in doc["steps"]}
                    create = steps["create"]["rpc"]["request"]
                    self.assertEqual(["music.stop"], create["toolkit"]["tool_names"]["value"])
                    self.assertEqual({"count": 1}, steps["catalog"]["expect"]["/items"])
                    self.assertEqual({"equals": "music.stop"}, steps["catalog"]["expect"]["/items/0/name"])
                    for group in ("mhs", "audioplayer_play", "audioplayer_stop", "run_workspace_set"):
                        probe = steps[group + "_0"]
                        self.assertEqual(0, probe["client_rpc"]["expect_calls"])
                        self.assertEqual({"equals": 0}, probe["expect"]["/calls"])
                    if workflow == "function-assistant":
                        self.assertNotIn("pattern", steps["turn_0"]["expect"].get("/text", {}))
                        self.assertEqual({"equals": 1}, steps["turn_0"]["expect"]["/response_count"])
                        snapshots = [s for s in doc["finally"] if s["id"].startswith("final_actual")]
                        self.assertEqual(4, len(snapshots))
                        self.assertTrue(all(s["client_rpc"]["observe_only"] for s in snapshots))
                    else:
                        self.assertIn("pattern", steps["turn_0"]["expect"]["/text"])
                        self.assertFalse(any(s["id"].startswith("final_actual") for s in doc["finally"]))

    def test_dedicated_suite_asserts_one_history_reply_per_turn(self):
        for profile in ("default", "testing"):
            doc = function_chat.function_document(profile)
            turns = [step for step in doc["steps"] if "peer_stream" in step]
            history = [step for step in doc["steps"] if step["id"].startswith("single_history_reply_")]
            self.assertEqual(12, len(turns))
            self.assertEqual(len(turns), len(history))
            for index, (turn, query) in enumerate(zip(turns, history)):
                self.assertTrue(turn["peer_stream"]["wait_for_history"])
                self.assertEqual({"selected_reply_" + str(index): "/reply"}, turn["capture"])
                self.assertEqual({"equals": 1}, turn["expect"]["/response_count"])
                self.assertIn("NO_DEVICE_ACTION", turn["expect"]["/text"]["not_contains"])
                self.assertEqual({"count": 2 * (index + 1)}, query["expect"]["/items"])
                self.assertEqual({"equals": "${selected_reply_" + str(index) + "}"}, query["expect"][f"/items/{2 * index + 1}/text"])


if __name__ == "__main__":
    unittest.main()
