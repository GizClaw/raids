"""Build a public, allowlisted report without copying private test evidence."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import html
import json
from pathlib import Path
import shutil
import statistics
import string
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import reply_scores_v2
import reply_scores_v3

ROOT = Path(__file__).resolve().parents[2]
WEIGHTS = [25, 25, 25, 15, 10]


def read(path, default=None):
    return json.loads(path.read_text()) if path.exists() else default


def public_rows(dialogue, scores=None, historical=False, pending=None):
    version = (scores or {}).get("rubric_version", "reply-score-v1")
    policies = {"reply-score-v2.0": reply_scores_v2, "reply-score-v3.0": reply_scores_v3}
    policy = policies.get(version)
    if version not in ("reply-score-v1", *policies):
        raise ValueError("Unknown scoring rubric version")
    if policy and (scores or {}).get("rubric_sha256") != policy.rubric_sha256():
        raise ValueError("Scoring rubric hash mismatch")
    score_rows = (scores or {}).get("rows", [])
    ratings_by_round = {r["i"]: r for r in score_rows}
    if len(ratings_by_round) != len(score_rows):
        raise ValueError("Duplicate scores")
    if set(ratings_by_round) - {r["round"] for r in dialogue}:
        raise ValueError("Score has no corresponding actual dialogue")
    pending_by_round = {}
    for item in pending or []:
        number, reason = item.get("round"), item.get("reason")
        if type(number) is not int or number in pending_by_round or not isinstance(reason, str) or not reason.strip():
            raise ValueError("Invalid pending fact check")
        pending_by_round[number] = reason
    result = []
    for row in dialogue:
        i = row["round"]
        if type(i) is not int or not 0 <= i <= 51:
            raise ValueError("Invalid round")
        item = {"round": i, "intended": row["intended"], "reply": row["reply"], "heard": row.get("heard"), "score": None}
        if not all(isinstance(item[k], str) and item[k] for k in ("intended", "reply")):
            raise ValueError("Missing actual dialogue")
        if i in ratings_by_round:
            score = ratings_by_round[i]
            levels = score.get("s", score.get("ratings"))
            if len(levels) != 5 or any(type(v) is not int or not 0 <= v <= 5 for v in levels):
                raise ValueError("Invalid five-dimension rating")
            if not isinstance(score.get("why"), str) or not score["why"].strip():
                raise ValueError("Missing scoring reason")
            if not historical:
                actual_hash = hashlib.sha256(json.dumps(
                    {k: item[k] for k in ("round", "intended", "reply")}, ensure_ascii=False, sort_keys=True).encode()).hexdigest()
                if score.get("dialogue_sha256") != actual_hash:
                    raise ValueError("Score does not bind this actual dialogue")
            if policy:
                calculated = policy.validate_row(score)
                item["score"] = {
                    "ratings": levels, **calculated, "why": score["why"],
                    "version": version, "core_task": score["core_task"],
                    "impact": score["impact"],
                    "impact_label": policy.rubric()["impacts"][score["impact"]]["label"],
                }
                if version == "reply-score-v3.0":
                    item["score"].update({
                        key: score[key] for key in ("user_effect", "issue_kind", "issue_family")
                    })
            else:
                item["score"] = {"ratings": levels, "total": sum(w * n / 5 for w, n in zip(WEIGHTS, levels)),
                                 "why": score["why"]}
        elif i in pending_by_round:
            item["review_note"] = pending_by_round[i]
        result.append(item)
    if len({r["round"] for r in result}) != len(result):
        raise ValueError("Duplicate rounds")
    return sorted(result, key=lambda r: r["round"])


def summarize(rows, official):
    totals = [r["score"]["total"] for r in rows if r.get("score")]
    if not totals:
        return None
    result = {
        "mean": round(statistics.fmean(totals), 2),
        "minimum": min(totals), "maximum": max(totals),
        "rated_replies": len(totals), "available_replies": len(rows),
        "stddev": round(statistics.pstdev(totals), 2) if len(totals) > 1 else None,
        "variance": round(statistics.pvariance(totals), 4) if len(totals) > 1 else None,
        "scoring_complete": bool(official),
    }
    if any(r.get("score", {}).get("version") in ("reply-score-v2.0", "reply-score-v3.0")
           for r in rows if r.get("score")):
        result["impact_counts"] = {
            impact: sum(r.get("score", {}).get("impact") == impact for r in rows if r.get("score"))
            for impact in reply_scores_v2.rubric()["impacts"]
        }
    if any(r.get("score", {}).get("version") == "reply-score-v3.0" for r in rows if r.get("score")):
        result["issue_counts"] = {
            kind: sum(r.get("score", {}).get("issue_kind") == kind for r in rows if r.get("score"))
            for kind in reply_scores_v3.rubric()["issue_kinds"] if kind != "none"
        }
    return result


def log_text(session, runtime, updated_at):
    labels = ["回应与推进", "连贯与规则", "事实与逻辑", "互动表达", "角色与语言"]
    language = {"zh": "中文", "en": "English", "mixed": "混合"}[session["language"]]
    rows = session["rows"]
    lines = [
        f'剧本：{session["title"]}', f"语言：{language}",
        f'对话轮次：{sum(r["round"] > 0 for r in rows)}/{session.get("expected", 52) - 1}',
        f'开场回复：{sum(r["round"] == 0 for r in rows)} 条（不计对话轮次）',
        f'已评分回复：{sum(bool(r["score"]) for r in rows)} 条（含开场）',
        f'GizClaw：{session.get("runtime", runtime)}',
        f'候选 SHA256：{session["candidate_sha256"]}', f"更新时间：{updated_at}",
    ]
    summary = session.get("summary")
    if summary:
        deviation = summary["stddev"] if summary["stddev"] is not None else "—（不足两条）"
        lines.extend([
            f'当前统计样本：{summary["rated_replies"]}/{len(rows)} 条已记录回复',
            f'平均分：{summary["mean"]}；最低分：{summary["minimum"]}；最高分：{summary["maximum"]}',
            f"标准差：{deviation}（单位：分）",
        ])
    if session.get("interruption"):
        lines.extend(["", "中断记录：", session["interruption"]])
    if session.get("note"):
        lines.extend(["", session["note"]])
    version = session.get("scoring_version")
    if version in ("reply-score-v2.0", "reply-score-v3.0"):
        lines.extend(["", f"评分口径：{version}；最终分为分项基础分与任务影响上限的较小值。",
                      "任务影响数量：" + json.dumps(
                          (session.get("summary") or {}).get("impact_counts", {}),
                          ensure_ascii=False)])
        if version == "reply-score-v3.0":
            lines.extend(["小问题只扣对应分项，不另压到90或70；关键结果错误上限40，主要交付缺失/答错语种上限20。",
                          "同类问题出现数量（不是独立缺陷数）：" + json.dumps(
                              (session.get("summary") or {}).get("issue_counts", {}), ensure_ascii=False)])
    for row in rows:
        lines.extend(["", "=" * 72, "开场" if row["round"] == 0 else f'第 {row["round"]} 轮',
                      "", "用户原话：", row["intended"], "", "主持完整回复：", row["reply"]])
        score = row["score"]
        if score:
            lines.extend(["", f'评分：{score["total"]:g}/100',
                          "；".join(f"{name} {rating}/5" for name, rating in zip(labels, score["ratings"]))])
            if score.get("version") in ("reply-score-v2.0", "reply-score-v3.0"):
                lines.extend([
                    "本轮核心任务：" + score["core_task"],
                    f'任务影响：{score["impact_label"]}；基础分 {score["base_total"]:g}；上限 {score["impact_cap"]:g}。',
                ])
                if score.get("version") == "reply-score-v3.0":
                    lines.append("对用户的具体影响：" + score["user_effect"])
            lines.extend(["评分依据：", score["why"]])
        else:
            lines.extend(["", "评分：待核查" if row.get("review_note") else "评分：待评分"])
            if row.get("review_note"):
                lines.extend(["待核查原因：", row["review_note"]])
        if row.get("heard") and row["heard"] != row["intended"]:
            lines.extend(["", "ASR 转写：", row["heard"]])
    if not rows:
        lines.extend(["", "尚无对话日志。"])
    return "\n".join(lines) + "\n"


def write_logs(data, output):
    directory = output / "logs"
    directory.mkdir(exist_ok=True)
    css_version = hashlib.sha256((output / "report.css").read_bytes()).hexdigest()[:12]
    allowed = set(string.ascii_lowercase + string.digits + "-_")
    for session in data["sessions"] + data["archives"]:
        name = session["id"]
        if not name or any(c not in allowed for c in name):
            raise ValueError("Unsafe session log filename")
        text = log_text(session, data["runtime"], data["updated_at"])
        session["logs"] = {"html": f"logs/{name}.html"}
        title = html.escape(session["title"] + " / " + session["language"] + " 日志")
        document = (
            '<!doctype html>\n<html lang="zh-CN"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            f"<title>{title}</title>"
            f'<link rel="stylesheet" href="../report.css?v={css_version}"></head>'
            f'<body><main class="log-page"><header><h1>{title}</h1>'
            '<a href="../">返回报告</a></header>'
            f'<pre class="plain-log">{html.escape(text)}</pre></main></body></html>\n'
        )
        (directory / (name + ".html")).write_text(document, encoding="utf-8")


def build(campaign, output, include_history=True):
    plan = read(campaign / "plan.json")
    attempts = read(campaign / "attempts.json", {"current": {}, "archives": []})
    current_ids = {v["catalog_id"] for v in plan["cases"].values()}
    catalog = []
    for file in sorted((ROOT / "workflows").glob("*/raid.json")):
        value = read(file)
        title, summary = value["title"], value.get("summary", {})
        catalog.append({"id": value["id"], "title": title.get("zh-CN", title.get("en", value["id"])),
                        "title_en": title.get("en", title.get("zh-CN", value["id"])),
                        "summary": summary.get("zh-CN", summary.get("en", "")), "category": value["category"],
                        "tags": value.get("tags", []), "current": value["id"] in current_ids})
    samples = [{"key": key, **{k: v[k] for k in ("title", "category", "catalog_id", "source_sha256")}}
               for key, v in plan["cases"].items()]
    def load_session(session, name):
        if not name or any(c not in string.ascii_lowercase + string.digits + "-_" for c in name):
            raise ValueError("Unsafe attempt directory")
        case = session["case"]
        record = plan["cases"][case]
        dialogue = read(campaign / name / "dialogue.json", [])
        scores = read(campaign / name / "log-scores.json")
        if scores and scores.get("candidate_sha256") != record["candidate_sha256"]:
            raise ValueError("Scoring candidate mismatch: " + name)
        pending = read(campaign / name / "pending-content-review.json", {}).get("pending", [])
        rows = public_rows(dialogue, scores, pending=pending)
        complete = [r["round"] for r in rows] == list(range(52))
        official = complete and all(r["score"] for r in rows)
        status = read(campaign / name / "status.json", {}).get("status", "queued")
        owner = read(campaign / name / "parallel-owner.json")
        claim = campaign / name / "once.claim"
        if owner and owner.get("schema") == "six51-parallel-owner/v1":
            owns_claim = claim.exists() and claim.read_text().strip() == str(owner.get("pid"))
            if (owns_claim and owner.get("session_id") == name
                    and owner.get("candidate_sha256") == record["candidate_sha256"]
                    and owner.get("status") in ("running", "collected", "incomplete")):
                status = owner["status"]
        if official:
            status = "scored"
        elif complete and (scores or {}).get("rubric_version") == "reply-score-v3.0" and all(
            row["score"] or row.get("review_note") for row in rows
        ):
            status = "pending-review"
        note = read(campaign / name / "run-note.json", {}).get("note")
        return {"id": name, "case": record.get("base_case", case), "variant": record.get("variant"),
                "cohort": record.get("cohort"),
                "catalog_id": record["catalog_id"],
                "language": session["language"], "title": record["title"], "expected": 52,
                "candidate_sha256": record["candidate_sha256"], "status": status, "complete": complete,
                "scoring_version": (scores or {}).get("rubric_version", "reply-score-v1"),
                "official": official, "rows": rows, "summary": summarize(rows, official),
                "interruption": note,
                "note": ("样本口径：本轮未专项改写剧本提示词或控制逻辑；沿用既有公共故事框架，"
                         "使用本轮统一的 Lite 原音链路。不能据此作为从未接受通用改动的原始对照。")
                        if case == "sushi" else None}
    by_id = {session["id"]: session for session in plan["sessions"]}
    sessions = [
        load_session(session, attempts["current"].get(session["id"], session["id"]))
        for session in plan["sessions"]
    ]
    if len({session["id"] for session in sessions}) != len(sessions):
        raise ValueError("Independent tests cannot share an attempt")
    archives = []
    for name in attempts["archives"]:
        original_id = attempts.get("archive_definitions", {}).get(name, name)
        if original_id not in by_id or name in {session["id"] for session in sessions}:
            raise ValueError("Archived attempt must be a distinct original session")
        archived = load_session(by_id[original_id], name)
        archived["title"] += " · 前次中断"
        archived["historical"] = True
        archives.append(archived)
    if include_history:
        baseline = ROOT / "tests/giztest/reports/baseline-figure-su-shi-e2e-20261029"
        if (baseline / "full23/dialogue.json").exists():
            scores = read(baseline / "log-only-v1/scores.json")
            rows = public_rows(read(baseline / "full23/dialogue.json"), scores, historical=True)
            archives.append({"id": "historical-sushi-24", "title": "苏轼 · 原版短测实录", "language": "mixed",
                             "historical": True, "complete": False, "official": False, "expected": 52,
                             "runtime": "0.35.7", "candidate_sha256": (scores or {}).get("source", {}).get("candidate_sha256", ""),
                             "note": "历史短测 24 条回复，其中中文 20 条、英文 4 条。保留逐条日志评分；各语言均不满足本轮 51 轮要求，无正式剧本分。",
                             "rows": rows, "summary": summarize(rows, False)})
    data = {"schema": "raids-public-report/v1", "updated_at": datetime.now(timezone.utc).isoformat(),
            "campaign": campaign.name, "runtime": plan["runtime"][0]["version"], "catalog": catalog,
            "samples": samples, "sessions": sessions, "archives": archives,
            "scoring": {"source": "Codex reads actual logs", "weights": WEIGHTS,
                        "versions": sorted({s["scoring_version"] for s in sessions}),
                        "aggregation": "min(weighted_dimension_total, impact_cap)",
                        "v2_aggregation": "min(weighted_dimension_total, impact_cap)",
                        "minimum_user_turns": 51, "required_replies": 52, "outcome_policy": "scores_only"}}
    # The campaign writes these already-safe summaries after local review.
    for name, key in (("calibration-public.json", "calibration"), ("comparison-public.json", "comparison")):
        value = read(campaign / "v3-rescore" / name)
        if value is not None:
            data["scoring"][key] = value
    collection_review = read(campaign / "collection-review-public.json", {})
    if isinstance(collection_review.get("notice"), str):
        data["collection_notice"] = collection_review["notice"]
    output.mkdir(parents=True, exist_ok=True)
    for name in ("index.html", "report.css", "report.js"):
        shutil.copyfile(ROOT / "web/reports" / name, output / name)
    write_logs(data, output)
    html = (output / "index.html").read_text()
    for name in ("report.css", "report.js"):
        version = hashlib.sha256((output / name).read_bytes()).hexdigest()[:12]
        html = html.replace('"' + name + '"', '"' + name + "?v=" + version + '"')
    stable_data = {key: value for key, value in data.items() if key != "updated_at"}
    data_version = hashlib.sha256(json.dumps(stable_data, sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:12]
    html = html.replace('"report-data.js"', '"report-data.js?v=' + data_version + '"')
    (output / "index.html").write_text(html)
    readme = (ROOT / "README.md").read_text()
    section = readme.split('<a id="reply-scoring-v1"></a>', 1)[1].split("\n## Catalog behavior notes", 1)[0]
    (output / "scoring.md").write_text(section.strip() + "\n")
    text = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    (output / "report.json").write_text(text + "\n")
    (output / "report-data.js").write_text("window.RAIDS_REPORT=" + text.replace("<", "\\u003c") + ";\n")
    (output / ".nojekyll").touch()
    print(json.dumps({"catalog": len(catalog), "sessions": len(sessions),
                      "new_replies": sum(len(s["rows"]) for s in sessions),
                      "official_grades": sum(s["official"] for s in sessions), "output": str(output)}, ensure_ascii=False))
    return data


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--campaign", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--no-history", action="store_true")
    args = parser.parse_args()
    build(args.campaign.resolve(), args.out.resolve(), not args.no_history)
