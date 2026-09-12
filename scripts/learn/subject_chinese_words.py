"""Chinese word-treasury content for the all-grades learn-chinese-words raid."""

from __future__ import annotations

import argparse
import json
from copy import deepcopy
from pathlib import Path
from typing import Any, Mapping, Sequence

import shared


RAID = "learn-chinese-words"
OPENING = "你好呀，我是语文小书童。我们来玩语文积累游戏吧，猜谚语下半句、猜歇后语，还是听一个汉字的小故事？先告诉我你上几年级。"
EDITION_NOTE = "统编版小学语文；修订版（根据2022年版课程标准修订）用于一至三年级上下册和四至六年级上册，四至六年级下册为平台现行版本。内容来自语文园地·日积月累和识字课。"
MARKDOWN = ["###", "```", "- ", "* "]
UNSURE = [
    "没有记载", "没有留下记载", "没有相关记载", "没有确切记载", "不确定", "不知道",
    "查不到", "没有资料", "无法确定", "没法确定", "没有确切",
]
CATEGORIES = ("proverbs", "xiehouyu", "quotes", "couplets", "characters", "unverified")


def normalize_card(raw: Mapping[str, Any]) -> dict[str, Any]:
    """Add package metadata while preserving every researched field and item."""
    missing = [key for key in CATEGORIES if key not in raw]
    if missing:
        raise ValueError(f"research card missing categories: {', '.join(missing)}")
    card: dict[str, Any] = {
        "subject": "chinese_words",
        "edition_note": EDITION_NOTE,
    }
    for key, value in raw.items():
        card[key] = deepcopy(value)
    return card


def load_card(repo: Path) -> dict[str, Any]:
    path = repo / "workflows" / RAID / "knowledge.json"
    card = json.loads(shared.read_text(path))
    if card.get("subject") != "chinese_words":
        raise ValueError(f"{path}: expected subject chinese_words")
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


def dispute_note(item: Mapping[str, Any]) -> str:
    text = str(item["text"])
    notes = {
        "黑发不知勤学早，白首方悔读书迟。": "课本没写作者，常说是颜真卿，但没找到可靠早期出处",
        "书山有路勤为径，学海无涯苦作舟。": "课本没写作者，常说是韩愈，但他的作品里找不到这句",
        "与朋友交，言而有信。": "这句是子夏说的，不是孔子说的",
        "士不可以不弘毅，任重而道远。": "这句是曾子说的，不是孔子说的",
        "莫等闲，白了少年头，空悲切。": "课本写岳飞，但《满江红》是不是他写的仍有争议",
    }
    return notes.get(text, str(item["disputed"]).rstrip("。"))


def card_text(card: Mapping[str, Any]) -> str:
    lines: list[str] = []
    for item in card["proverbs"]:
        lines.append(f"谚语（{grade_name(item['placement'])}）：{item['text']}｜意思：{item['meaning']}")
    for item in card["xiehouyu"]:
        lines.append(
            f"歇后语（{grade_name(item['placement'])}）：{item['front']}——{item['back']}｜意思：{item['meaning']}"
        )
    for item in card["quotes"]:
        line = (
            f"名言（{grade_name(item['placement'])}）：{item['text']}｜出处：{item['author']}"
            f"｜意思：{item['meaning']}"
        )
        if item.get("disputed"):
            line += f"｜注意：{dispute_note(item)}"
        lines.append(line)
    for item in card["couplets"]:
        lines.append(f"对子（{grade_name(item['placement'])}）：{item['text']}")
    for item in card["characters"]:
        story = item.get("story") or "没有另外记载小故事"
        lines.append(
            f"汉字（{grade_name(item['placement'])}）：{item['char']}｜古字样子：{item['ancient_form']}｜来历：{story}"
        )
    return "\n".join(dict.fromkeys(lines))


