"""Report integrity: private evidence stays local; incomplete runs have no grade."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import build_report_site as site


def dialogue_row(number=0):
    return {"round": number, "intended": "A real question", "reply": "A real reply", "heard": "A real question",
            "authorization": "PRIVATE_AUTH_SENTINEL", "reasoning_content": "PRIVATE_REASONING_SENTINEL",
            "hidden_answer": "PRIVATE_ANSWER_SENTINEL"}


class PublicReportTests(unittest.TestCase):
    def test_only_public_dialogue_fields_are_exported(self):
        row = site.public_rows([dialogue_row()])[0]
        text = json.dumps(row)
        self.assertNotIn("PRIVATE_", text)
        self.assertEqual(row["intended"], "A real question")
        self.assertIsNone(row["score"])

    def test_wrong_score_binding_is_rejected(self):
        scores = {"rows": [{"i": 0, "s": [5] * 5, "why": "Evidence", "dialogue_sha256": "wrong"}]}
        with self.assertRaisesRegex(ValueError, "bind"):
            site.public_rows([dialogue_row()], scores)

    def test_multiple_scores_cannot_select_the_last(self):
        row = {"i": 0, "s": [5] * 5, "why": "Evidence"}
        with self.assertRaisesRegex(ValueError, "Duplicate scores"):
            site.public_rows([dialogue_row()], {"rows": [row, row]}, historical=True)

    def test_weighted_score_uses_ratings(self):
        original = dialogue_row()
        binding = hashlib.sha256(json.dumps({k: original[k] for k in ("round", "intended", "reply")},
                                            ensure_ascii=False, sort_keys=True).encode()).hexdigest()
        scores = {"rows": [{"i": 0, "s": [5, 4, 4, 5, 5], "why": "Two supported local issues",
                            "dialogue_sha256": binding}]}
        rows = site.public_rows([original], scores)
        self.assertEqual(rows[0]["score"]["total"], 90)
        summary = site.summarize(rows, False)
        self.assertEqual(summary["mean"], 90)
        self.assertEqual(summary["rated_replies"], 1)
        self.assertIsNone(summary["stddev"])
        self.assertFalse(summary["scoring_complete"])

    def test_v2_report_uses_effective_score_instead_of_old_weighted_score(self):
        original = dialogue_row()
        binding = hashlib.sha256(json.dumps(
            {k: original[k] for k in ("round", "intended", "reply")},
            ensure_ascii=False, sort_keys=True).encode()).hexdigest()
        ratings = [5, 2, 5, 5, 5]
        scores = {
            "rubric_version": "reply-score-v2.0",
            "rubric_sha256": site.reply_scores_v2.rubric_sha256(),
            "rows": [{
                "i": 0, "s": ratings, "why": "The key-object recap contradicts prior handling.",
                "dialogue_sha256": binding, "core_task": "Recall key-object custody.",
                "impact": "core", "evidence": ["r0"],
                **site.reply_scores_v2.calculate(ratings, "core"),
            }],
        }
        rows = site.public_rows([original], scores)
        self.assertEqual(85, rows[0]["score"]["base_total"])
        self.assertEqual(40, rows[0]["score"]["total"])
        summary = site.summarize(rows, False)
        self.assertEqual(40, summary["mean"])
        self.assertEqual(1, summary["impact_counts"]["core"])
        session = {
            "title": "Example", "language": "en", "candidate_sha256": "candidate",
            "rows": rows, "summary": summary, "scoring_version": "reply-score-v2.0",
        }
        text = site.log_text(session, "test", "2026-10-30")
        self.assertIn("评分：40/100", text)
        self.assertIn("基础分 85；上限 40", text)
        scores["rows"][0]["total"] = 90
        with self.assertRaisesRegex(ValueError, "total"):
            site.public_rows([original], scores)

    def test_summary_only_reports_numeric_scores(self):
        rows = [{"score": {"total": 100 if i < 46 else 79, "block": False}} for i in range(52)]
        summary = site.summarize(rows, True)
        self.assertGreater(summary["mean"], 90)
        self.assertEqual(summary["minimum"], 79)
        self.assertEqual(summary["maximum"], 100)
        self.assertEqual(summary["rated_replies"], 52)
        self.assertNotIn("thresholds", summary)
        self.assertNotIn("pass", summary)

    def test_v3_presentation_is_local_but_core_failure_stays_capped(self):
        original = dialogue_row()
        binding = hashlib.sha256(json.dumps(
            {k: original[k] for k in ("round", "intended", "reply")},
            ensure_ascii=False, sort_keys=True).encode()).hexdigest()
        row = {
            "i": 0, "s": [5, 5, 5, 5, 4], "why": "NPC dialogue is direct; identity and action remain clear.",
            "dialogue_sha256": binding, "core_task": "Answer the current question.",
            "user_effect": "The answer is usable; only role presentation needs cleanup.",
            "impact": "minor", "issue_kind": "presentation", "issue_family": "role-presentation",
            "evidence": ["current"], **site.reply_scores_v3.calculate([5, 5, 5, 5, 4], "minor"),
        }
        scores = {"rubric_version": "reply-score-v3.0",
                  "rubric_sha256": site.reply_scores_v3.rubric_sha256(), "rows": [row]}
        rows = site.public_rows([original], scores)
        self.assertEqual(98, rows[0]["score"]["total"])
        self.assertEqual(1, site.summarize(rows, False)["issue_counts"]["presentation"])
        self.assertEqual(row["user_effect"], rows[0]["score"]["user_effect"])
        row.update(s=[5, 2, 5, 5, 5], impact="core", issue_kind="state",
                   **site.reply_scores_v3.calculate([5, 2, 5, 5, 5], "core"))
        self.assertEqual(40, site.public_rows([original], scores)[0]["score"]["total"])

    def test_partial_scores_have_sample_statistics(self):
        rows = [{"score": {"total": 70}}, {"score": None}, {"score": {"total": 90}}]
        summary = site.summarize(rows, False)
        self.assertEqual(summary["mean"], 80)
        self.assertEqual(summary["minimum"], 70)
        self.assertEqual(summary["maximum"], 90)
        self.assertEqual(summary["rated_replies"], 2)
        self.assertEqual(summary["available_replies"], 3)
        self.assertEqual(summary["variance"], 100)
        self.assertEqual(summary["stddev"], 10)
        self.assertFalse(summary["scoring_complete"])

    def test_pending_fact_check_is_neither_zero_nor_full_marks(self):
        rows = site.public_rows([dialogue_row()], pending=[{"round": 0, "reason": "A key date needs primary evidence"}])
        self.assertIsNone(rows[0]["score"])
        self.assertEqual(rows[0]["review_note"], "A key date needs primary evidence")
        self.assertIsNone(site.summarize(rows, False))

    def test_log_page_keeps_full_text_and_escapes_markup(self):
        row = site.public_rows([{
            **dialogue_row(),
            "intended": "Question <script>alert(1)</script>",
            "reply": "Complete reply\nSecond line & original words",
        }])[0]
        data = {"runtime": "test", "updated_at": "2026-10-29", "archives": [], "sessions": [{
            "id": "example-en", "title": "Example", "language": "en", "official": False,
            "summary": None, "candidate_sha256": "candidate", "rows": [row],
        }]}
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary)
            (output / "report.css").write_text("")
            site.write_logs(data, output)
            document = (output / "logs/example-en.html").read_text()
            self.assertIn("Question &lt;script&gt;alert(1)&lt;/script&gt;", document)
            self.assertIn("Complete reply\nSecond line &amp; original words", document)
            self.assertNotIn("<script>", document)
            self.assertNotIn("PRIVATE_", document)
            self.assertNotIn("download", document)
            self.assertFalse(list(output.rglob("*.txt")))
            self.assertEqual(data["sessions"][0]["logs"], {"html": "logs/example-en.html"})

    def test_opening_is_not_counted_as_a_dialogue_turn(self):
        session = {
            "title": "Example", "language": "en", "expected": 52, "official": False,
            "summary": None, "candidate_sha256": "candidate",
            "rows": site.public_rows([dialogue_row(0), dialogue_row(1)]),
        }
        text = site.log_text(session, "test", "2026-10-29")
        self.assertIn("对话轮次：1/51", text)
        self.assertIn("开场回复：1 条（不计对话轮次）", text)

    def test_fully_scored_short_run_has_no_official_grade(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "workflows/a").mkdir(parents=True)
            (root / "web/reports").mkdir(parents=True)
            (root / "README.md").write_text('<a id="reply-scoring-v1"></a>\nRules\n## Catalog behavior notes\n')
            for name in ("index.html", "report.css", "report.js"):
                (root / "web/reports" / name).write_text("")
            (root / "workflows/a/raid.json").write_text(json.dumps({
                "id": "a", "category": "story", "title": {"en": "English-only catalog title"}, "summary": {"en": "Summary"}}))
            campaign = root / "campaign"
            (campaign / "a-en").mkdir(parents=True)
            (campaign / "plan.json").write_text(json.dumps({
                "cases": {"a": {"title": "A", "category": "story", "catalog_id": "a",
                                "source_sha256": "source", "candidate_sha256": "candidate"}},
                "sessions": [{"id": "a-en", "case": "a", "language": "en"}], "runtime": [{"version": "test"}]}))
            row = dialogue_row()
            binding = hashlib.sha256(json.dumps({k: row[k] for k in ("round", "intended", "reply")},
                                                ensure_ascii=False, sort_keys=True).encode()).hexdigest()
            (campaign / "a-en/dialogue.json").write_text(json.dumps([row]))
            (campaign / "a-en/log-scores.json").write_text(json.dumps({
                "candidate_sha256": "candidate", "rows": [{"i": 0, "s": [5] * 5, "why": "Supported",
                                                           "dialogue_sha256": binding}]}))
            with patch.object(site, "ROOT", root):
                data = site.build(campaign, root / "site", include_history=False)
            session = data["sessions"][0]
            self.assertFalse(session["complete"])
            self.assertFalse(session["official"])
            self.assertEqual(session["summary"]["mean"], 100)
            self.assertFalse(session["summary"]["scoring_complete"])
            self.assertEqual(session["rows"][0]["score"]["total"], 100)
            self.assertNotIn("PRIVATE_", (root / "site/report.json").read_text())
            self.assertNotIn("technical", session)
            self.assertNotIn("block", session["rows"][0]["score"])
            (campaign / "r2-a-en").mkdir()
            fresh = {**dialogue_row(), "reply": "A different fresh-session reply"}
            (campaign / "r2-a-en/dialogue.json").write_text(json.dumps([fresh]))
            (campaign / "attempts.json").write_text(json.dumps({
                "current": {"a-en": "r2-a-en"}, "archives": ["a-en"]}))
            with patch.object(site, "ROOT", root):
                data = site.build(campaign, root / "fresh-site", include_history=False)
            current, archive = data["sessions"][0], data["archives"][0]
            self.assertEqual(len(current["rows"]), 1)
            self.assertEqual(current["rows"][0]["reply"], fresh["reply"])
            self.assertIsNone(current["summary"])
            self.assertFalse(current["complete"])
            self.assertEqual(archive["summary"]["mean"], 100)
            self.assertEqual(archive["logs"]["html"], "logs/a-en.html")
            self.assertEqual(current["logs"]["html"], "logs/r2-a-en.html")
            self.assertTrue((root / "fresh-site/logs/a-en.html").exists())
            (campaign / "r2-a-en/status.json").write_text(json.dumps({"status": "incomplete"}))
            (campaign / "r2-a-en/once.claim").write_text("123")
            owner = {"schema": "six51-parallel-owner/v1", "session_id": "r2-a-en", "pid": 123,
                     "candidate_sha256": "candidate", "status": "running"}
            (campaign / "r2-a-en/parallel-owner.json").write_text(json.dumps(owner))
            with patch.object(site, "ROOT", root):
                data = site.build(campaign, root / "owned-site", include_history=False)
            self.assertEqual(data["sessions"][0]["status"], "running")
            owner["pid"] = 124
            (campaign / "r2-a-en/parallel-owner.json").write_text(json.dumps(owner))
            with patch.object(site, "ROOT", root):
                data = site.build(campaign, root / "wrong-owner-site", include_history=False)
            self.assertEqual(data["sessions"][0]["status"], "incomplete")
            (campaign / "attempts.json").write_text(json.dumps({
                "current": {"a-en": "../a-en"}, "archives": []}))
            with patch.object(site, "ROOT", root), self.assertRaisesRegex(ValueError, "Unsafe"):
                site.build(campaign, root / "unsafe-site", include_history=False)


if __name__ == "__main__":
    unittest.main()
