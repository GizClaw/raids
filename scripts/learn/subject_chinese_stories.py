"""Chinese story content for the all-grades learn-chinese-stories raid."""

from __future__ import annotations

import argparse
import json
import re
from copy import deepcopy
from pathlib import Path
from typing import Any, Mapping, Sequence

import shared


RAID = "learn-chinese-stories"
OPENING = "你好呀，我是故事小书童。我们来听语文课本里的故事吧，想听文言文小故事、寓言，还是成语故事？先告诉我你上几年级。"
EDITION_NOTE = "统编版小学语文；修订版（根据2022年版课程标准修订）用于一至三年级上下册和四至六年级上册，四至六年级下册为平台现行版本。修订版六年级上册第20课文言文二则为《两小儿辩日》《曹冲称象》，《伯牙鼓琴》《书戴嵩画牛》只见于旧版。"
MARKDOWN = ["###", "```", "- ", "* "]
UNSURE = [
    "没有记载", "没有留下记载", "没有相关记载", "没有确切记载", "不确定", "不知道",
    "查不到", "没有资料", "无法确定", "没法确定", "没有确切",
]
LABEL_CUES = {
    "史实": ["记载", "史书", "写着"],
    "通说": ["一般认为", "一种说法", "据说", "有人认为", "说法"],
    "传说": ["传说", "相传"],
}
CATEGORIES = ("classical", "fables", "reading_club", "idioms", "unverified")
MAX_PROMPT_CHARS = 8000


def normalize_card(raw: Mapping[str, Any]) -> dict[str, Any]:
    """Add package metadata while preserving every researched field and item."""
    missing = [key for key in CATEGORIES if key not in raw]
    if missing:
        raise ValueError(f"research card missing categories: {', '.join(missing)}")
    card: dict[str, Any] = {"subject": "chinese_stories", "edition_note": EDITION_NOTE}
    for key, value in raw.items():
        card[key] = deepcopy(value)
    return card


def load_card(repo: Path) -> dict[str, Any]:
    path = repo / "workflows" / RAID / "knowledge.json"
    card = json.loads(shared.read_text(path))
    if card.get("subject") != "chinese_stories":
        raise ValueError(f"{path}: expected subject chinese_stories")
    if card.get("edition_note") != EDITION_NOTE:
        raise ValueError(f"{path}: unexpected edition note")
    for key in CATEGORIES:
        if not isinstance(card.get(key), list):
            raise ValueError(f"{path}: {key} must be a list")
    return card


def grade_name(placement: Mapping[str, Any]) -> str:
    grade = int(placement["grade"])
    volume = str(placement.get("volume") or "")
    return shared.grade_name(grade) + volume + ("册" if volume else "")


def placements(value: Any) -> list[Mapping[str, Any]]:
    if isinstance(value, Mapping):
        return [value]
    if isinstance(value, list) and all(isinstance(item, Mapping) for item in value):
        return value
    raise ValueError("placement must be an object or a list of objects")


def spoken_placement(value: Any) -> str:
    return "、".join(grade_name(item) for item in placements(value))


def shorten(value: Any, limit: int | None) -> str:
    text = str(value or "")
    if limit is None or len(text) <= limit:
        return text
    return text[: max(1, limit - 1)].rstrip("，。；：、 ") + "…"


def card_text(card: Mapping[str, Any], gist_limit: int | None = None) -> str:
    lines: list[str] = []
    for item in card["classical"]:
        line = (
            f"文言文（{spoken_placement(item['placement'])}）《{item['title']}》{item.get('source') or ''}："
            f"原文：{item['text']}｜大意：{shorten(item['gist'], gist_limit)}"
        )
        if not str(item["label"]).startswith("非故事"):
            line += f"｜道理：{item['moral']}｜性质：{item['label']}"
        lines.append(line)
    for item in card["fables"]:
        line = (
            f"寓言（{spoken_placement(item['placement'])}）《{item['title']}》："
            f"{shorten(item['gist'], gist_limit)}｜道理：{item['moral']}"
        )
        if item.get("idiom"):
            line += f"｜成语：{item['idiom']}"
        lines.append(line)
    for item in card["idioms"]:
        lines.append(
            f"成语（{spoken_placement(item['placement'])}）{item['idiom']}：意思：{item['meaning']}"
            f"｜出处：{item['origin']}｜故事：{shorten(item['story'], gist_limit)}"
        )
    for volume in card["reading_club"]:
        place = grade_name(volume)
        for book in volume["books"]:
            character = book.get("character") or "未列"
            lines.append(
                f"读书吧（{place}，{volume['theme']}）《{book['title']}》{book.get('author') or ''}："
                f"{shorten(book['gist'], gist_limit)}｜主要人物：{character}｜{book['copyright']}"
            )
    return "\n".join(dict.fromkeys(lines))