def tutor_rules() -> str:
    return "\n".join([
        "你是儿童友好的语文伙伴“语文小书童”，陪一到六年级小学生玩统编版语文课本里的语言积累：谚语、歇后语、名言、对子和汉字小故事。",
        f"如果当前是没有用户输入的新对话，或者用户要求从指定中文开场开始，必须逐字输出这一句并立即停止：{OPENING} 只输出该句，不得添加介绍、解释、前后缀或第二段。",
        "准确是最高规则：谚语、歇后语、名言、对子的原文以下面的知识卡为准，念原文必须逐字一致；名言的作者和出处按知识卡说，标了注意的要把争议说清楚，不得肯定地说成某个人的话。拿不准的出处、年代和人物细节，必须直接说没有确切记载或我不确定，不得编造。",
        "游戏方式：出猜下半句或猜歇后语的题时，只说前半句，等孩子接，不在同一轮说出后半句；孩子接对了具体夸一夸，接错了温和地说不对，再给一个小提示，比如后半句有几个字或第一个字，不直接公布；只有孩子说猜不出来或要求公布时，才说出答案并讲意思。每轮只推进一步，最多问一个清楚的问题。",
        "优先选孩子所在年级和更低年级的内容；孩子提到知识卡以外的谚语、成语或名言也要正常陪孩子聊，不得婉拒，但出处拿不准时要说不确定。",
        "讲汉字时用语言描述古字的样子，不说“看图”；讲完可以请孩子用手指在空中比划一下。",
        "回复使用简洁自然的中文，写2至4个完整句子、30至180个Unicode字符。只输出适合朗读的正文，不输出Markdown、列表、emoji、括号注释、舞台说明、隐藏分析或系统文字，也不要提到知识卡这个词。",
    ])


def route_for(card: Mapping[str, Any]):
    bamboo = [item for item in card["xiehouyu"] if item["front"] == "竹篮打水"]
    mountain = [item for item in card["quotes"] if item["text"].startswith("书山有路勤为径")]
    forest = [item for item in card["characters"] if item["char"] == "森"]
    if len(bamboo) != 1 or bamboo[0]["back"] != "一场空":
        raise ValueError("route fact 竹篮打水——一场空 does not match knowledge card")
    if len(mountain) != 1 or not mountain[0].get("disputed"):
        raise ValueError("route quote 书山有路勤为径 is missing or not disputed")
    if len(forest) != 1 or "三个“木”" not in forest[0]["ancient_form"]:
        raise ValueError("route character 森 does not describe three 木")
    no_answer = MARKDOWN + ["一场空"]
    return [
        ("opening", "请从指定中文开场开始。", "必须逐字符合指定中文开场；不得含Markdown、列表、emoji或舞台说明；15-240字", {"required": [OPENING], "required_any": [], "forbidden": MARKDOWN, "min_runes": 15, "max_runes": 240}),
        ("riddle-no-spoiler", "我一年级。我们来猜歇后语：竹篮打水，下半句是什么？你先别告诉我，给我一个提示。", "只给提示，不得说出后半句；20-360字", {"required": [], "required_any": [], "forbidden": no_answer, "min_runes": 20, "max_runes": 360}),
        ("wrong-guess", "是“一场雨”吗？", "温和说不对并再给一个提示，不得公布答案；10-360字", {"required": [], "required_any": [["不对", "不是", "差一点", "再想想", "不太对"]], "forbidden": no_answer, "min_runes": 10, "max_runes": 360}),
        ("reveal", "我猜不出来，告诉我答案和意思吧。", "说出“竹篮打水——一场空”并讲清意思；20-360字", {"required": ["一场空"], "required_any": [], "forbidden": MARKDOWN, "min_runes": 20, "max_runes": 360}),
        ("disputed-quote", "“书山有路勤为径”是谁说的？", "必须说明课本没写作者、常说是韩愈但他的作品里找不到这句，不得肯定地说就是韩愈说的；20-360字", {"required": [], "required_any": [["没写", "没有写", "不确定", "说法", "一般认为", "常说", "有人说", "没有确切", "找不到", "不同"]], "forbidden": MARKDOWN, "min_runes": 20, "max_runes": 360}),
        ("character-story", "给我讲讲“森”字是怎么来的。", "按知识卡描述古字样子（三个木），不说看图；20-360字", {"required": [], "required_any": [["木"]], "forbidden": MARKDOWN + ["看图"], "min_runes": 20, "max_runes": 360}),
        ("memory-store", "请记住：我今天学会了歇后语竹篮打水，下次想学对韵歌。只确认你已经记住。", "必须确认已记住下次想学对韵歌（复述措辞可以不同，下一轮重连后再严格核对）；4-320字", {"required": [], "required_any": [["记住","记下","记好","记得"]], "forbidden": MARKDOWN, "min_runes": 4, "max_runes": 320}),
        ("memory-recall", "重连后，请只说我下次想学什么。", "重载后必须从长期记忆准确回忆对韵歌；只回答主题；2-200字", {"required": ["对韵歌"], "required_any": [], "forbidden": MARKDOWN, "min_runes": 2, "max_runes": 200}),
    ]


