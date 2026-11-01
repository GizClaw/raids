#!/usr/bin/env python3
"""Regenerate figure-* raid packages from workflows/<raid>/figure.json and cards/figure/<人物>.txt."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any

import evidence

sys.dont_write_bytecode = True

HERE = Path(__file__).resolve().parent
TEMPLATES = HERE / "templates"
MAX_ALIAS = 63  # GizClaw runtime aliases, e.g. eino-<raid>-mr.<role>
TIERS = ("smoke", "quality", "soak", "device")
VARIANT = "eino.multi-role"  # the only implementation: file stem and Giztest suffix
IMPLEMENTATION = "eino-multi-role"  # its key in raid.json
CHAPTERS = (1, 2, 3, 4)
KEY = re.compile(r"[a-z]+(?:-[a-z]+)*")
# Figure text lands inside JS and Starlark string literals and Eino f_string
# templates, so it must not carry quotes, backslashes, braces or line breaks.
UNSAFE = re.compile(r"[\"'\\{}\n\r`]|@@")

ROLE_VIEW_HEAD = "当前角色资料：narrator 旁白，第1至4章只述可见事实、不代演角色；"
ROLE_VIEW_TAIL = ("\n本故事四章、人物相遇和章内行动是本仓库基于史料的原创改编安排，不等同史书记载；"
                  "所有角色只知亲历或已公开信息，不知别人的私密想法和未来结果；每章比较至少两种立场，不要求全员轮流发言。")
NARRATOR = {"key": "narrator", "name": "旁白", "aliases": ["旁白", "narrator"], "chapters": list(CHAPTERS)}
PRONOUNS = {
    "male": {"zh": "他", "subject": "he", "object": "him", "possessive": "his", "reflexive": "himself"},
    "female": {"zh": "她", "subject": "she", "object": "her", "possessive": "her", "reflexive": "herself"},
}


def repository_root() -> Path:
    return HERE.parents[1]


def discover_raids(repo: Path) -> list[str]:
    return sorted(path.parent.name for path in (repo / "workflows").glob("figure-*/figure.json"))


# A knowledge card describes the person, not the raid: one “字段：值” line per
# field in cards/figure/_template.txt order. The whole card is embedded in the
# prompt as the factual reference; list fields separate items with “；”.
CARDS = ("cards", "figure")
NONE = "无"


def card_fields(repo: Path) -> list[str]:
    path = repo.joinpath(*CARDS, "_template.txt")
    return [line.partition("：")[0].strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def read_card(repo: Path, name: str) -> dict[str, str]:
    path = repo.joinpath(*CARDS, f"{name}.txt")
    if not path.is_file():
        raise ValueError(f"missing knowledge card {path.relative_to(repo)}")
    values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        key, sep, value = line.partition("：")
        key, value = key.strip(), value.strip()
        if not sep or not key or not value:
            raise ValueError(f"{path}: “{line}” must be a non-empty “字段：值” line")
        check_text(f"{path}: {key}", value)
        if "|" in value:
            raise ValueError(f"{path}: {key} must not contain |")
        if key in values:
            raise ValueError(f"{path}: {key} appears twice")
        values[key] = value
    if list(values) != card_fields(repo):
        raise ValueError(f"{path}: fields must be exactly {'、'.join(card_fields(repo))} in this order")
    if values["人物"] != name:
        raise ValueError(f"{path}: 人物 must be {name}")
    return values


def birth_fact(card: dict[str, str]) -> str:
    """The birth years (or reign years) the card's 时代 gives, for the quality reviewer."""
    era = card["时代"]
    years = [m.group(0) for m in re.finditer(r"前?\d{3,4}年", era)
             if not re.search(r"(?:—|卒于|卒年)约?$", era[:m.start()])]
    years += re.findall(r"[\u4e00-\u9fff]{2}[一二三四五六七八九十元]+年", era)
    if not years:
        raise ValueError(f"时代 {era} names no birth year")
    return "、".join(dict.fromkeys(years)) + ("（生年不详，只是一说）" if "不详" in era else "")