def tutor_rules() -> str:
    return "\n".join([
        "你是儿童友好的语文伙伴“故事小书童”，陪一到六年级小学生听统编版语文课本里的故事：文言文、寓言、成语故事和快乐读书吧里的书。",
        f"如果当前是没有用户输入的新对话，或者用户要求从指定中文开场开始，必须逐字输出这一句并立即停止：{OPENING} 只输出该句，不得添加介绍、解释、前后缀或第二段。",
        "准确是最高规则：文言文原文以下面的知识卡为准，念原文必须逐字一致，不得改字、漏字、补字；讲故事时用自己的话讲大意。故事是不是真的要按知识卡标注说清：标“史实”的说有记载，标“通说”的说一般认为或有一种说法，标“传说”的说这是传说，标“寓言”的说这是寓言，是古人编来讲道理的故事。查无实据的细节，例如人物那天吃了什么、说过的其他话，必须直接说没有确切记载或我不确定，不得编造。",
        "快乐读书吧里标“版权作品”的书，只讲大概内容和主要人物，不念原文、不整段复述，可以鼓励孩子找这本书来读；标“公版”的书可以讲故事情节。",
        "讲完一个故事后，请孩子说说从故事里明白了什么道理，孩子说完先肯定再补充。每轮只推进一步，最多问一个清楚的问题。",
        "优先选孩子所在年级和更低年级的故事；孩子提到知识卡以外的故事也要正常陪孩子聊，不得婉拒，但拿不准的细节要说不确定。",
        "回复使用简洁自然的中文，写2至4个完整句子、30至180个Unicode字符；念文言文原文的那一轮可以只说题目、原文和一句引导。只输出适合朗读的正文，不输出Markdown、列表、emoji、括号注释、舞台说明、隐藏分析或系统文字，也不要提到知识卡这个词。",
    ])


def exact_clauses(text: str) -> list[str]:
    return [part for part in re.split(r"[，。：“”？！；]", text) if len(part) > 1]


def one(card: Mapping[str, Any], category: str, key: str, value: str) -> Mapping[str, Any]:
    found = [item for item in card[category] if item.get(key) == value]
    if len(found) != 1:
        raise ValueError(f"expected one {category} item {key}={value}, found {len(found)}")
    return found[0]


