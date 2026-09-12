"""Subject-independent rendering helpers for learn-* raid packages."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


ADVENTURE = "adventure-science"
GIZTEST_FILES = (
    "eino.giztest.yaml",
    "flowcraft.giztest.yaml",
    "eino.realtime.giztest.yaml",
    "flowcraft.realtime.giztest.yaml",
)
GRADE_NUMERALS = "一二三四五六"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8")


def write_json(path: Path, value: Any) -> None:
    write_text(path, json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def indent(text: str, width: int) -> str:
    prefix = " " * width
    return "\n".join(prefix + line if line else line for line in text.split("\n"))


def grade_name(grade: int) -> str:
    return GRADE_NUMERALS[grade - 1] + "年级"


def learning_prompts(rules: str, body: str, index: str) -> tuple[str, str]:
    flowcraft = "\n".join([
        rules, "知识卡：", body, index,
        "可核对的长期学习进度：${board.scenario_memory}",
        "回复必须与上面已确认的学习进度一致，不得推翻孩子已确认的年级、已学的内容或孩子的更正。",
    ])
    eino = "\n".join([
        rules, "知识卡：", body, index, "",
        "相关长期记忆只用于承接已确认的学习进度；为空时忽略，不得让旧记忆覆盖孩子当前的更正：", "{memory}",
    ])
    return flowcraft, eino


def replace_once(text: str, old: str, new: str, *, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise ValueError(f"expected one {label}, found {count}")
    return text.replace(old, new, 1)


def replace_block(text: str, start_marker: str, end_marker: str, body: str) -> str:
    try:
        start = text.index(start_marker) + len(start_marker)
        end = text.index(end_marker, start)
    except ValueError as error:
        raise ValueError("template block markers changed") from error
    return text[:start] + body + text[end:]


def render_flowcraft(repo: Path, raid: str, system_prompt: str) -> str:
    text = read_text(repo / "workflows" / ADVENTURE / "flowcraft.yaml")
    text = text.replace(ADVENTURE, raid)
    text = text.replace("adventure-guide", "tutor")
    text = text.replace("memory: adventure", "memory: learner")
    text = replace_once(
        text,
        "            lanes:\n            - story_progress",
        "            lanes:\n            - learning_events",
        label="Flowcraft recall lane",
    )
    text = replace_once(
        text,
        "                lane: story_progress\n                kind: state",
        "                lane: learning_events\n                kind: event",
        label="Flowcraft observation lane",
    )
    text = text.replace('"raid_scenario_state_v2"', '"learn_progress_v1"')
    text = text.replace("'Confirmed scenario history:'", "'Confirmed learning history:'")
    text = replace_block(
        text,
        "system_prompt: |-\n",
        "\n          track_steps: true",
        indent(system_prompt, 12),
    )
    if "adventure" in text.replace("memory_observe", ""):
        raise ValueError("Flowcraft learn rendering left an adventure reference")
    return text


def render_eino(repo: Path, raid: str, system_prompt: str, memory_description: str) -> str:
    text = read_text(repo / "workflows" / ADVENTURE / "eino.yaml")
    text = text.replace(ADVENTURE, raid)
    text = text.replace("memory: adventure", "memory: learner")
    text = replace_once(
        text,
        'base = "当前互动剧本的已确认选择、场景进度、事实和用户明确要求记住的信息"',
        f'base = "{memory_description}"',
        label="Eino memory description",
    )
    text = replace_block(
        text,
        "        - role: system\n          template: |-\n",
        "\n        - placeholder: history",
        indent(system_prompt, 12),
    )
    if "adventure" in text.replace("memory_observe", ""):
        raise ValueError("Eino learn rendering left an adventure reference")
    return text


def render_tester(
    repo: Path,
    raid: str,
    route: Sequence[tuple[str, str, str, Mapping[str, Any]]],
    rules: str,
) -> str:
    text = read_text(repo / "workflows" / ADVENTURE / "test.yaml")
    text = text.replace(ADVENTURE, raid)
    dumps = lambda value: json.dumps(value, ensure_ascii=False)
    start = text.index("          REQUESTS = ")
    end = text.index("          PERSONA = ", start)
    block = (
        "          REQUESTS = " + dumps([item[1] for item in route]) + "\n"
        "          INTENTS = " + dumps([""] * len(route)) + "\n"
        "          CHECKPOINTS = " + dumps([item[0] for item in route]) + "\n"
        "          CONTRACTS = " + dumps([item[2] for item in route]) + "\n"
        "          CHECKS = " + dumps([item[3] for item in route]) + "\n"
        "          RULES = " + dumps(rules) + "\n"
    )
    text = text[:start] + block + text[end:]
    text, count = re.subn(r"\n          N = \d+\n", f"\n          N = {len(route)}\n", text)
    if count != 1:
        raise ValueError(f"expected one Tester route length, found {count}")
    return text


def render_giztests(
    repo: Path,
    raid: str,
    route_size: int,
    recall_query: str,
    realtime_text: str,
) -> dict[str, str]:
    rendered: dict[str, str] = {}
    source = repo / "tests" / "giztest" / ADVENTURE
    before_reload_turns = 2 * (route_size - 1)
    per_client_turns = route_size - 1
    for name in GIZTEST_FILES:
        text = read_text(source / name).replace(ADVENTURE, raid)
        if ".realtime." in name:
            text = replace_once(
                text,
                "text: 请简短介绍当前故事，并告诉我现在可以做什么。",
                f"text: {realtime_text}",
                label=f"{name} synthesized text",
            )
        else:
            text = replace_once(
                text, "the 7-response", f"the {route_size}-response", label=f"{name} response count"
            )
            text = replace_once(
                text, "    max_turns: 12", f"    max_turns: {before_reload_turns}", label=f"{name} relay turns"
            )
            text = replace_once(
                text, "      equals: 12", f"      equals: {before_reload_turns}", label=f"{name} completed turns"
            )
            old_counts = "    /turns/candidate/count:\n      equals: 6\n    /turns/tester/count:\n      equals: 6"
            new_counts = (
                "    /turns/candidate/count:\n"
                f"      equals: {per_client_turns}\n"
                "    /turns/tester/count:\n"
                f"      equals: {per_client_turns}"
            )
            text = replace_once(text, old_counts, new_counts, label=f"{name} per-client turns")
            text = replace_once(text, "      query: 星火七号", f"      query: {recall_query}", label=f"{name} recall query")
        rendered[name] = text
    return rendered


def render_raid_manifest(
    repo: Path,
    raid: str,
    *,
    title: Mapping[str, str],
    summary: Mapping[str, str],
    tags: Sequence[str],
    route: Sequence[tuple[str, str, str, Mapping[str, Any]]],
    voice_description: str,
) -> dict[str, Any]:
    manifest = json.loads(read_text(repo / "workflows" / ADVENTURE / "raid.json"))
    manifest = json.loads(
        json.dumps(manifest, ensure_ascii=False).replace(ADVENTURE, raid).replace("adventure-guide", "tutor")
    )
    manifest["category"] = "learn"
    manifest["title"] = dict(title)
    manifest["summary"] = dict(summary)
    manifest["rating"]["age"] = "6+"
    manifest["tags"] = list(tags)
    for engine in ("eino", "flowcraft"):
        implementation = manifest["implementations"][engine]
        implementation["memory"]["layout_id"] = "learner"
        for model in implementation["parameters"]["models"].values():
            model["role"] = "tutor"
    voice = manifest["implementations"]["flowcraft"]["parameters"]["voices"]
    voice[f"flowcraft-{raid}.tutor"]["description"] = voice_description
    manifest["tester"]["route"] = {
        "responses": len(route),
        "checkpoints": [item[0] for item in route],
    }
    return manifest


def markdown_link(url: str) -> str:
    return url.replace("(", "%28").replace(")", "%29").replace(" ", "%20")


def source_links(urls: Iterable[str]) -> str:
    return " ".join(f"[{index}]({markdown_link(url)})" for index, url in enumerate(urls, 1))


def implementation_table(raid: str) -> str:
    return f"""| File | Workflow ID | Engine | Memory layout | Model slots | Voice slots |
| --- | --- | --- | --- | --- | --- |
| `eino.yaml` | `eino-{raid}` | eino | learner | `eino-{raid}.model` | - |
| `flowcraft.yaml` | `flowcraft-{raid}` | flowcraft | learner | `flowcraft-{raid}.model` | `flowcraft-{raid}.tutor` |"""
