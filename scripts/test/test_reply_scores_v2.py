import copy
import unittest

import reply_scores_v2 as scoring


class TaskImpactScoringTests(unittest.TestCase):
    def test_core_result_cannot_be_compensated_by_fluent_expression(self):
        self.assertEqual(40, scoring.calculate([5, 3, 5, 5, 5], "core")["total"])
        self.assertEqual(40, scoring.calculate([5] * 5, "core")["total"])

    def test_wholly_wrong_language_and_unanswered_task_have_same_impact_cap(self):
        self.assertEqual(20, scoring.calculate([5, 5, 5, 5, 0], "missed")["total"])
        self.assertEqual(20, scoring.calculate([1, 2, 5, 5, 5], "missed")["total"])

    def test_secondary_error_differs_from_core_answer_error(self):
        self.assertEqual(70, scoring.calculate([5, 5, 3, 5, 5], "material")["total"])
        self.assertEqual(40, scoring.calculate([5, 5, 3, 5, 5], "core")["total"])

    def test_minor_does_not_become_core_failure(self):
        self.assertEqual(90, scoring.calculate([5, 5, 5, 5, 4], "minor")["total"])
        self.assertEqual(100, scoring.calculate([5] * 5, "intact")["total"])

    def test_base_below_cap_remains_below_cap(self):
        self.assertEqual(0, scoring.calculate([0] * 5, "core")["total"])
        self.assertEqual(20, scoring.calculate([1] * 5, "minor")["total"])

    def test_unknown_and_bad_ratings_cannot_be_converted_to_a_number(self):
        for ratings in (None, [True] * 5, [5.0] * 5, [6] * 5, [5] * 4):
            with self.subTest(ratings=ratings), self.assertRaises(ValueError):
                scoring.calculate(ratings, "intact")
        with self.assertRaises(ValueError):
            scoring.calculate([5] * 5, "pending")

    def test_evidence_task_and_stored_effective_total_are_required(self):
        row = {
            "s": [5, 2, 5, 5, 5], "impact": "core",
            "core_task": "Recall the last inkstone handling.",
            "why": "The recap contradicts the board and writing in round two.",
            "evidence": ["r2", "current"],
            **scoring.calculate([5, 2, 5, 5, 5], "core"),
        }
        scoring.validate_row(row)
        for key in ("core_task", "why", "evidence"):
            modified = copy.deepcopy(row)
            modified.pop(key)
            with self.subTest(key=key), self.assertRaises(ValueError):
                scoring.validate_row(modified)
        with self.assertRaises(ValueError):
            scoring.validate_row({**row, "total": 90})

    def test_diagnostic_levels_and_task_impact_must_be_consistent(self):
        for impact, ratings in [
            ("intact", [5, 4, 5, 5, 5]),
            ("minor", [5, 2, 5, 5, 5]),
            ("material", [5, 4, 5, 5, 5]),
            ("core", [5, 4, 5, 5, 5]),
            ("missed", [2, 5, 5, 5, 5]),
        ]:
            row = {
                "s": ratings, "impact": impact, "core_task": "A current task",
                "why": "Explicit current evidence", "evidence": ["current"],
                **scoring.calculate(ratings, impact),
            }
            with self.subTest(impact=impact), self.assertRaises(ValueError):
                scoring.validate_row(row)


if __name__ == "__main__":
    unittest.main()