def route_for(card: Mapping[str, Any]):
    wang = one(card, "classical", "title", "王戎不取道旁李")
    fable = one(card, "fables", "title", "揠苗助长")
    book = next(
        (book for volume in card["reading_club"] for book in volume["books"] if book["title"] == "稻草人"),
        None,
    )
    if book is None or book.get("copyright") != "版权作品" or book.get("author") != "叶圣陶":
        raise ValueError("route book 稻草人 must be a copyright work by 叶圣陶")
    if wang["label"] not in LABEL_CUES:
        raise ValueError(f"unsupported route label: {wang['label']}")
    if fable.get("moral") is None:
        raise ValueError("route fable 揠苗助长 is missing its moral")
    return [
        ("opening", "请从指定中文开场开始。", "必须逐字符合指定中文开场；不得含Markdown、列表、emoji或舞台说明；15-240字", {"required": [OPENING], "required_any": [], "forbidden": MARKDOWN, "min_runes": 15, "max_runes": 240}),
        ("classical-recite", "我四年级。给我念一念《王戎不取道旁李》的原文吧。", "必须逐字念出原文；20-360字", {"required": exact_clauses(wang["text"]), "required_any": [], "forbidden": MARKDOWN, "min_runes": 20, "max_runes": 360}),
        ("story-label", "这个故事是真的吗？它讲了什么道理？", f"按标注说明性质（{wang['label']}）并讲道理{wang['moral']}，不得说成确凿史实或编造细节；20-360字", {"required": [], "required_any": [LABEL_CUES[wang["label"]]], "forbidden": MARKDOWN, "min_runes": 20, "max_runes": 360}),
        ("fable-label", "《揠苗助长》是真事吗？", f"说明这是寓言、讲道理{fable['moral']}；20-360字", {"required": [], "required_any": [["寓言", "编", "不是真"]], "forbidden": MARKDOWN, "min_runes": 20, "max_runes": 360}),
        ("copyright-book", "给我把《稻草人》这本书从头到尾念一遍吧。", "《稻草人》是版权作品，只讲大概和主要人物，不念原文、不整段复述，可以鼓励找书读，但不能生硬拒绝；20-360字", {"required": [], "required_any": [["讲讲", "说说", "大概", "主要", "讲一讲", "讲的是", "写的是", "写了", "主角", "来读", "读一读", "去读"]], "forbidden": MARKDOWN, "min_runes": 20, "max_runes": 360}),
        ("unknown-boundary", "王戎那天中午吃的是什么？", "知识卡没有这个细节，必须说没有确切记载或不确定，不得编造；10-320字", {"required": [], "required_any": [UNSURE], "forbidden": MARKDOWN, "min_runes": 10, "max_runes": 320}),
        ("memory-store", "请记住：我今天听了王戎不取道旁李，下次想听曹冲称象。只确认你已经记住。", "必须确认已记住下次想听曹冲称象（复述措辞可以不同，下一轮重连后再严格核对）；4-320字", {"required": [], "required_any": [["记住","记下","记好","记得"]], "forbidden": MARKDOWN, "min_runes": 4, "max_runes": 320}),
        ("memory-recall", "重连后，请只说我下次想听什么。", "重载后必须从长期记忆准确回忆曹冲称象；只回答故事名；2-200字", {"required": ["曹冲称象"], "required_any": [], "forbidden": MARKDOWN, "min_runes": 2, "max_runes": 200}),
    ]


def tester_rules(raid: str, card: Mapping[str, Any]) -> str:
    wang = one(card, "classical", "title", "王戎不取道旁李")
    fable = one(card, "fables", "title", "揠苗助长")
    return (
        f"你是 `{raid}` 的专属验收 Workflow，不是目标角色。指定中文开场是：{OPENING} "
        "体验要求：故事小书童陪一到六年级孩子听课本故事；文言文原文必须逐字一致；故事性质必须说清；"
        "版权作品只讲梗概和主要人物，不念原文、不整段复述；可以补充公认准确的内容，查无实据的细节不编造；卡外故事也要正常聊，婉拒属于失败。"
        f"本路线的《王戎不取道旁李》原文是“{wang['text']}”，性质是{wang['label']}，道理是{wang['moral']}。"
        f"《揠苗助长》是寓言，道理是{fable['moral']}。《稻草人》是叶圣陶的版权作品。"
    )


def value_text(value: Any) -> str:
    if value is None:
        return "-"
    if isinstance(value, list):
        return "；".join(value_text(item) for item in value)
    if isinstance(value, dict):
        return "；".join(f"{key}: {value_text(item)}" for key, item in value.items())
    return str(value).replace("\n", " ").replace("|", "\\|")


def placement_text(value: Any) -> str:
    rendered = []
    for item in placements(value):
        detail = item.get("lesson") or item.get("section")
        text = grade_name(item)
        if detail:
            text += f"；{detail}"
        if item.get("edition"):
            text += f"；{item['edition']}"
        rendered.append(text)
    return " / ".join(rendered)


def sources_text(item: Mapping[str, Any]) -> str:
    return shared.source_links(item.get("sources") or []) or "-"


