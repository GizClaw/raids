"""Content scores from retained dialogue. This never edits host output or old verdicts."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import time
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[2]
RUBRIC = ROOT / "tests/giztest/judges/reply-score-v1.4.json"


def strict_json(value):
    """Reject bad JSON, duplicate keys and nonfinite numbers; never repair text."""
    def object_pairs(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("Duplicate JSON key")
            result[key] = value
        return result

    def constant(_):
        raise ValueError("Nonfinite JSON number")

    return json.loads(value, object_pairs_hook=object_pairs, parse_constant=constant)


def read(path):
    return strict_json(Path(path).read_text())


def write_new(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def compact(value):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def reference_catalog(batch, target):
    refs = [f"r{turn['i']}" for turn in batch["turns"] if turn["i"] <= target]
    refs.extend(item["id"] for item in batch["independent_evidence"])
    refs.extend(item["id"] for item in batch["function_events"] if item.get("round", target) <= target)
    if len(refs) != len(set(refs)):
        raise ValueError("Ambiguous reference identifiers")
    return refs


def content_turn(turn):
    """Original synthesized words are the content source; ASR is diagnostic only."""
    return {key: value for key, value in turn.items() if key != "asr"}


def prepare(case, output, rubric_path=RUBRIC):
    """Input includes actual answers, not the host prompt or an expected story."""
    directory = Path(case["directory"]).resolve()
    dialogue = read(directory / "dialogue.json")
    audit = read(directory / "audit.json")
    numbers = [row["round"] for row in dialogue]
    if numbers != list(range(len(dialogue))):
        raise ValueError("Dialogue must be complete and ordered from round zero")
    turns = [{"i": row["round"], "intended": row["intended"],
              "asr": row["heard"], "reply": row["raw_history"]}
             for row in dialogue]
    value = {
        "rubric_version": read(rubric_path)["version"],
        "rubric_sha256": digest(rubric_path),
        "category": case["category"], "name": case["name"],
        "contract": case["contract"], "turns": turns,
        "independent_evidence": case.get("independent_evidence", []),
        "function_events": case.get("function_events", []),
        "source": {
            "directory": str(directory),
            "dialogue_sha256": digest(directory / "dialogue.json"),
            "audit_sha256": digest(directory / "audit.json"),
            "candidate_sha256": audit["candidate_sha256"],
            "technical_status": audit["technical_status"],
            "old_automatic_content_opinion": audit["automatic_content_opinion"],
            "expected_replies": audit["expected_host_replies"],
        },
    }
    write_new(output, value)
    return value


def request_body(batch, model, rubric_path=RUBRIC, *, thinking="disabled"):
    rubric = read(rubric_path)
    if thinking not in ("enabled", "disabled"):
        raise ValueError("Thinking must be explicitly enabled or disabled")
    if batch["rubric_sha256"] != digest(rubric_path):
        raise ValueError("Rubric changed after preparation")
    target = batch.get("target_i")
    if type(target) is not int or target not in [turn["i"] for turn in batch["turns"]]:
        raise ValueError("One existing target_i is required; bulk generation is not supported")
    system = rubric["system_policy"] + "\n约定：" + batch["contract"]
    # The complete record grammar is in the policy. No provider-generated JSON
    # or Tool schema is needed; the application serializes validated data.
    static_chars = len(system) + 17
    if static_chars > 1000:
        raise ValueError(f"Expanded static judge context {static_chars} > 1000")
    data = {"category": batch["category"], "target_i": target,
            "history": [content_turn(turn) for turn in batch["turns"] if turn["i"] < target],
            "independent_evidence": batch["independent_evidence"],
            "function_events": [event for event in batch["function_events"]
                                if event.get("round", target) <= target],
            "refs": reference_catalog(batch, target),
            "current_turn": content_turn(next(turn for turn in batch["turns"] if turn["i"] == target))}
    body = {"model": model, "stream": False, "thinking": {"type": thinking},
            "temperature": 0, "max_tokens": 16384 if thinking == "enabled" else 8192,
            "messages": [{"role": "system", "content": system},
                         {"role": "user", "content": compact(data)}]}
    return body, static_chars


def validate(opinion, batch, rubric_path=RUBRIC):
    """Validate numeric/provenance structure, never factual strings or expected prose."""
    rubric = read(rubric_path)
    if batch["rubric_sha256"] != digest(rubric_path):
        raise ValueError("Rubric changed; do not rescore with different weights silently")
    if not isinstance(opinion, dict) or set(opinion) != {"rows"} or not isinstance(opinion["rows"], list):
        raise ValueError("Expected native score rows object")
    turns = [r["i"] for r in batch["turns"]]
    if "target_i" in batch:
        if type(batch["target_i"]) is not int or batch["target_i"] not in turns:
            raise ValueError("Unknown target round")
        expected = [batch["target_i"]]
    else:
        expected = turns
    indices = [r.get("i") for r in opinion["rows"] if isinstance(r, dict)]
    if len(indices) != len(expected) or any(type(i) is not int for i in indices) or sorted(indices) != expected:
        raise ValueError("Missing, duplicate or foreign round; no padding or reply selection")
    external_ids = {e["id"] for e in batch["independent_evidence"]}
    rows = []
    for row in sorted(opinion["rows"], key=lambda r: r["i"]):
        if set(row) != {"i", "s", "why", "block", "evidence"}:
            raise ValueError("Unexpected score fields")
        scores = row["s"]
        if not isinstance(scores, list) or len(scores) != len(rubric["dimensions"]) or any(
                type(score) is not int or not 0 <= score <= 5 for score in scores):
            raise ValueError("Exactly five integer ratings between zero and five required")
        if type(row["block"]) is not bool or not isinstance(row["why"], str):
            raise ValueError("Invalid blocker or explanation")
        refs = row["evidence"]
        if not isinstance(refs, list) or any(not isinstance(ref, str) for ref in refs):
            raise ValueError("Evidence must be reference IDs")
        event_ids = {e["id"] for e in batch["function_events"] if e.get("round", row["i"]) <= row["i"]}
        available = {f"r{i}" for i in turns if i <= row["i"]} | external_ids | event_ids
        if any(ref not in available for ref in refs):
            raise ValueError("Unknown or future-turn evidence")
        if (min(scores) < 4 or row["block"]) and (not refs or not row["why"].strip()):
            raise ValueError("Material deductions or blocker need explicit evidence and impact")
        if min(scores) < 5 and not row["why"].strip():
            raise ValueError("Every deduction needs an explanation")
        points = [d["weight"] * score / 5 for d, score in zip(rubric["dimensions"], scores)]
        rows.append({**row, "points": dict(zip((d["id"] for d in rubric["dimensions"]), points)),
                     "total": sum(points)})
    return rows


def validate_turn(opinion, batch, rubric_path=RUBRIC):
    if "target_i" not in batch:
        raise ValueError("A per-reply score needs its target identity")
    return validate({"rows": [opinion]}, batch, rubric_path)[0]


def indexed_score(opinion, batch, rubric_path=RUBRIC):
    """Resolve validated foreign keys, not loose citation text or model prose."""
    if not isinstance(opinion, dict) or not isinstance(opinion.get("evidence"), list):
        raise ValueError("Expected a typed structured score object")
    refs = reference_catalog(batch, batch["target_i"])
    indices = opinion["evidence"]
    if any(type(i) is not int or i < 0 or i >= len(refs) for i in indices):
        raise ValueError("Evidence reference index is not present in the supplied catalog")
    resolved = {**opinion, "evidence": [refs[i] for i in indices]}
    row = validate_turn(resolved, batch, rubric_path)
    row["evidence_indexes"] = indices
    return row


def parse_score_record(text, batch, rubric_path=RUBRIC):
    """One explicit primary grammar, with no JSON repair or alternate formats."""
    if not isinstance(text, str):
        raise ValueError("Expected the complete evaluator text")
    if text.count("S|") != 1:
        raise ValueError("One unambiguous terminal score delimiter is required")
    why, delimiter, payload = text.rstrip("\r\n").partition("S|")
    if not why.strip():
        raise ValueError("A score must retain its rationale")
    terminal = delimiter + payload
    fields = terminal.split("|")
    if len(fields) != 7 or fields[0] != "S":
        raise ValueError("Expected exactly five ratings and one block marker")
    if any(value not in ("0", "1", "2", "3", "4", "5") for value in fields[1:6]):
        raise ValueError("Score record needs five single-digit ratings between zero and five")
    if fields[6] not in ("0", "1"):
        raise ValueError("Block marker must be zero or one")
    opinion = {"i": batch["target_i"], "s": [int(x) for x in fields[1:6]],
               "why": why, "block": fields[6] == "1", "evidence": [f"r{batch['target_i']}"]}
    row = validate_turn(opinion, batch, rubric_path)
    row['evidence_binding'] = 'Application-owned target/context locator; model evidence remains in rationale, not claimed as independently verified counterproof'
    row['context_sha256'] = hashlib.sha256(compact({
        'target_i': batch['target_i'], 'turns': [t for t in batch['turns'] if t['i'] <= batch['target_i']],
        'independent_evidence': batch['independent_evidence'],
        'function_events': [e for e in batch['function_events'] if e.get('round', batch['target_i']) <= batch['target_i']]
    }).encode()).hexdigest()
    return row


def provider_score(value, batch, rubric_path=RUBRIC):
    """Provider owns the outer API response; application owns the score JSON."""
    choices = value.get("choices", [])
    if len(choices) != 1 or choices[0].get("finish_reason") != "stop":
        raise ValueError("Expected a complete evaluator response")
    message = choices[0]["message"]
    if message.get("refusal") or message.get("tool_calls"):
        raise ValueError("The score-record protocol has no refusal or ToolCall fallback")
    return parse_score_record(message.get("content"), batch, rubric_path)


def decode_provider_response(raw):
    """Decode API transport only, retaining every model content delta verbatim."""
    text = raw.decode("utf-8") if isinstance(raw, bytes) else raw
    if text.lstrip().startswith("{"):
        return strict_json(text)
    content, finish = [], None
    ended = False
    for line in text.splitlines():
        if not line.startswith("data:"):
            continue
        payload = line[5:].strip()
        if not payload:
            continue
        if payload == "[DONE]":
            ended = True
            continue
        if ended:
            raise ValueError("Provider data appeared after stream completion")
        event = strict_json(payload)
        choices = event.get("choices", [])
        if len(choices) > 1:
            raise ValueError("Multiple provider choices are not one score")
        for choice in choices:
            if choice.get("index", 0) != 0:
                raise ValueError("Unexpected provider choice index")
            delta = choice.get("delta", {})
            if delta.get("tool_calls") or delta.get("refusal"):
                raise ValueError("Score-record stream must not fall back to a ToolCall or refusal")
            value = delta.get("content")
            if value is not None:
                if not isinstance(value, str):
                    raise ValueError("Unexpected provider content type")
                content.append(value)
            reason = choice.get("finish_reason")
            if reason is not None:
                if finish is not None:
                    raise ValueError("Duplicate provider completion")
                finish = reason
    if not ended or finish != "stop":
        raise ValueError("Provider stream did not finish completely")
    return {"choices": [{"finish_reason": finish, "message": {"content": "".join(content)}}]}


def summarize(rows, expected_replies, technical_status, rubric_path=RUBRIC):
    rubric = read(rubric_path)
    indices = [r["i"] for r in rows]
    complete = indices == list(range(expected_replies))
    average = sum(r["total"] for r in rows) / len(rows) if rows else None
    sensitivity = {}
    for threshold in rubric["proposed_thresholds"]:
        passing = sum(r["total"] >= threshold for r in rows)
        required = math.ceil(expected_replies * rubric["minimum_turn_pass_fraction"])
        # Automatic blocker allegations remain allegations until Root checks them.
        accepted = bool(complete and average >= threshold and passing >= required and
                        not any(r["block"] for r in rows))
        sensitivity[str(threshold)] = {
            "mean_reaches_line": bool(average is not None and average >= threshold),
            "replies_at_or_above": passing, "required_replies": required,
            "content_provisionally_accepted": accepted,
            "technical_separately_passed": technical_status == "PASS",
            "provisionally_accepted_with_technical": accepted and technical_status == "PASS",
        }
    return {"replies": len(rows), "expected_replies": expected_replies, "complete": complete,
            "mean": round(average, 2) if average is not None else None,
            "minimum": min((r["total"] for r in rows), default=None),
            "dimension_means": {d["id"]: round(sum(r["points"][d["id"]] for r in rows) / len(rows), 2)
                                for d in rubric["dimensions"]} if rows else {},
            "blocker_allegation_rounds": [r["i"] for r in rows if r["block"]],
            "threshold_comparison": sensitivity,
            "technical_status": technical_status, "thresholds_are_proposed": True}


def evaluate(input_path, output_dir, endpoint, model, key_file, target_i, thinking="disabled"):
    """One credential-free recorded request; no retries, E2E sessions or shared mutations."""
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    batch = read(input_path)
    batch = {**batch, "target_i": target_i}
    body, static_chars = request_body(batch, model, thinking=thinking)
    write_new(output / "attempt.once.json", {"pid": os.getpid(), "input_sha256": digest(input_path), "target_i": target_i,
              "started_at_utc": datetime.now(timezone.utc).isoformat(), "no_retries": True})
    write_new(output / "request.json", body)
    key = Path(key_file).read_text().strip()
    if not key:
        raise ValueError("Empty API credential")
    request = urllib.request.Request(endpoint.rstrip("/") + "/chat/completions",
        data=compact(body).encode(), headers={"Content-Type": "application/json", "Authorization": "Bearer " + key})
    start = time.monotonic()
    try:
        with urllib.request.urlopen(request, timeout=240) as response:
            raw = response.read()
        (output / "response.raw.json").write_bytes(raw)
        value = strict_json(raw)
        rows = [provider_score(value, batch)]
        result = {"evaluator": "Pro automatic opinion, not independently verified factual truth",
                  "model": model, "thinking": thinking, "static_context_chars": static_chars,
                  "input_sha256": digest(input_path), "rubric_sha256": digest(RUBRIC),
                  "request_sha256": digest(output / "request.json"),
                  "response_sha256": digest(output / "response.raw.json"),
                  "duration_seconds": round(time.monotonic() - start, 3), "usage": value.get("usage"),
                  "rows": rows, "summary": summarize(rows, batch["source"]["expected_replies"],
                                                      batch["source"]["technical_status"])}
        write_new(output / "scores.json", result)
        return result
    except Exception as error:
        # Never echo provider responses, auth headers or credentials in an exception.
        status = error.code if isinstance(error, urllib.error.HTTPError) else None
        write_new(output / "failed.json", {"status": "INCOMPLETE", "error_type": type(error).__name__,
                  "http_status": status, "no_retry": True})
        raise RuntimeError(f"Judge incomplete ({type(error).__name__}, HTTP {status}); evidence retained") from None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    p = commands.add_parser("prepare")
    p.add_argument("--manifest", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    p = commands.add_parser("evaluate")
    p.add_argument("--input", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--endpoint", required=True)
    p.add_argument("--model", default="doubao-seed-2-1-pro-260915")
    p.add_argument("--api-key-file", type=Path, required=True)
    p.add_argument("--round", type=int, required=True)
    p.add_argument("--thinking", choices=["enabled", "disabled"], default="disabled")
    p = commands.add_parser("summarize")
    p.add_argument("--input", type=Path, required=True)
    p.add_argument("--opinion", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "prepare":
        for case in read(args.manifest)["cases"]:
            prepare(case, args.out / (case["category"] + ".json"))
    elif args.command == "evaluate":
        value = evaluate(args.input, args.out, args.endpoint, args.model, args.api_key_file, args.round, args.thinking)
        print(compact({"target_i": args.round, "score": value["rows"][0], "script_summary": value["summary"]}))
    else:
        batch = read(args.input)
        rows = validate(read(args.opinion), batch)
        print(json.dumps(summarize(rows, batch["source"]["expected_replies"],
                                   batch["source"]["technical_status"]), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
