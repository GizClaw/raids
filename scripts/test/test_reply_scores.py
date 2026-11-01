import copy
import unittest

import reply_scores as score


class ReplyScoresTest(unittest.TestCase):
    def setUp(self):
        self.batch = {"rubric_sha256": score.digest(score.RUBRIC), "contract": "仅旁白；按用户语种。",
                      "turns": [{"i": i} for i in range(24)],
                      "independent_evidence": [{"id": "source-a"}], "function_events": []}
        self.opinion = {"rows": [{"i": i, "s": [5] * 5, "why": "", "block": False,
                                   "evidence": []} for i in range(24)]}

    def test_weighted_score_and_threshold_boundary(self):
        for row in self.opinion["rows"]:
            row.update(s=[4] * 5, why="各项可用，存在局部不足。")
        rows = score.validate(self.opinion, self.batch)
        self.assertEqual(80, rows[0]["total"])
        result = score.summarize(rows, 24, "PASS")
        self.assertTrue(result["threshold_comparison"]["80"]["content_provisionally_accepted"])
        self.assertFalse(result["threshold_comparison"]["85"]["content_provisionally_accepted"])

    def test_good_mean_cannot_hide_three_bad_turns(self):
        for row in self.opinion["rows"][:3]:
            row.update(s=[3] * 5, why="同轮存在明显问题。", evidence=[f"r{row['i']}"])
        rows = score.validate(self.opinion, self.batch)
        result = score.summarize(rows, 24, "PASS")
        self.assertGreater(result["mean"], 90)
        self.assertFalse(result["threshold_comparison"]["80"]["content_provisionally_accepted"])

    def test_one_local_error_does_not_automatically_fail_script(self):
        self.opinion["rows"][7].update(s=[5, 5, 1, 4, 5], why="局部知识错误但可继续。", evidence=["r7", "source-a"])
        rows = score.validate(self.opinion, self.batch)
        self.assertTrue(score.summarize(rows, 24, "PASS")["threshold_comparison"]["80"]["content_provisionally_accepted"])

    def test_technical_failure_is_not_averaged_away(self):
        rows = score.validate(self.opinion, self.batch)
        result = score.summarize(rows, 24, "FAIL")["threshold_comparison"]["80"]
        self.assertTrue(result["content_provisionally_accepted"])
        self.assertFalse(result["provisionally_accepted_with_technical"])

    def test_blocker_needs_evidence_and_prevents_automatic_acceptance(self):
        self.opinion["rows"][5].update(block=True, why="换谜底导致无法继续。")
        with self.assertRaises(ValueError):
            score.validate(self.opinion, self.batch)
        self.opinion["rows"][5]["evidence"] = ["r4", "r5"]
        rows = score.validate(self.opinion, self.batch)
        self.assertFalse(score.summarize(rows, 24, "PASS")["threshold_comparison"]["80"]["content_provisionally_accepted"])

    def test_missing_duplicate_and_foreign_turns_rejected(self):
        for replacement in (self.opinion["rows"][:-1], self.opinion["rows"][:-1] + [self.opinion["rows"][0]],
                            self.opinion["rows"][:-1] + [{**self.opinion["rows"][-1], "i": 25}]):
            with self.subTest(replacement=replacement[-1]["i"]), self.assertRaises(ValueError):
                score.validate({"rows": replacement}, self.batch)

    def test_bool_float_out_of_range_and_wrong_dimension_count_rejected(self):
        for ratings in ([True, 5, 5, 5, 5], [5.0] * 5, [6] * 5, [-1] * 5, [5] * 4):
            value = copy.deepcopy(self.opinion)
            value["rows"][0]["s"] = ratings
            with self.subTest(ratings=ratings), self.assertRaises(ValueError):
                score.validate(value, self.batch)

    def test_absent_or_future_evidence_cannot_support_deductions(self):
        for refs in ([], ["r1"], ["not-a-source"]):
            value = copy.deepcopy(self.opinion)
            value["rows"][0].update(s=[2, 5, 5, 5, 5], why="需要纠正。", evidence=refs)
            with self.subTest(refs=refs), self.assertRaises(ValueError):
                score.validate(value, self.batch)

    def test_partial_run_cannot_pass(self):
        rows = score.validate(self.opinion, self.batch)[:-1]
        result = score.summarize(rows, 24, "PASS")
        self.assertFalse(result["complete"])
        self.assertFalse(result["threshold_comparison"]["80"]["content_provisionally_accepted"])

    def test_rubric_hash_frozen_and_static_context_counted(self):
        self.batch.update(category="story", target_i=0, independent_evidence=[], function_events=[])
        body, chars = score.request_body(self.batch, "judge")
        self.assertLessEqual(chars, 1000)
        self.assertEqual({"type": "disabled"}, body["thinking"])
        self.assertNotIn("response_format", body)
        self.assertNotIn("tools", body)
        self.assertNotIn("tool_choice", body)
        self.assertIn("S|4|3|5|4|5|0", body["messages"][0]["content"])
        self.batch["rubric_sha256"] = "changed"
        with self.assertRaises(ValueError):
            score.validate(self.opinion, self.batch)

    def test_per_reply_keeps_history_but_never_future_turns_or_events(self):
        self.batch.update(category="guess", target_i=3,
                          function_events=[{"id": "state-2", "round": 2}, {"id": "state-4", "round": 4}])
        body, _ = score.request_body(self.batch, "judge")
        data = score.strict_json(body["messages"][-1]["content"])
        self.assertEqual([0, 1, 2], [row["i"] for row in data["history"]])
        self.assertEqual(3, data["current_turn"]["i"])
        self.assertEqual("current_turn", list(data)[-1])
        self.assertEqual(["r0", "r1", "r2", "r3", "source-a", "state-2"], data["refs"])
        self.assertEqual(["state-2"], [row["id"] for row in data["function_events"]])
        current = {"i": 3, "s": [3, 5, 5, 5, 5], "why": "本轮遗漏已选动作。", "block": False, "evidence": ["r1", "r3", "state-2"]}
        self.assertEqual(90, score.validate_turn(current, self.batch)["total"])
        with self.assertRaises(ValueError):
            score.validate_turn({**current, "i": 4}, self.batch)
        with self.assertRaises(ValueError):
            score.validate_turn({**current, "evidence": ["state-4"]}, self.batch)

    def test_strict_json_rejects_real_failure_shape_without_quote_repair(self):
        malformed = '{"i":0,"s":[5,5,5,5,5],"why":"可用","block":false,evidence":["r0"]}'
        with self.assertRaises(ValueError):
            score.strict_json(malformed)
        for raw in ('{"i":0,"i":1}', '{"evidence":[],"\\u0065vidence":[]}', '{"s":NaN}', '{"s":Infinity}'):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                score.strict_json(raw)
        self.assertEqual({"why": '台词中含“引号”与\\n文本'}, score.strict_json('{"why":"台词中含“引号”与\\\\n文本"}'))

    def test_provider_requires_complete_primary_score_record(self):
        self.batch["target_i"] = 0
        value = {"choices": [{"finish_reason": "stop", "message": {"content": "回答完整且与前序一致。\nS|5|5|5|5|5|0"}}]}
        self.assertEqual(100, score.provider_score(value, self.batch)["total"])
        altered = copy.deepcopy(value)
        altered["choices"][0]["finish_reason"] = "length"
        with self.assertRaises(ValueError):
            score.provider_score(altered, self.batch)
        altered = copy.deepcopy(value)
        altered["choices"][0]["message"]["tool_calls"] = [{"function": {"name": "score"}}]
        with self.assertRaises(ValueError):
            score.provider_score(altered, self.batch)

    def test_bulk_request_rejected_before_model_invocation(self):
        self.batch.update(category="story")
        with self.assertRaises(ValueError):
            score.request_body(self.batch, "judge")

    def test_function_evidence_is_typed_and_referentially_valid(self):
        self.batch["target_i"] = 3
        opinion = {"i": 3, "s": [3, 5, 5, 5, 5], "why": "该轮没有执行已经选定的动作。",
                   "block": False, "evidence": [1, 3, 4]}
        result = score.indexed_score(opinion, self.batch)
        self.assertEqual(["r1", "r3", "source-a"], result["evidence"])
        for bad in ([-1], [5], [True], ["r3"], ["current_turn:i=3"]):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                score.indexed_score({**opinion, "evidence": bad}, self.batch)

    def test_reference_catalog_cannot_alias_two_sources(self):
        self.batch["independent_evidence"] = [{"id": "r0"}]
        with self.assertRaises(ValueError):
            score.reference_catalog(self.batch, 0)

    def test_record_protocol_preserves_free_text_quotes_commas_and_newlines(self):
        self.batch["target_i"] = 3
        rationale = '原文含“引号”、逗号和JSON示意 {bad: "json"}。\n第二段说明相反事实，仍保留原文。'
        result = score.parse_score_record(rationale + '\nS|4|5|3|4|5|0\n', self.batch)
        self.assertEqual(rationale + '\n', result["why"])
        self.assertEqual(82, result["total"])
        self.assertEqual(["r3"], result["evidence"])

    def test_record_protocol_rejects_missing_or_repaired_fields(self):
        self.batch["target_i"] = 3
        for terminal in ('S|5|5|5|5|0', 'S|6|5|5|5|5|0', 'S|5|5|5|5|5|2',
                         'S|5|5|5|5|5|0|500', 'S|5.0|5|5|5|5|0',
                         'S|5|5|5|5|5|0\n```', '{"s":[5,5,5,5,5]}', 'S|5|5|5|5|5|0S|5|5|5|5|5|0'):
            with self.subTest(terminal=terminal), self.assertRaises(ValueError):
                score.parse_score_record('证据说明。\n' + terminal, self.batch)
        with self.assertRaises(ValueError):
            score.parse_score_record('S|5|5|5|5|5|0', self.batch)

    def test_stream_transport_preserves_all_deltas_and_requires_completion(self):
        chunks = [
            {"choices": [{"index": 0, "delta": {"content": '解释含“引号”'}, "finish_reason": None}]},
            {"choices": [{"index": 0, "delta": {"content": '\nS|5|5|5|5|5|0'}, "finish_reason": None}]},
            {"choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}]},
            {"choices": [], "usage": {"prompt_tokens": 10}},
        ]
        stream = ''.join('data: ' + score.compact(chunk) + '\n\n' for chunk in chunks) + 'data: [DONE]\n\n'
        value = score.decode_provider_response(stream)
        self.assertEqual('解释含“引号”\nS|5|5|5|5|5|0', value['choices'][0]['message']['content'])
        with self.assertRaises(ValueError):
            score.decode_provider_response(stream.replace('data: [DONE]\n\n', ''))
        with self.assertRaises(ValueError):
            score.decode_provider_response(stream.replace('"finish_reason":"stop"', '"finish_reason":"length"'))

    def test_content_grading_never_substitutes_asr_for_original_question(self):
        self.batch.update(category="guess", target_i=0, turns=[{
            "i": 0, "intended": "Is it a mammal?", "asr": "Is it a Mammoth?",
            "reply": "Yes, it is a mammal."}])
        original = copy.deepcopy(self.batch)
        body, _ = score.request_body(self.batch, "judge")
        data = score.strict_json(body['messages'][-1]['content'])
        self.assertNotIn('asr', data['current_turn'])
        self.assertEqual('Is it a mammal?', data['current_turn']['intended'])
        self.assertEqual(original, self.batch)

    def test_reasoning_is_explicit_and_does_not_change_default_or_rubric(self):
        self.batch.update(category="figure", target_i=0)
        disabled, count = score.request_body(self.batch, "judge")
        enabled, enabled_count = score.request_body(self.batch, "judge", thinking="enabled")
        self.assertEqual({"type": "disabled"}, disabled['thinking'])
        self.assertEqual({"type": "enabled"}, enabled['thinking'])
        self.assertEqual(disabled['messages'], enabled['messages'])
        self.assertEqual(count, enabled_count)
        with self.assertRaises(ValueError):
            score.request_body(self.batch, "judge", thinking="automatic")


if __name__ == "__main__":
    unittest.main()