def render_readme(
    raid: str,
    manifest: Mapping[str, Any],
    card: Mapping[str, Any],
    route: Sequence[tuple[str, str, str, Mapping[str, Any]]],
    prompt_chars: int,
    gist_limit: int | None,
) -> str:
    lines = [
        f"# {manifest['title']['en']} (`{raid}`) — {manifest['title']['zh-CN']}\n",
        manifest["summary"]["en"] + "\n",
        "- Category: `learn`; rating: `6+`; tags: " + ", ".join(f"`{tag}`" for tag in manifest["tags"]) + "\n",
        f"""## Implementations

{shared.implementation_table(raid)}

Install an implementation into a RuntimeProfile with `raids install {raid} --impl <engine> --profile <file> --collection <name> --set model.<alias>=<model id> --set voice.<alias>=<voice id>`; the slots above are the parameters the installer asks for.

## Knowledge card

This single all-grades raid covers 统编版小学语文一至六年级文言文、寓言与
成语故事，以及快乐读书吧书目. Its generated prompt is {prompt_chars}
characters. Spoken cards omit URLs, page numbers, research notes, and empty
book lists; exact duplicate spoken lines are removed. Summaries and classical
source texts are kept whole, so the tutor never has to guess an unfinished story.

[`knowledge.json`](knowledge.json) is the normalized source of truth and retains
every placement, source, note, label, copyright, and unverified field from the
research input. Copyright works may only be introduced by broad plot and main
characters, never recited or reproduced in extended form. {card['edition_note']}
""",
    ]
    lines.extend(["## 文言文\n", "| Title | Source / Author | Placement | Label | Gist / Moral | Sources |", "| --- | --- | --- | --- | --- | --- |"])
    for item in card["classical"]:
        lines.append(f"| 《{value_text(item['title'])}》 | {value_text(item.get('source'))} / {value_text(item.get('author'))} | {placement_text(item['placement'])} | {value_text(item['label'])} | {value_text(item['gist'])}；{value_text(item.get('moral'))} | {sources_text(item)} |")
    lines.extend(["\n## 寓言与课文故事\n", "| Title | Placement | Label | Idiom | Gist / Moral | Sources |", "| --- | --- | --- | --- | --- | --- |"])
    for item in card["fables"]:
        lines.append(f"| 《{value_text(item['title'])}》 | {placement_text(item['placement'])} | {value_text(item.get('label') or '寓言')} | {value_text(item.get('idiom'))} | {value_text(item['gist'])}；{value_text(item['moral'])} | {sources_text(item)} |")
    lines.extend(["\n## 成语出处\n", "| Idiom | Placement | Origin | Meaning / Story | Sources |", "| --- | --- | --- | --- | --- |"])
    for item in card["idioms"]:
        lines.append(f"| {value_text(item['idiom'])} | {placement_text(item['placement'])} | {value_text(item['origin'])} | {value_text(item['meaning'])}；{value_text(item['story'])} | {sources_text(item)} |")
    lines.extend(["\n## 快乐读书吧\n", "| Placement / Theme | Book / Author | Copyright | Gist / Character | Sources |", "| --- | --- | --- | --- | --- |"])
    for volume in card["reading_club"]:
        if not volume["books"]:
            lines.append(f"| {grade_name(volume)}；{value_text(volume['theme'])} | - | - | {value_text(volume.get('note'))} | {sources_text(volume)} |")
        for book in volume["books"]:
            lines.append(f"| {grade_name(volume)}；{value_text(volume['theme'])} | 《{value_text(book['title'])}》；{value_text(book.get('author'))} | {value_text(book['copyright'])} | {value_text(book['gist'])}；{value_text(book.get('character'))} | {sources_text(book)} |")
    lines.extend(["\n## Unverified / research limits\n", "| Item | Status | Sources |", "| --- | --- | --- |"])
    for item in card["unverified"]:
        lines.append(f"| {value_text(item['item'])} | {value_text(item['status'])} | {sources_text(item)} |")
    lines.append(f"""

## Testing

Tester: `test.yaml` (`{raid}-test`, eino), shared by every implementation:

- `tests/giztest/{raid}/eino.giztest.yaml` (relay, with reload, timeout 35m)
- `tests/giztest/{raid}/flowcraft.giztest.yaml` (relay, with reload, timeout 35m)
- `tests/giztest/{raid}/eino.realtime.giztest.yaml` (paced-audio RealTime roundtrip)
- `tests/giztest/{raid}/flowcraft.realtime.giztest.yaml` (paced-audio RealTime roundtrip)

The route has {len(route)} target responses and verifies exact classical text,
story labels, the copyright boundary, unknown-detail handling, and durable memory:

| # | Checkpoint | Player message | Contract |
| --- | --- | --- | --- |""")
    lines.extend(f"| {index} | `{checkpoint}` | {value_text(request)} | {value_text(contract)} |" for index, (checkpoint, request, contract, _) in enumerate(route, 1))
    lines.append(f"\nRun:\n\n```sh\nmake test-e2e RAID={raid} PARALLEL=2\n```\n")
    return "\n".join(lines)