def card_legends(card: dict[str, str]) -> list[str]:
    """Legend names, the part of each 后人传说 item before “——”."""
    names = [item.partition("——")[0].strip() for item in card["后人传说"].split("；") if item.strip()]
    if not names or any(not name for name in names):
        raise ValueError("后人传说 must list items as “名称——说明”")
    return names


def template(name: str) -> str:
    return (TEMPLATES / name).read_text(encoding="utf-8")


def fill(text: str, values: dict[str, str]) -> str:
    for key, value in values.items():
        text = text.replace(f"@@{key}@@", value)
    if "@@" in text:
        start = text.index("@@")
        raise ValueError(f"unfilled template placeholder near: {text[start:start + 40]!r}")
    return text


def cast(data: dict[str, Any]) -> list[dict[str, Any]]:
    """Speaking roles in voice order: the figure, the companion, then the guests."""
    return [data["figure"], data["companion"], *data["guests"]]


def role_chapters(role: dict[str, Any]) -> list[int]:
    return role.get("chapters", list(CHAPTERS))


def roles_in(data: dict[str, Any], chapter: int) -> list[str]:
    return [NARRATOR["key"]] + [role["key"] for role in cast(data) if chapter in role_chapters(role)]


def check_text(where: str, value: Any) -> None:
    if not isinstance(value, str) or not value.strip() or UNSAFE.search(value):
        raise ValueError(f"{where} must be non-empty text without quotes, backslashes, braces, backticks or line breaks")


def load(repo: Path, raid: str) -> dict[str, Any]:
    path = repo / "workflows" / raid / "figure.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("id") != raid:
        raise ValueError(f"{path}: id must be {raid}")
    figure, companion, guests = data["figure"], data["companion"], data["guests"]
    if raid != f"figure-{figure['key']}":
        raise ValueError(f"{path}: raid ID must be figure-<figure.key>")
    if figure.get("gender") not in PRONOUNS:
        raise ValueError(f"{path}: figure.gender must be one of {', '.join(PRONOUNS)}")
    if len(data["chapters"]) != len(CHAPTERS):
        raise ValueError(f"{path}: a figure raid tells a life in exactly {len(CHAPTERS)} chapters")
    if len(guests) != 2:
        raise ValueError(f"{path}: the multi-role cast adds exactly two guests")
    for field in ("key", "name", "name_en", "aliases", "views"):
        if field not in figure:
            raise ValueError(f"{path}: figure lacks {field}")
    for field in ("chapters",):
        if field in figure or field in companion:
            raise ValueError(f"{path}: the figure and the companion appear in every chapter; drop {field}")
    keys: set[str] = {NARRATOR["key"]}
    names: set[str] = {NARRATOR["name"]}
    for role in cast(data):
        where = f"{path}: role {role.get('key')}"
        if not KEY.fullmatch(role["key"]) or role["key"] in keys:
            raise ValueError(f"{where}: key must be unique lowercase words joined by hyphens")
        check_text(f"{where} name", role["name"])
        if role["name"] in names:
            raise ValueError(f"{where}: name {role['name']} is used twice")
        keys.add(role["key"])
        names.add(role["name"])
        if role["aliases"][0] != role["name"] or role["key"] not in role["aliases"]:
            raise ValueError(f"{where}: aliases must start with the name and include the key")
        for alias in role["aliases"]:
            check_text(f"{where} alias", alias)
        chapters = role_chapters(role)
        if chapters != sorted(set(chapters)) or not set(chapters) <= set(CHAPTERS):
            raise ValueError(f"{where}: chapters must be ascending chapter numbers")
        if len(role["views"]) != len(chapters):
            raise ValueError(f"{where}: needs one view for each of its chapters {chapters}")
        for view in role["views"]:
            for field in ("want", "temper", "action"):
                check_text(f"{where} view {field}", view[field])
        alias = f"eino-{raid}-mr.{role['key']}"
        if len(alias.encode("utf-8")) > MAX_ALIAS:
            raise ValueError(f"{where}: Voice alias {alias} exceeds {MAX_ALIAS} bytes")
    for guest in guests:
        if 1 in role_chapters(guest):
            raise ValueError(f"{path}: guest {guest['key']} must arrive after chapter 1; the companion is the chapter 1 partner")
    if len(f"eino-{raid}-multi-role".encode("utf-8")) > MAX_ALIAS:
        raise ValueError(f"{path}: raid ID is too long for its multi-role Workflow ID")
    for number, chapter in enumerate(data["chapters"], 1):
        check_text(f"{path}: chapter {number} title", chapter["title"])
    titles = [chapter["title"] for chapter in data["chapters"]]
    if len(set(titles)) != len(titles):
        raise ValueError(f"{path}: chapter titles must differ")
    for field in ("premise", "free_talk.topics", "free_talk.question", "opening.intro", "opening.guests",
                  "opening.question", "opening.choice", "title.zh-CN"):
        section, _, key = field.partition(".")
        check_text(f"{path}: {field}", data[section][key] if key else data[section])
    if data["opening"]["choice"] not in data["opening"]["question"]:
        raise ValueError(f"{path}: opening.choice must be one of the options named in opening.question")
    if not data["opening"]["intro"].startswith(f"我是{figure['name']}") or companion["name"] not in data["opening"]["intro"]:
        raise ValueError(f"{path}: opening.intro must start with 我是{figure['name']} and introduce {companion['name']}")
    for guest in guests:
        if guest["name"] not in data["opening"]["guests"]:
            raise ValueError(f"{path}: opening.guests must announce {guest['name']}")
    if "legends" in data:
        raise ValueError(f"{path}: legends belong in the knowledge card's 后人传说, not in figure.json")
    if "narration" in data:
        narration = data["narration"]
        if (set(narration) - {"mode", "search"} or narration.get("mode") != "compact"
                or ("search" in narration and not isinstance(narration["search"], bool))):
            raise ValueError(f"{path}: narration must declare mode compact; source units come from the complete card")
    card = read_card(repo, figure["name"])
    for role in (companion, *guests):
        if role["name"] not in card["身边的人"]:
            raise ValueError(f"cards/figure/{figure['name']}.txt: 身边的人 must describe {role['name']}")
    data["card"] = card
    data["legends"] = card_legends(card)
    return data


