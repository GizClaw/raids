import unittest
import reply_scores_v3 as scoring


def record(ratings, impact, kind, family="example"):
    return {
        "s": ratings, "impact": impact, "issue_kind": kind,
        "issue_family": family, "core_task": "Answer the current question.",
        "user_effect": "The answer remains clear; only role segmentation needs cleanup.",
        "why": "A concrete current passage and its task consequence.",
        "evidence": ["current"], **scoring.calculate(ratings, impact),
    }


class ExperienceScoringTests(unittest.TestCase):
    def test_presentation_only_has_local_cost(self):
        row = record([5, 5, 5, 5, 4], "minor", "presentation")
        self.assertEqual(98, scoring.validate_row(row)["total"])
        self.assertEqual(100, row["impact_cap"])

    def test_presentation_cannot_be_upgraded_to_whole_reply_failure(self):
        for impact in ("material", "core", "missed"):
            row = record([2, 2, 5, 5, 3], impact, "presentation")
            with self.subTest(impact=impact), self.assertRaises(ValueError):
                scoring.validate_row(row)

    def test_background_name_prefix_and_explicit_failed_name_correction_differ(self):
        secondary = record([5, 5, 5, 5, 4], "minor", "secondary_preference")
        correction = record([2, 5, 5, 5, 5], "core", "state")
        correction["user_effect"] = "The current name correction is still wrong and needs another correction."
        self.assertEqual(98, scoring.validate_row(secondary)["total"])
        self.assertEqual(40, scoring.validate_row(correction)["total"])

    def test_core_error_cannot_be_compensated_by_expression(self):
        self.assertEqual(40, scoring.calculate([5, 2, 5, 5, 5], "core")["total"])
        self.assertEqual(40, scoring.calculate([5] * 5, "core")["total"])

    def test_missing_delivery_and_wrong_language_remain_twenty(self):
        self.assertEqual(20, scoring.validate_row(
            record([1, 2, 5, 5, 5], "missed", "main_missing"))["total"])
        self.assertEqual(20, scoring.validate_row(
            record([5, 5, 5, 5, 0], "missed", "wrong_language"))["total"])

    def test_partial_fact_and_core_fact_keep_distinct_impacts(self):
        self.assertEqual(70, scoring.validate_row(
            record([5, 5, 3, 5, 5], "material", "secondary_fact"))["total"])
        self.assertEqual(40, scoring.validate_row(
            record([5, 5, 2, 5, 5], "core", "core_fact"))["total"])

    def test_pending_cannot_be_given_a_default_number(self):
        with self.assertRaises(ValueError):
            scoring.calculate([5] * 5, "pending")

    def test_explicit_effect_and_issue_family_required(self):
        base = record([5, 5, 5, 5, 4], "minor", "presentation")
        for key in ("user_effect", "why", "core_task", "evidence", "issue_family"):
            row = dict(base)
            row.pop(key)
            with self.subTest(key=key), self.assertRaises(ValueError):
                scoring.validate_row(row)

    def test_forged_totals_are_rejected(self):
        row = record([5, 2, 5, 5, 5], "core", "state")
        row["total"] = 85
        with self.assertRaisesRegex(ValueError, "total"):
            scoring.validate_row(row)

    def test_intact_has_no_deduction(self):
        row = record([5] * 5, "intact", "none", None)
        self.assertEqual(100, scoring.validate_row(row)["total"])
        row["s"][-1] = 4
        row.update(scoring.calculate(row["s"], "intact"))
        with self.assertRaises(ValueError):
            scoring.validate_row(row)

    def test_invalid_ratings_rejected(self):
        for ratings in (None, [True] * 5, [5.0] * 5, [6] * 5, [5] * 4):
            with self.subTest(ratings=ratings), self.assertRaises(ValueError):
                scoring.calculate(ratings, "minor")


if __name__ == "__main__":
    unittest.main()