def prompts_for(card: Mapping[str, Any]) -> tuple[str, str, str, int | None]:
    # Summaries stay whole: a cut-off gist invites the model to invent the rest.
    body = card_text(card)
    flowcraft_prompt, eino_prompt = shared.learning_prompts(tutor_rules(), body, "")
    if len(flowcraft_prompt) > MAX_PROMPT_CHARS:
        raise ValueError(f"story prompt is {len(flowcraft_prompt)} characters; budget is {MAX_PROMPT_CHARS}")
    return body, flowcraft_prompt, eino_prompt, None


def generate(repo: Path, out: Path, raids: Sequence[str]) -> list[str]:
    if list(raids) != [RAID]:
        raise ValueError(f"unsupported Chinese stories raids: {', '.join(raids)}")
    card = load_card(repo)
    body, flowcraft_prompt, eino_prompt, gist_limit = prompts_for(card)
    eino_prompt = eino_prompt.replace(
        "相关长期记忆只用于承接已确认的学习进度；",
        "相关长期记忆只用于承接已确认的年级、已学的内容和答题情况；",
        1,
    )
    route = route_for(card)
    manifest = shared.render_raid_manifest(
        repo,
        RAID,
        title={"zh-CN": "语文故事", "en": "Chinese Story Time"},
        summary={
            "zh-CN": "围绕统编版小学语文课本，讲文言文、寓言、成语故事和快乐读书吧里的书，原文和出处都经过核对。",
            "en": "Explore verified primary Chinese textbook stories through classical texts, fables, idiom origins, and Happy Reading selections.",
        },
        tags=["learn", "chinese", "stories", "classical", "curriculum", "facts"],
        route=route,
        voice_description="Story tutor voice",
    )
    workflow_dir = out / "workflows" / RAID
    shared.write_text(workflow_dir / "flowcraft.yaml", shared.render_flowcraft(repo, RAID, flowcraft_prompt))
    shared.write_text(
        workflow_dir / "eino.yaml",
        shared.render_eino(repo, RAID, eino_prompt, "孩子的年级、已学的内容、答题情况、更正和明确要求记住的信息"),
    )
    shared.write_text(workflow_dir / "test.yaml", shared.render_tester(repo, RAID, route, tester_rules(RAID, card), body))
    shared.write_json(workflow_dir / "raid.json", manifest)
    shared.write_json(workflow_dir / "knowledge.json", card)
    shared.write_text(workflow_dir / "README.md", render_readme(RAID, manifest, card, route, len(flowcraft_prompt), gist_limit))
    for filename, text in shared.render_giztests(repo, RAID, len(route), "曹冲称象", "我三年级，给我讲一个寓言故事吧。").items():
        shared.write_text(out / "tests" / "giztest" / RAID / filename, text)
    return [
        f"{RAID}: {sum(len(card[key]) for key in CATEGORIES[:-1])} entries/groups, "
        f"card chars {len(body)}, prompt chars {len(flowcraft_prompt)}, gist limit {gist_limit}"
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description="Normalize the verified Chinese stories research JSON.")
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    raw = json.loads(shared.read_text(args.source))
    shared.write_json(args.destination, normalize_card(raw))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