def view_line(role: dict[str, Any], chapter: int) -> str:
    chapters = role_chapters(role)
    view = role["views"][chapters.index(chapter)]
    end = "。" if chapter == CHAPTERS[-1] else "，"
    return (f"{role['key']} {role['name']}，仅第{'、'.join(str(n) for n in chapters)}章可出场，{view['want']}；"
            f"{view['temper']}，第{chapter}章{view['action']}{end}")


def role_views(data: dict[str, Any]) -> list[str]:
    return [ROLE_VIEW_HEAD + "；".join(view_line(role, n) for role in cast(data) if n in role_chapters(role)) + ROLE_VIEW_TAIL
            for n in CHAPTERS]


def role_table(data: dict[str, Any]) -> str:
    rows = [NARRATOR] + [{"key": r["key"], "name": r["name"], "aliases": r["aliases"], "chapters": role_chapters(r)}
                         for r in cast(data)]
    return json.dumps(rows, ensure_ascii=False, separators=(",", ":"))


def starlark_role_aliases(data: dict[str, Any]) -> str:
    return repr([(NARRATOR["key"], NARRATOR["aliases"])] + [(role["key"], role["aliases"]) for role in cast(data)])


def english_list(items: list[str]) -> str:
    return items[0] if len(items) == 1 else ", ".join(items[:-1]) + " and " + items[-1]


def english_chapters(chapters: list[int]) -> str:
    if len(chapters) == 1:
        return f"chapter {chapters[0]} only"
    if chapters[-1] == CHAPTERS[-1] and chapters == list(range(chapters[0], CHAPTERS[-1] + 1)):
        return f"chapter {chapters[0]} onward"
    return "chapters " + english_list([str(n) for n in chapters])


