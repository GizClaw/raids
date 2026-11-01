"""Noncompensatory per-reply scoring; semantic judgments are supplied by Root."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUBRIC = ROOT / "tests/giztest/judges/reply-score-v2.json"


def rubric():
    return json.loads(RUBRIC.read_text())


def rubric_sha256():
    return hashlib.sha256(RUBRIC.read_bytes()).hexdigest()


def calculate(ratings, impact):
    policy = rubric()
    if not isinstance(ratings, list) or len(ratings) != 5 or any(
        type(n) is not int or not 0 <= n <= 5 for n in ratings
    ):
        raise ValueError("Five integer ratings from zero to five required")
    if impact not in policy["impacts"]:
        raise ValueError("Unknown task impact")
    base = sum(w * n / 5 for w, n in zip(policy["weights"], ratings))
    cap = policy["impacts"][impact]["cap"]
    return {"base_total": base, "impact_cap": cap, "total": min(base, cap)}


def validate_row(row):
    if not isinstance(row.get("core_task"), str) or not row["core_task"].strip():
        raise ValueError("An explicit current core task is required")
    if not isinstance(row.get("why"), str) or not row["why"].strip():
        raise ValueError("A contextual scoring rationale is required")
    ratings = row.get("s", row.get("ratings"))
    values = calculate(ratings, row.get("impact"))
    impact = row["impact"]
    minimum = min(ratings)
    if impact == "intact" and ratings != [5] * 5:
        raise ValueError("An intact task cannot have a deducted dimension")
    if impact == "minor" and minimum != 4:
        raise ValueError("A minor issue must use the local-defect dimension anchor")
    limits = {"material": 3, "core": 2, "missed": 1, "unusable": 0}
    if impact in limits and minimum > limits[impact]:
        raise ValueError("Affected dimensions do not reflect the recorded task impact")
    for key, value in values.items():
        if row.get(key) != value:
            raise ValueError("Stored " + key + " differs from rubric calculation")
    if row["impact"] != "intact" and not row.get("evidence"):
        raise ValueError("A deduction needs actual evidence locators")
    return values
