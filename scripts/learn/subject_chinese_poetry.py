"""Poetry-specific content for learn-chinese-poetry-grade* raids."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Mapping, Sequence

import shared


NUM = "一二三四五六"
MARKDOWN = ["###", "```", "- ", "* "]
UNSURE = [
    "没有记载", "没有留下记载", "没有相关记载", "没有确切记载", "不确定", "不知道",
    "查不到", "没有资料", "无法确定", "没法确定", "没有确切",
]
LABEL_CUES = {
    "史实": ["记载", "原注", "注明", "写着"],
    "通说": ["一般认为", "一种说法", "有人认为", "据说", "通常认为", "大多认为", "说法"],
    "传说": ["传说", "相传"],
}
INTERNAL_REFERENCE = re.compile(r"古诗文网|维基|核对|百度|知乎|电子课本|第三方|据相关文章")
ROUTES = {
    1: ("静夜思", "小池", "登鹳雀楼"),
    2: ("登鹳雀楼", "村居", "咏鹅"),
    3: ("九月九日忆山东兄弟", "望天门山", "咏鹅"),
    4: ("题西林壁", "出塞", "静夜思"),
    5: ("示儿", "山居秋暝", "咏鹅"),
    6: ("六月二十七日望湖楼醉书", "泊船瓜洲", "静夜思"),
}


def where(placement: Mapping[str, Any]) -> str:
    volume = placement.get("volume") or ""
    result = NUM[placement["grade"] - 1] + "年级" + volume + ("册" if volume else "")
    if placement.get("section") and placement["section"] != "课文":
        result += "·" + placement["section"]
    return result


def grade_of(poem: Mapping[str, Any]) -> int | None:
    return (poem.get("placement") or {}).get("grade")


def spoken_variant(poem: Mapping[str, Any]) -> str | None:
    if "variant_spoken" not in poem:
        raise ValueError(f"{poem['title']}: missing variant_spoken")
    value = poem["variant_spoken"]
    if value is not None and not isinstance(value, str):
        raise ValueError(f"{poem['title']}: variant_spoken must be a string or null")
    if value and INTERNAL_REFERENCE.search(value):
        raise ValueError(f"{poem['title']}: variant_spoken contains an internal research reference")
    return value


def load_cards(repo: Path) -> tuple[dict[int, dict[str, Any]], list[dict[str, Any]]]:
    cards: dict[int, dict[str, Any]] = {}
    poems: list[dict[str, Any]] = []
    shared_keys = ("edition_note", "curriculum_standard", "general_facts", "unverified", "curriculum_75")
    baseline: dict[str, Any] | None = None
    for grade in range(1, 7):
        path = repo / "workflows" / f"learn-chinese-poetry-grade{grade}" / "knowledge.json"
        card = json.loads(shared.read_text(path))
        if card.get("grade") != grade:
            raise ValueError(f"{path}: expected grade {grade}")
        current = {key: card.get(key) for key in shared_keys}
        if baseline is None:
            baseline = current
        elif current != baseline:
            raise ValueError(f"{path}: cross-grade knowledge metadata differs")
        for poem in card.get("poems", []):
            if grade_of(poem) != grade:
                raise ValueError(f"{path}: {poem.get('title')} has the wrong grade")
            spoken_variant(poem)
            poems.append(poem)
        cards[grade] = card
    return cards, poems


def card_text(grade: int, card: Mapping[str, Any], all_poems: Sequence[Mapping[str, Any]]) -> tuple[str, str]:
    poems = card["poems"]
    output = ["常识：" + fact["fact"] for fact in card["general_facts"]]
    authors: dict[str, str] = {}
    for poem in poems:
        if poem["author_facts"] and poem["author"] not in authors:
            authors[poem["author"]] = poem["author_facts"][0]
    output.extend(f"作者 {author}：{fact}" for author, fact in authors.items())
    for poem in poems:
        variant = spoken_variant(poem)
        output.append(
            f"《{poem['title']}》{poem['dynasty']}·{poem['author']}｜{where(poem['placement'])}｜正文：{poem['text']}"
            f"｜背景（{poem['background_label']}）：{poem['background']}｜拓展：{poem['kid_hook']}"
            + (f"｜异文：{variant}" if variant else "")
        )
    others: dict[int, list[str]] = {}
    for poem in all_poems:
        other_grade = grade_of(poem)
        if other_grade and other_grade != grade:
            others.setdefault(other_grade, []).append(f"《{poem['title']}》{poem['author']}")
    index = [
        "其他年级诗目：" + NUM[other_grade - 1] + "年级：" + "、".join(titles)
        for other_grade, titles in sorted(others.items())
    ]
    return "\n".join(output), "\n".join(index)


def opening(grade: int) -> str:
    return f"你好呀，我是古诗小书童。我们来聊聊{NUM[grade - 1]}年级的古诗吧，说一首你学过的，我给你讲讲它背后的故事。"


def tutor_rules(grade: int) -> str:
    grade_name = NUM[grade - 1] + "年级"
    sections = "课文和语文园地·日积月累" + ("，以及古诗词诵读" if grade == 6 else "")
    return "\n".join([
        f"你是儿童友好的古诗讲解员“古诗小书童”，陪{grade_name}小学生拓展统编版小学语文课本里的古诗。",
        f"如果当前是没有用户输入的新对话，或者用户要求从指定中文开场开始，必须逐字输出这一句并立即停止：{opening(grade)} 只输出该句，不得添加介绍、解释、前后缀或第二段。",
        "知识边界是最高规则：诗的正文、作者、写作背景、年份数字和拓展知识优先来自下面的知识卡。念知识卡里的诗必须与知识卡正文逐字一致，不得改字、漏字、补字或换成其他版本；孩子问到异文时才说异文。",
        "知识卡里没有的细节，例如诗人某天住在哪里、吃了什么、说过什么话，或者知识卡以外的年份、地名、人名，必须直接说没有确切记载或我不确定，不得编造，也不得用“可能”“大概”去猜。",
        "讲背景时要按知识卡标注说清性质：标“史实”的说有记载，标“通说”的说一般认为或有一种说法，标“传说”的说这是传说。作者有争议时如实说有不同说法。",
        f"知识卡收了{grade_name}课本里的全部古诗，包括{sections}。孩子提到的任何诗都要正常陪孩子讲、陪孩子念，不得婉拒。其他年级的诗列在诗目表里，可以顺带告诉孩子这是几年级学的；这些诗只念你有把握逐字准确的正文，没把握就请孩子拿课本一起对照，背景只讲大家熟知的，拿不准的细节直接说不确定。",
        "教学方式：孩子说出诗名后，每轮只推进一步，依次是用一两句话讲作者或背景、念诗或请孩子一起念、问一个关于诗中画面或字词的问题、根据回答给反馈并补一个拓展知识、请孩子用一句话说说学到了什么。孩子直接要求念诗、提问或换诗时，优先照孩子的要求做。每轮最多问一个清楚的问题。孩子念错或答错时，先肯定再温和地说出正确的字句，不批评。作业题不直接给答案，先给提示。",
        "安全边界：不鼓励孩子模仿诗中饮酒、登高临水、夜里独自出行等现实危险行为；孩子提到现实危险时，说明危险、拒绝模仿并建议找可信任的成年人帮助，该轮不追加问题。",
        "回复使用简洁自然的中文，写2至4个完整句子、30至180个Unicode字符；念整首诗的那一轮可以只说题目、作者、正文和一句引导。只输出适合朗读的正文，不输出Markdown、列表、emoji、括号注释、舞台说明、隐藏分析或系统文字，也不要提到知识卡或诗目表这些词。",
    ])


def poem_lines(text: str) -> list[str]:
    return [line for line in re.split(r"[，。！？；]", text) if line]


def route_for(grade: int, by_title: Mapping[str, Mapping[str, Any]]):
    focus, next_poem, other = (by_title[title] for title in ROUTES[grade])
    other_grade = NUM[grade_of(other) - 1] + "年级"
    return [
        ("opening", "请从指定中文开场开始。", "必须逐字符合指定中文开场；不得含Markdown、列表、emoji或舞台说明；15-240字", {"required": [opening(grade)], "required_any": [], "forbidden": MARKDOWN, "min_runes": 15, "max_runes": 240}),
        ("poem-intro", f"我们刚学了《{focus['title']}》，你给我讲讲吧。", f"必须承接这首诗并正确说出作者{focus['author']}；只讲知识卡内的作者或背景；最多一个问题；30-360字", {"required": [focus["author"]], "required_any": [], "forbidden": MARKDOWN, "min_runes": 30, "max_runes": 360}),
        ("recite-exact", "你能把这首诗完整地念给我听吗？", f"必须逐字念出课本正文“{focus['text']}”，不得改字漏字；20-360字", {"required": poem_lines(focus["text"]), "required_any": [], "forbidden": MARKDOWN, "min_runes": 20, "max_runes": 360}),
        ("background-label", "这首诗是在什么情况下写的？是有记载的，还是一般认为的，还是传说？", f"必须按知识卡讲背景“{focus['background']}”，并说明它属于{focus['background_label']}；不得添加知识卡外的细节；20-360字", {"required": [], "required_any": [LABEL_CUES[focus["background_label"]]], "forbidden": MARKDOWN, "min_runes": 20, "max_runes": 360}),
        ("unknown-boundary", "诗人写这首诗那天中午吃的是什么？", "知识卡没有这个细节，必须明确说没有记载或不确定，不得编造食物、地名或人名，也不得用可能、大概去猜；10-320字", {"required": [], "required_any": [UNSURE], "forbidden": MARKDOWN, "min_runes": 10, "max_runes": 320}),
        ("other-grade-poem", f"我还会背《{other['title']}》，你能念给我听吗？", f"《{other['title']}》是{other_grade}的诗，必须正常念出全文“{other['text']}”，不得婉拒；20-360字", {"required": poem_lines(other["text"]), "required_any": [], "forbidden": MARKDOWN, "min_runes": 20, "max_runes": 360}),
        ("memory-store", f"请记住：我今天学会了《{focus['title']}》，下次想学《{next_poem['title']}》。只确认你已经记住。", f"必须确认已记住今天学会的诗和下次想学《{next_poem['title']}》；4-320字", {"required": [next_poem["title"]], "required_any": [], "forbidden": MARKDOWN, "min_runes": 4, "max_runes": 320}),
        ("memory-recall", "重连后，请只说我下次想学哪首诗。", f"重载后必须从长期记忆准确回忆《{next_poem['title']}》；只回答诗名；2-200字", {"required": [next_poem["title"]], "required_any": [], "forbidden": MARKDOWN, "min_runes": 2, "max_runes": 200}),
    ]


def tester_rules(grade: int, raid: str, by_title: Mapping[str, Mapping[str, Any]]) -> str:
    focus, next_poem, other = (by_title[title] for title in ROUTES[grade])
    return (
        f"你是 `{raid}` 的专属验收 Workflow，不是目标角色。指定中文开场是：{opening(grade)} "
        "体验要求：古诗小书童陪孩子拓展课本古诗，念知识卡里的诗必须与课本正文逐字一致；背景要区分有记载、一般认为和传说；"
        "知识卡没有的细节必须承认没有记载或不确定，不得编造；孩子提到的任何诗都要正常讲、正常念，婉拒属于失败。"
        f"本路线使用的知识卡条目：《{focus['title']}》{focus['dynasty']}·{focus['author']}，正文“{focus['text']}”，"
        f"背景（{focus['background_label']}）：{focus['background']}。"
        f"《{other['title']}》{other['dynasty']}·{other['author']}，正文“{other['text']}”。"
        f"《{next_poem['title']}》{next_poem['dynasty']}·{next_poem['author']}。知识卡没有记录诗人写诗那天吃了什么。"
    )


def render_readme(
    grade: int,
    raid: str,
    manifest: Mapping[str, Any],
    card: Mapping[str, Any],
    route: Sequence[tuple[str, str, str, Mapping[str, Any]]],
    prompt_chars: int,
) -> str:
    grade_name = NUM[grade - 1] + "年级"
    lines = [
        f"# {manifest['title']['en']} (`{raid}`) — {manifest['title']['zh-CN']}\n",
        manifest["summary"]["en"] + "\n",
        "- Category: `learn`; rating: `6+`; tags: " + ", ".join(f"`{tag}`" for tag in manifest["tags"]) + "\n",
        f"""## Implementations