def chinese_chapters(role: dict[str, Any]) -> str:
    chapters = role_chapters(role)
    if len(chapters) == 1:
        return f"{role['name']}仅第{chapters[0]}章"
    if chapters == list(range(chapters[0], CHAPTERS[-1] + 1)):
        return f"{role['name']}第{chapters[0]}章起"
    return f"{role['name']}第{'、'.join(str(n) for n in chapters)}章"


def values(raid: str, data: dict[str, Any]) -> dict[str, str]:
    figure, companion, (guest1, guest2) = data["figure"], data["companion"], data["guests"]
    pronoun = PRONOUNS[figure["gender"]]
    out = {
        # Composite values first: fill() substitutes in this order.
        "ROLE_VIEWS": json.dumps(role_views(data), ensure_ascii=False),
        "ROLE_TABLE": role_table(data),
        "ROLE_ALIASES": starlark_role_aliases(data),
        "OPENING_INTRO": data["opening"]["intro"],
        "OPENING_GUESTS": data["opening"]["guests"],
        "OPENING_QUESTION": data["opening"]["question"],
        "OPENING_CHOICE": data["opening"]["choice"],
        "PREMISE": data["premise"],
        "LEGENDS": "、".join(data["legends"]),
        "FREE_TALK_TOPICS": data["free_talk"]["topics"],
        "RAID": raid,
        "TITLE": data["title"]["zh-CN"],
        "GUEST_CHAPTERS": "、".join(chinese_chapters(guest) for guest in data["guests"]),
    }
    for number, chapter in enumerate(data["chapters"], 1):
        out[f"CH{number}"] = chapter["title"]
    for slot, role in (("FIGURE", figure), ("COMPANION", companion), ("GUEST1", guest1), ("GUEST2", guest2)):
        out[slot] = role["name"]
        out[f"{slot}_KEY"] = role["key"]
        out[f"{slot}_VAR"] = role["key"].replace("-", "_")
    out["FIGURE_EN"] = figure["name_en"]
    out["PRONOUN"] = pronoun["zh"]
    # Quality probes: the birth year the card gives, and its first later legend.
    out["BIRTH_FACT"] = birth_fact(data["card"])
    out["LEGEND_NAME"] = data["legends"][0].strip("“”")
    out["LEGEND_QUESTION"] = "“" + out["LEGEND_NAME"] + "”"
    # The card sits inside a YAML block scalar indented by twelve spaces.
    out["KNOWLEDGE_CARD"] = "\n            ".join(f"{key}：{value}" for key, value in data["card"].items())
    return out


def render_readme(raid: str, data: dict[str, Any], slots: dict[str, str]) -> str:
    figure, companion, guests = data["figure"], data["companion"], data["guests"]
    pronoun = PRONOUNS[figure["gender"]]
    if "narration" in data:
        return fill(template("README.compact.md"), {
            **slots,
            "TITLE_EN": data["title"]["en"],
            "SUMMARY_EN": data["summary"]["en"],
            "CHAPTER_CHAIN": " → ".join(c["title"] for c in data["chapters"]),
        })
    rows = []
    for number, chapter in enumerate(data["chapters"], 1):
        entry = "first opening request" if number == 1 else f"chapter {number - 1} transition satisfied and player explicitly continues"
        if number < len(CHAPTERS):
            transition = f"player resolves the current hook and requests chapter {number + 1}"
            ending = f"emit the chapter {number + 1} heading once, followed directly by that chapter's opening scene"
        else:
            transition = "player confirms a durable choice and one remaining responsibility"
            ending = "speak the closing line once, then hand the raid over to free conversation"
        rows.append(f"| {number}. {chapter['title']} | {entry} | {chapter['goal']} | observe a concrete consequence; "
                    f"compare the characters present | {transition} | {ending} |")
    guest_text = " and ".join(f"{g['name']} (`{g['key']}`, {english_chapters(g['chapters'])})" for g in guests)
    legends = english_list(data["legends"])
    return fill(template("README.md"), {
        **slots,
        "TITLE_EN": data["title"]["en"],
        "SUMMARY_EN": data["summary"]["en"],
        "CHAPTER_ROWS": "\n".join(rows),
        "CHAPTER_CHAIN": " → ".join(f"第{n}章《{c['title']}》" for n, c in enumerate(data["chapters"], 1)),
        "CAST": (f"narrator (visible facts and transitions), {figure['name']} (`{figure['key']}`, the subject, speaking as “我”), "
                 f"and {pronoun['possessive']} {companion['relation_en']} {companion['name']} (`{companion['key']}`). "
                 f"The multi-role variants add {guest_text}, matching when they entered {pronoun['possessive']} life."),
        "BOUNDARY": (f"{figure['name']} only knows {pronoun['possessive']} own era — asked about anything later, "
                     f"{pronoun['subject']} says so in character and steers back. {legends} must be told as later legend, "
                     f"not as something {pronoun['subject']} lived."),
        "REFLEXIVE": pronoun["reflexive"],
        "HARDSHIP": data["hardship_en"],
        "MR_ALIASES_EINO": ", ".join(f"`eino-{raid}-mr.{key}`" for key in ["storyteller"] + [r["key"] for r in cast(data)]),
    })


