"""Preserve device entry, audio completion and request-specific follow-ups."""
import importlib.util
from pathlib import Path
import unittest


spec = importlib.util.spec_from_file_location("device_flow", Path(__file__).with_name("device-flow.py"))
flow = importlib.util.module_from_spec(spec)
spec.loader.exec_module(flow)


def device_document(raid, suffix):
    impl = next(impl for variant, impl in flow.implementations(raid) if variant == suffix)
    return flow.document(raid, suffix, impl)


def replies(document):
    return {step["peer_stream"]["input"]: step for step in document["steps"] if "peer_stream" in step}


class DeviceFlowTest(unittest.TestCase):
    def test_prompt_led_followups_keep_audio_and_resume_without_forced_questions(self):
        for raid, suffix in (
            ("figure-li-bai", "eino.multi-role"),
            ("story-alice", "eino.multi-role"),
            ("adventure-treasure", "eino"),
        ):
            with self.subTest(raid=raid):
                document = device_document(raid, suffix)
                turns = replies(document)
                for text in ("我选第一个", "继续", "继续上次的内容"):
                    step = turns[text]
                    self.assertTrue(step["expect"]["/text"]["non_empty"])
                    self.assertNotIn("pattern", step["expect"]["/text"])
                    self.assertTrue(step["peer_stream"]["require_audio"])
                    self.assertTrue(step["expect"]["/text_eos"]["equals"])
                    self.assertTrue(step["expect"]["/audio_eos"]["equals"])
                steps = document["steps"]
                resume_index = steps.index(turns["继续上次的内容"])
                self.assertEqual(steps[resume_index - 1]["rpc"]["method"], "server.run.workspace.reload")

    def test_every_opening_and_restart_still_invites_a_choice(self):
        for raid, suffix in (
            ("figure-li-bai", "eino.multi-role"),
            ("story-alice", "eino.multi-role"),
            ("adventure-treasure", "eino"),
        ):
            with self.subTest(raid=raid):
                starts = [step for step in device_document(raid, suffix)["steps"]
                          if step.get("peer_stream", {}).get("input") == "开始"]
                self.assertEqual(len(starts), 2)
                for step in starts:
                    self.assertEqual(step["expect"]["/text"]["pattern"], flow.ENDS_WITH_QUESTION)

    def test_traditional_variants_keep_all_closing_questions(self):
        for raid, suffix in (("story-alice", "eino"), ("adventure-treasure", "eino.multi-role")):
            with self.subTest(raid=raid):
                for step in replies(device_document(raid, suffix)).values():
                    self.assertEqual(step["expect"]["/text"]["pattern"], flow.ENDS_WITH_QUESTION)


if __name__ == "__main__":
    unittest.main()
