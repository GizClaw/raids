"""Experience-based task impact: local presentation defects have local cost."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUBRIC = ROOT / "tests/giztest/judges/reply-score-v3.json"


def rubric():
    return json.loads(RUBRIC.read_text())


def rubric_sha256():
    return hashlib.sha256(RUBRIC.read_bytes()).hexdigest()


def calculate(ratings, impact):
    policy = rubric()
    if not isinstance(ratings, list) or len(ratings) != 5 or any(
        type(v) is not int or not 0 <= v <= 5 for v in ratings
    ):
        raise ValueError("Five integer ratings from zero to five required")
    if impact not in policy["impacts"]:
        raise ValueError("Unknown task impact")
    base = sum(weight * value / 5 for weight, value in zip(policy["weights"], ratings))
    cap = policy["impacts"][impact]["cap"]
    return {"base_total": base, "impact_cap": cap, "total": min(base, cap)}


def validate_row(row):
    for key in ("core_task", "user_effect", "why"):
        if not isinstance(row.get(key), str) or not row[key].strip():
            raise ValueError("Explicit " + key + " required")
    ratings = row.get("s", row.get("ratings"))
    impact = row.get("impact")
    values = calculate(ratings, impact)
    issue = row.get("issue_kind")
    if issue not in rubric()["issue_kinds"]:
        raise ValueError("Unknown issue kind")
    if impact == "intact":
        if ratings != [5] * 5 or issue != "none":
            raise ValueError("Intact task must have no deducted dimension or issue")
    else:
        if issue == "none" or not row.get("evidence") or not row.get("issue_family"):
            raise ValueError("A deduction needs actual evidence and an issue family")
    if impact == "minor" and min(ratings) != 4:
        raise ValueError("Minor issue must use local-defect diagnostic anchors")
    for key, limit in {"material": 3, "core": 2, "missed": 1, "unusable": 0}.items():
        if impact == key and min(ratings) > limit:
            raise ValueError("Diagnostics do not reflect task impact")
    if issue in ("presentation", "secondary_preference") and impact not in ("minor", "intact"):
        raise ValueError("Presentation or secondary preference alone cannot cap the whole task")
    if issue in ("main_missing", "wrong_language") and impact != "missed":
        raise ValueError("Missing main delivery or wrong language needs the missed anchor")
    for key, value in values.items():
        if row.get(key) != value:
            raise ValueError("Stored " + key + " differs from rubric")
    return values