def substitute(value: Any, slots: dict[str, Any]) -> Any:
    """Fill a parsed JSON template; a string that is exactly one placeholder takes the slot's type."""
    if isinstance(value, dict):
        return {substitute(k, slots): substitute(v, slots) for k, v in value.items()}
    if isinstance(value, list):
        return [substitute(item, slots) for item in value]
    if isinstance(value, str):
        whole = re.fullmatch(r"@@([A-Z0-9_]+)@@", value)
        if whole and not isinstance(slots[whole.group(1)], str):
            return slots[whole.group(1)]
        return fill(value, {k: v if isinstance(v, str) else str(v) for k, v in slots.items() if isinstance(v, (str, int))})
    return value


def render_routing(raid: str, data: dict[str, Any], slots: dict[str, str]) -> str:
    typed: dict[str, Any] = dict(slots)
    typed["FREE_TALK_QUESTION"] = data["free_talk"]["question"]
    for number in CHAPTERS:
        typed[f"ROLES_{number}"] = roles_in(data, number)
    for index, guest in enumerate(data["guests"], 1):
        first = role_chapters(guest)[0]
        typed[f"GUEST{index}_FIRST"] = first
        typed[f"GUEST{index}_FIRST_HEADING"] = f"第 {first} 章：{data['chapters'][first - 1]['title']}"
    cases = substitute(json.loads(template("routing-cases.json")), typed)
    return json.dumps(cases, ensure_ascii=False, indent=2) + "\n"