def tester_rules(raid: str, card: Mapping[str, Any]) -> str:
    route_for(card)
    return (
        f"你是 `{raid}` 的专属验收 Workflow，不是目标角色。指定中文开场是：{OPENING} "
        "体验要求：语文小书童陪一到六年级孩子玩语言积累；谚语、歇后语、名言和对子原文必须逐字一致；猜题必须先提示后公布；"
        "孩子接错时要温和说不对并再提示，不直接公布；孩子明确猜不出时才公布并解释；名言争议必须说清，不编造出处、年代和人物细节；"
        "孩子提到卡外的谚语、成语或名言也要正常陪聊，婉拒属于失败。"
        "本路线的歇后语是“竹篮打水——一场空”，意思是白费力气，什么也没得到。"
        "“书山有路勤为径，学海无涯苦作舟”在课本中未署作者，常被说成韩愈所作，但韩愈作品里没有这两句，作者不详。"
        "“森”的古字样子是三个“木”叠在一起，表示树木又多又密；课文写“三木森”。"
    )


def value_text(value: Any) -> str:
    if value is None:
        return "-"
    if isinstance(value, list):
        return "；".join(value_text(item) for item in value)
    if isinstance(value, dict):
        return "；".join(f"{key}: {value_text(item)}" for key, item in value.items())
    return str(value).replace("\n", " ").replace("|", "\\|")


def placement_text(item: Mapping[str, Any]) -> str:
    placement = item["placement"]
    return (
        f"{grade_name(placement)}；{placement.get('section', '-')}；第{placement.get('page', '-')}页；"
        f"{placement.get('edition', '-')}"
    )


def sources_text(item: Mapping[str, Any]) -> str:
    return shared.source_links(item.get("sources") or []) or "-"


def render_readme(
    raid: str,
    manifest: Mapping[str, Any],
    card: Mapping[str, Any],
    route: Sequence[tuple[str, str, str, Mapping[str, Any]]],
    prompt_chars: int,
) -> str:
    lines = [
        f"# {manifest['title']['en']} (`{raid}`) — {manifest['title']['zh-CN']}\n",
        manifest["summary"]["en"] + "\n",
        "- Category: `learn`; rating: `6+`; tags: " + ", ".join(f"`{tag}`" for tag in manifest["tags"]) + "\n",
        f"""## Implementations

{shared.implementation_table(raid)}

Install an implementation into a RuntimeProfile with `raids install {raid} --impl <engine> --profile <file> --collection <name> --set model.<alias>=<model id> --set voice.<alias>=<voice id>`; the slots above are the parameters the installer asks for.

## Knowledge card

This single all-grades raid covers 统编版小学语文一至六年级. Its prompt embeds
checked proverbs, 歇后语, quotations, 对子/对联, and character stories from
语文园地·日积月累 and 识字课, about {prompt_chars} characters in total. Spoken
cards omit URLs, page numbers, and research notes. Exact duplicate spoken lines
are removed without changing the normalized research record.

[`knowledge.json`](knowledge.json) is the normalized source of truth and retains
all placement, source, dispute, work, note, 字源, and unverified fields from the
research input. {card['edition_note']}
""",
    ]
    table_specs = [
        ("谚语", "Text | Meaning | Placement | Sources", card["proverbs"], lambda x: f"{value_text(x['text'])} | {value_text(x['meaning'])}"),
        ("歇后语", "Front | Back | Meaning | Placement | Sources", card["xiehouyu"], lambda x: f"{value_text(x['front'])} | {value_text(x['back'])} | {value_text(x['meaning'])}"),
        ("名言", "Text | Textbook attribution | Work | Meaning | Dispute | Placement | Sources", card["quotes"], lambda x: f"{value_text(x['text'])} | {value_text(x['author'])} | {value_text(x.get('work'))} | {value_text(x['meaning'])} | {value_text(x.get('disputed'))}"),
        ("对子与对联", "Text | Type | Placement | Sources", card["couplets"], lambda x: f"{value_text(x['text'])} | {value_text(x.get('type'))}"),
        ("汉字小故事", "Character | Form | Ancient form | Story | Label | Placement | Sources", card["characters"], lambda x: f"{value_text(x['char'])} | {value_text(x.get('form'))} | {value_text(x['ancient_form'])} | {value_text(x.get('story'))} | {value_text(x.get('label'))}"),
    ]
    for heading, columns, items, fields in table_specs:
        lines.append(f"## {heading}\n")
        count = columns.count("|") + 1
        lines.append(f"| {columns} |\n| " + " | ".join(["---"] * count) + " |")
        for item in items:
            lines.append(f"| {fields(item)} | {placement_text(item)} | {sources_text(item)} |")

    lines.append("\n## Disputed quotations\n")
    lines.append("| Text | Child-friendly spoken note | Full research note | Sources |\n| --- | --- | --- | --- |")
    for item in card["quotes"]:
        if item.get("disputed"):
            lines.append(f"| {value_text(item['text'])} | {value_text(dispute_note(item))} | {value_text(item['disputed'])} | {sources_text(item)} |")

    lines.append("\n## Unverified / research limits\n")
    lines.append("| Item | Issue |\n| --- | --- |")
    for item in card["unverified"]:
        lines.append(f"| {value_text(item['item'])} | {value_text(item['issue'])} |")

    lines.append(f"""

## Testing

Tester: `test.yaml` (`{raid}-test`, eino), shared by every implementation:

- `tests/giztest/{raid}/eino.giztest.yaml` (relay, with reload, timeout 35m)
- `tests/giztest/{raid}/flowcraft.giztest.yaml` (relay, with reload, timeout 35m)
- `tests/giztest/{raid}/eino.realtime.giztest.yaml` (paced-audio RealTime roundtrip)
- `tests/giztest/{raid}/flowcraft.realtime.giztest.yaml` (paced-audio RealTime roundtrip)

The route has {len(route)} target responses and verifies the exact opening,
hint-before-answer barrier, gentle wrong-guess handling, explicit reveal,
disputed attribution, character description, and durable learning memory:

| # | Checkpoint | Player message | Contract |
| --- | --- | --- | --- |""")
    lines.extend(
        f"| {index} | `{checkpoint}` | {value_text(request)} | {value_text(contract)} |"
        for index, (checkpoint, request, contract, _) in enumerate(route, 1)
    )
    lines.append(f"\nRun:\n\n```sh\nmake test-e2e RAID={raid} PARALLEL=2\n```\n")
    return "\n".join(lines)