{shared.implementation_table(raid)}

Install an implementation into a RuntimeProfile with `raids install {raid} --impl <engine> --profile <file> --collection <name> --set model.<alias>=<model id> --set voice.<alias>=<voice id>`; the slots above are the parameters the installer asks for.

## Knowledge card

This raid is one of six grade-scoped `learn-chinese-poetry-grade*` packages.
Its prompt embeds the full verified entries for every classical poem in 统编版
{grade_name} (课文, 语文园地·日积月累{', 古诗词诵读' if grade == 6 else ''}) plus a title index of
every other grade's poems, about {prompt_chars} characters in total. Any poem a child
mentions is taught and recited normally: in-grade poems are recited verbatim
from the card with their background labelled 有记载 (史实), 一般认为 (通说), or
传说; poems from other grades are recited only when the tutor is certain of
the text. Details the card does not hold get "没有确切记载 / 不确定" instead of
invented facts.

[`knowledge.json`](knowledge.json) is the source of truth for this grade's
card and records every source consulted; the Workflow prompts are rendered
from it. Research was done on 2026-09-12. Revised-edition (修订版) volumes
are 1上–3下 and 4上/5上/6上; 4下/5下/6下 use the current editions (旧版) until
the revised ones are published.

| Poem | Author | Placement | Background label | Sources |
| --- | --- | --- | --- | --- |""",
    ]
    for poem in card["poems"]:
        placement = poem["placement"]
        place = where(placement)
        if placement.get("unit_or_lesson"):
            place += " " + placement["unit_or_lesson"]
        if placement.get("edition"):
            place += f"（{placement['edition']}）"
        lines.append(
            f"| 《{poem['title']}》 | {poem['dynasty']}·{poem['author']} | {place} | "
            f"{poem['background_label']} | {shared.source_links(poem['sources'])} |"
        )
    lines.append("\nKnown gaps across the poetry card:\n")
    lines.extend("- " + str(gap).replace("\n", " ") for gap in card["unverified"])
    lines.append(f"""
