#!/usr/bin/env python3
"""Regenerate figure-* raid packages from workflows/<raid>/figure.json and cards/figure/<人物>.txt."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

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
    for role in cast(data):
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
    return json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"


def outputs(raid: str, data: dict[str, Any]) -> dict[str, str]:
    slots = values(raid, data)
    files = {
        f"workflows/{raid}/raid.json": raid_manifest(raid, data),
        f"workflows/{raid}/README.md": render_readme(raid, data, slots),
        f"workflows/{raid}/routing-cases.json": render_routing(raid, data, slots),
        f"workflows/{raid}/test.multi-role.yaml": fill(template("test.multi-role.yaml"), slots),
        f"workflows/{raid}/{VARIANT}.yaml": fill(template(f"{VARIANT}.yaml"), slots),
    }
    for tier in TIERS:
        files[f"tests/giztest/{tier}/{raid}.{VARIANT}.giztest.yaml"] = fill(template(f"{tier}.{VARIANT}.giztest.yaml"), slots)
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