def generate(repo: Path, out: Path, raids: Sequence[str]) -> list[str]:
    if list(raids) != [RAID]:
        raise ValueError(f"unsupported Chinese words raids: {', '.join(raids)}")
    card = load_card(repo)
    body = card_text(card)
    flowcraft_prompt, eino_prompt = shared.learning_prompts(tutor_rules(), body, "")
    eino_prompt = eino_prompt.replace(
        "相关长期记忆只用于承接已确认的学习进度；",
        "相关长期记忆只用于承接已确认的年级、已学的内容和答题情况；",
        1,
    )
    route = route_for(card)
    manifest = shared.render_raid_manifest(
        repo,
        RAID,
        title={"zh-CN": "语文积累", "en": "Chinese Word Treasury"},
        summary={
            "zh-CN": "围绕统编版小学语文日积月累和识字课，猜谚语歇后语、讲名言出处和汉字来历，原文和出处都经过核对。",
            "en": "Explore verified primary Chinese textbook treasures through proverb and two-part-allegorical-saying riddles, quotation attributions, couplets, and character stories.",
        },
        tags=["learn", "chinese", "proverbs", "characters", "curriculum", "facts"],
        route=route,
        voice_description="Chinese tutor voice",
    )
    workflow_dir = out / "workflows" / RAID
    shared.write_text(workflow_dir / "flowcraft.yaml", shared.render_flowcraft(repo, RAID, flowcraft_prompt))
    shared.write_text(
        workflow_dir / "eino.yaml",
        shared.render_eino(
            repo,
            RAID,
            eino_prompt,
            "孩子的年级、已学的内容、答题情况、更正和明确要求记住的信息",
        ),
    )
    shared.write_text(workflow_dir / "test.yaml", shared.render_tester(repo, RAID, route, tester_rules(RAID, card), body))
    shared.write_json(workflow_dir / "raid.json", manifest)
    shared.write_json(workflow_dir / "knowledge.json", card)
    shared.write_text(workflow_dir / "README.md", render_readme(RAID, manifest, card, route, len(flowcraft_prompt)))
    for filename, text in shared.render_giztests(repo, RAID, len(route), "对韵歌", "我二年级，我们来猜谚语吧。").items():
        shared.write_text(out / "tests" / "giztest" / RAID / filename, text)
    return [
        f"{RAID}: {sum(len(card[key]) for key in CATEGORIES[:-1])} entries, "
        f"card chars {len(body)}, prompt chars {len(flowcraft_prompt)}"
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description="Normalize the verified Chinese words research JSON.")
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    raw = json.loads(shared.read_text(args.source))
    shared.write_json(args.destination, normalize_card(raw))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