def raid_manifest(raid: str, data: dict[str, Any]) -> str:
    llm = "Chat model that generates every turn; needs streaming Chinese output"
    alias = f"eino-{raid}-mr"
    voices = {f"{alias}.storyteller": {"role": "storyteller", "language": "zh-CN", "description": "旁白：连续剧本段落音色"}}
    voice_roles = [data["figure"]] if data.get("narration", {}).get("mode") == "compact" else cast(data)
    for role in voice_roles:
        voices[f"{alias}.{role['key']}"] = {"role": role["key"], "language": "zh-CN",
                                            "description": f"{role['name']}：连续剧本段落音色"}
    manifest = {
        "schema": "raids.raid/v1alpha1",
        "id": raid,
        "category": "figure",
        "title": data["title"],
        "summary": data["summary"],
        "rating": {"age": data["rating"]["age"], "scheme": "raids-age-v2", "content": data["rating"]["content"]},
        "tags": data["tags"],
        "language": ["zh-CN"],
        # A figure raid ships one implementation: continuous Eino multi-role narration.
        "implementations": {
            IMPLEMENTATION: {
                "file": f"{VARIANT}.yaml",
                "workflow_id": f"eino-{raid}-multi-role",
                "driver": "eino",
                "input": ["text", "realtime"],
                "memory": {"layout_id": "story-teller"},
                "parameters": {
                    "models": {f"{alias}.model": {"kind": "llm", "role": "narrator", "description": llm}},
                    "voices": voices,
                },
            },
        },
        "testers": {
            "multi-role": {
                "file": "test.multi-role.yaml",
                "workflow_id": f"{raid}-test-multi-role",
                "driver": "eino",
                "parameters": {"models": {f"{raid}-test.model": {"kind": "llm", "role": "judge", "description": llm}}},
                "route": {
                    "responses": 16,
                    "checkpoints": [f"response-{n}" for n in range(1, 17)],
                    "milestones": [8, 16],
                    "reload_before": 9,
                    "chapters": [chapter["title"] for chapter in data["chapters"]],
                },
                "implementations": [IMPLEMENTATION],
            },
        },
        "tests": [
            {"file": f"tests/giztest/{tier}/{raid}.{VARIANT}.giztest.yaml", "tier": tier, "implementations": [IMPLEMENTATION]}
            for tier in TIERS[:3]
        ],
    }
    if data.get("narration", {}).get("search"):
        parameters = manifest["implementations"][IMPLEMENTATION]["parameters"]
        parameters["models"][f"{alias}.model"]["description"] = "Stream the interactive story and use Search only for unresolved factual questions"
        manifest["implementations"][IMPLEMENTATION]["parameters"]["tools"] = {
            "reference.search": {"resource_id": "volc-reference-search",
                                 "description": "史实、诗文与出处检索"},
        }
    if data.get("narration", {}).get("mode") == "compact":
        manifest["implementations"][IMPLEMENTATION]["input"] = ["text", "push-to-talk"]
        models = manifest["implementations"][IMPLEMENTATION]["parameters"]["models"]
        models[f"{alias}.model"]["description"] = "Native audio plot narration; function Tool capability disabled"
        models[f"{alias}.intent-model"] = {"kind": "llm", "role": "narrator", "description": "Internal native-audio mode/language schema; no public output or function Tools"}
        models[f"{alias}.research-model"] = {"kind": "llm", "role": "narrator", "description": "Native audio source narrator with Search for uncertain factual questions"}
    return json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"