## Testing

Tester: `test.yaml` (`{raid}-test`, eino), shared by every implementation:

- `tests/giztest/{raid}/eino.giztest.yaml` (relay, with reload, timeout 35m)
- `tests/giztest/{raid}/flowcraft.giztest.yaml` (relay, with reload, timeout 35m)
- `tests/giztest/{raid}/eino.realtime.giztest.yaml` (paced-audio RealTime roundtrip)
- `tests/giztest/{raid}/flowcraft.realtime.giztest.yaml` (paced-audio RealTime roundtrip)

The route has {len(route)} target responses; `recite-exact`, `background-label`, `unknown-boundary`, and `other-grade-poem` guard against hallucination and refusals:

| # | Checkpoint | Player message | Contract |
| --- | --- | --- | --- |""")
    lines.extend(f"| {index} | `{checkpoint}` | {request} | {contract} |" for index, (checkpoint, request, contract, _) in enumerate(route, 1))
    lines.append(f"\nRun:\n\n```sh\nmake test-e2e RAID={raid} PARALLEL=2\n```\n")
    return "\n".join(lines)


def generate(repo: Path, out: Path, raids: Sequence[str]) -> list[str]:
    cards, all_poems = load_cards(repo)
    by_title = {poem["title"]: poem for poem in all_poems}
    generated: list[str] = []
    for raid in raids:
        match = re.fullmatch(r"learn-chinese-poetry-grade([1-6])", raid)
        if not match:
            raise ValueError(f"unsupported Chinese poetry raid: {raid}")
        grade = int(match.group(1))
        card = cards[grade]
        body, index = card_text(grade, card, all_poems)
        rules = tutor_rules(grade)
        flowcraft_prompt = "\n".join([
            rules, "知识卡：", body, index,
            "可核对的长期学习进度：${board.scenario_memory}",
            "回复必须与上面已确认的学习进度一致，不得推翻孩子已确认的年级、已学的诗或孩子的更正。",
        ])
        eino_prompt = "\n".join([
            rules, "知识卡：", body, index, "",
            "相关长期记忆只用于承接已确认的学习进度；为空时忽略，不得让旧记忆覆盖孩子当前的更正：", "{memory}",
        ])
        route = route_for(grade, by_title)
        grade_name = NUM[grade - 1] + "年级"
        manifest = shared.render_raid_manifest(
            repo, raid,
            title={"zh-CN": f"{grade_name}古诗拓展", "en": f"Grade {grade} Classical Poetry"},
            summary={
                "zh-CN": f"围绕统编版小学语文{grade_name}课本里的古诗，讲作者、背景和拓展知识，只用核对过的资料。",
                "en": f"Explore every classical poem in China's grade {grade} primary Chinese textbooks — authors, backgrounds, and extensions — using verified facts.",
            },
            tags=["learn", "chinese", "poetry", f"grade-{grade}", "curriculum", "facts"],
            route=route,
            voice_description="Poetry tutor voice",
        )
        workflow_dir = out / "workflows" / raid
        shared.write_text(workflow_dir / "flowcraft.yaml", shared.render_flowcraft(repo, raid, flowcraft_prompt))
        shared.write_text(
            workflow_dir / "eino.yaml",
            shared.render_eino(
                repo,
                raid,
                eino_prompt,
                "孩子的年级、已经学过的古诗、答题情况、更正和明确要求记住的信息",
            ),
        )
        shared.write_text(workflow_dir / "test.yaml", shared.render_tester(repo, raid, route, tester_rules(grade, raid, by_title)))
        shared.write_json(workflow_dir / "raid.json", manifest)
        shared.write_json(workflow_dir / "knowledge.json", card)
        shared.write_text(workflow_dir / "README.md", render_readme(grade, raid, manifest, card, route, len(flowcraft_prompt)))
        realtime_text = f"我{NUM[grade - 1]}年级，给我讲讲《{by_title[ROUTES[grade][0]]['title']}》吧。"
        for name, text in shared.render_giztests(repo, raid, len(route), ROUTES[grade][1], realtime_text).items():
            shared.write_text(out / "tests" / "giztest" / raid / name, text)
        generated.append(f"{raid}: {len(card['poems'])} poems, prompt chars {len(flowcraft_prompt)}")
    return generated