def render_compact_workflow(data: dict[str, Any], slots: dict[str, str]) -> str:
    repo = repository_root()
    source_units = evidence.units(repo, data)
    source_path = repo / "cards" / "figure" / f"{data['figure']['name']}.txt"
    english_path = source_path.with_suffix(".en.json")
    english = json.loads(english_path.read_text(encoding="utf-8"))
    if set(english) != {"source_sha256", "units"} or english["source_sha256"] != hashlib.sha256(source_path.read_bytes()).hexdigest():
        raise ValueError(f"{english_path}: English units must match the exact Chinese source card")
    for unit in source_units:
        unit["id"] = f"L{unit['line']}.{unit['part']}"
        unit["en"] = english["units"].get(unit["id"])
        if not isinstance(unit["en"], str) or not unit["en"].strip() or any(mark in unit["en"] for mark in ["【", "】", "\n", "\r"]):
            raise ValueError(f"{english_path}: {unit['id']} needs a whole unlabelled English rendering")
    if set(english["units"]) != {unit["id"] for unit in source_units}:
        raise ValueError(f"{english_path}: English units must exactly mirror the whole source-card units")
    scene_path = source_path.with_suffix(".scene.json")
    scene = json.loads(scene_path.read_text(encoding="utf-8"))
    if (set(scene) - {"source_sha256", "source_units", "context", "narrator_units", "actor_context", "actor_frame", "actor_sources"}
            or not {"source_sha256", "source_units", "context"} <= set(scene)
            or scene["source_sha256"] != english["source_sha256"]):
        raise ValueError(f"{scene_path}: scene evidence must match the exact Chinese source card")
    if (not isinstance(scene["source_units"], list) or not scene["source_units"]
            or any(not isinstance(identifier, str) for identifier in scene["source_units"])
            or len(set(scene["source_units"])) != len(scene["source_units"])
            or not set(scene["source_units"]) <= {unit["id"] for unit in source_units}
            or not isinstance(scene["context"], str) or not scene["context"].strip()
            or any(mark in scene["context"] for mark in ["\n", "\r"])):
        raise ValueError(f"{scene_path}: scene context requires complete text and unique valid source IDs")
    narrator_units = scene.get("narrator_units", [])
    if (not isinstance(narrator_units, list)
            or any(not isinstance(identifier, str) for identifier in narrator_units)
            or len(set(narrator_units)) != len(narrator_units)
            or not set(narrator_units) <= {unit["id"] for unit in source_units}):
        raise ValueError(f"{scene_path}: narrator_units requires unique valid source IDs")
    actor_context = scene.get("actor_context", scene["context"])
    actor_frame = scene.get("actor_frame", "晚年" + data["figure"]["name"])
    if any(not isinstance(value, str) or not value.strip() or any(mark in value for mark in ["\n", "\r", "【", "】"])
           for value in (actor_context, actor_frame)):
        raise ValueError(f"{scene_path}: actor context and frame require complete unlabelled text")
    actor_sources = scene.get("actor_sources", [])
    if not isinstance(actor_sources, list) or any(not isinstance(url, str) or not url.startswith("https://") for url in actor_sources):
        raise ValueError(f"{scene_path}: actor_sources requires HTTPS source references")
    for unit in source_units:
        if unit["field"] == "后人传说" or unit["id"] in narrator_units:
            unit["narrator_only"] = True
    english_terms = {unit["id"]: evidence.tokens(unit["en"]) for unit in source_units}
    english_frequencies = Counter(term for terms in english_terms.values() for term in terms)
    for unit in source_units:
        for term in english_terms[unit["id"]]:
            unit["terms"].setdefault(term, max(1, 100 // english_frequencies[term]))
    bootstrap = [index for index, unit in enumerate(source_units)
                 if unit["field"] == "生平" and unit["part"] <= 2]
    fixed_speakers = [NARRATOR["name"], data["figure"]["name"]]
    prompt = fill(template("structured.compact.star"), {
        "FACTS_LITERAL": "[\n" + "\n".join("    " + repr(unit) + "," for unit in source_units) + "\n]",
        "BOOTSTRAP_LITERAL": repr(bootstrap),
        # Query grammar and language-selection words are not source evidence.
        # Keep the source units and their historical text unchanged.
        "IGNORED_WORDS_LITERAL": repr(evidence.IGNORED_WORDS + [
            "a", "an", "to", "of", "in", "is", "it", "on", "for", "do", "does", "did",
            "you", "your", "me", "my", "we", "our", "who", "what", "when", "where", "why", "how",
            "can", "could", "would", "will", "are", "were", "have", "has", "had", "now",
            "please", "switch", "english", "chinese", "continue", "return", "back",
        ]),
        "POLICY_LITERAL": repr(fill(template("instructions.compact.txt"), {**slots, "ACTOR_FRAME": actor_frame})),
        "SCENE_FACTS_LITERAL": repr(scene["context"]),
        "ACTOR_FACTS_LITERAL": repr(actor_context),
        "SCENE_FORMAT_LITERAL": repr("\n声道角色仅" + " ".join("【" + name + "】" for name in fixed_speakers) + "。"),
        "FIGURE_LABELS_LITERAL": repr([data["figure"]["name"], data["figure"]["name_en"]]),
        "HISTORY_CONTEXT_SOURCE": (repo / "scripts/common/history_context.star").read_text(encoding="utf-8"),
    })
    indent = lambda source: "".join(("          " + line if line else "") + "\n" for line in source.splitlines())
    return fill(template("eino.compact.yaml"), {**slots, "PROMPT_SCRIPT": indent(prompt)})


def render_workflow(data: dict[str, Any], slots: dict[str, str]) -> str:
    if "narration" in data:
        return render_compact_workflow(data, slots)
    parts = {
        "NARRATION_STATE": "        - name: narration-context\n          type: string\n          merge: replace\n",
        "NARRATION_CONTROL": template("control-narration.yaml"),
        "NARRATION_INPUT": "          narration_context:\n            from: narration-context\n",
        "NARRATION_NEXT": "control-narration",
        "NARRATION_EDGE": "      - from: control-narration\n        to: build-prompt\n",
        "INSTRUCTIONS": template("instructions.standard.txt"),
        "OBSERVATION_PREFIX": "",
        "OBSERVATION_REPLY": "故事本轮确认：",
        "MAX_RUN_STEPS": "12",
        "NARRATION_MODEL": "model",
        "INITIAL_MODEL_OUTPUTS": "",
        "INITIAL_MODEL_VALUES": "",
        "REFERENCE_LOOP": "",
        "MODEL_EDGE": "      - from: build-prompt\n        to: narrator-model\n",
        "REFERENCE_EDGES": "",
        "REFERENCE_BRANCHES": "",
        "NARRATOR_BRANCH": (
            "      - from: narrator-model\n        mode: first_match\n        routes:\n"
            "        - when:\n            field: memory-route\n            op: eq\n            value: opening\n"
            "          to: end\n        default: capture-observation\n"),
    }
    parts["BUILD_PROMPT"] = fill(template("build-prompt.standard.yaml"), {**parts, **slots})
    return fill(template(f"{VARIANT}.yaml"), {**parts, **slots})


def outputs(raid: str, data: dict[str, Any]) -> dict[str, str]:
    slots = values(raid, data)
    compact = data.get("narration", {}).get("mode") == "compact"
    device_slots = {
        "DEVICE_USER_STORY": (
            "# As a child entering a prompt-led story or adventure on the H106 device,\n"
            "# I want an opening choice, follow-ups that answer my request, and resume/restart cues that preserve or reset progress correctly.\n"
            "# So that replies preserve continuity and text/audio completion without an extra question after every action."
        ) if compact else (
            "# As a child entering a story or adventure on the H106 device,\n"
            "# I want every reply to end with a question, \"继续\" to carry the story on, and \"继续上次的内容\" / \"开始\" to resume or restart,\n"
            "# So that the story never stops in silence after a chapter ends."
        ),
        "DEVICE_FOLLOWUP": "      non_empty: true" if compact else (
            "      min_length: 20\n      pattern: \"[？?][^？?]{0,40}$\""
        ),
    }
    files = {
        f"workflows/{raid}/raid.json": raid_manifest(raid, data),
        f"workflows/{raid}/README.md": render_readme(raid, data, slots),
        f"workflows/{raid}/routing-cases.json": render_routing(raid, data, slots),
        f"workflows/{raid}/test.multi-role.yaml": fill(template("test.multi-role.yaml"), slots),
        f"workflows/{raid}/{VARIANT}.yaml": render_workflow(data, slots),
    }
    if compact:
        files[f"workflows/{raid}/context-cases.json"] = fill(template("context-cases.json"), slots)
    for tier in TIERS:
        document = fill(template(f"{tier}.{VARIANT}.giztest.yaml"), {**slots, **device_slots})
        if compact:
            document = (document.replace("WORKSPACE_INPUT_MODE_REALTIME", "WORKSPACE_INPUT_MODE_PUSH_TO_TALK")
                        .replace("mode: realtime", "mode: push-to-talk")
                        .replace("_realtime", "_ptt")
                        .replace("realtime responsiveness", "native PTT responsiveness"))
        files[f"tests/giztest/{tier}/{raid}.{VARIANT}.giztest.yaml"] = document
    return files


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, help="output root (default: repository root)")
    parser.add_argument("raids", nargs="*", help="specific figure-* raid IDs (default: all)")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo = repository_root()
    out = args.out.resolve() if args.out else repo
    raids = args.raids or discover_raids(repo)
    if not raids:
        raise ValueError("no workflows/figure-*/figure.json found")
    for raid in raids:
        data = load(repo, raid)
        for relative, text in outputs(raid, data).items():
            target = out / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(text, encoding="utf-8")
        print(f"generated {raid}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, ValueError, KeyError) as error:
        print(f"generate figure raids: {error}", file=sys.stderr)
        sys.exit(1)
