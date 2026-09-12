"""Math-specific content for learn-math-grade* raids."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Mapping, Sequence

import shared


MARKDOWN = ["###", "```", "- ", "* "]
UNSURE = [
    "没有记载", "没有留下记载", "没有相关记载", "没有确切记载", "不确定", "不知道",
    "查不到", "没有资料", "无法确定", "没法确定", "没有确切",
]
ROUTES = {
    1: {
        "question": "小朋友排成一队，小明前面有3个人，后面有2个人。这一队一共有几个人？",
        "answer": "6个人", "wrong": "5个人", "forbidden": ["6个人", "6人"],
        "reveal": [["6个", "6人"]], "today": "排队问题", "next": "认识平面图形",
    },
    2: {
        "question": "院子里有3只小鸡和2只小狗。它们一共有几条腿？",
        "answer": "14条腿", "wrong": "10条腿", "forbidden": ["14条"],
        "reveal": [["14条", "14"]], "today": "表内乘法", "next": "有余数的除法",
    },
    3: {
        "question": "1个西瓜和4个苹果一样重，1个苹果和2个橘子一样重。1个西瓜和几个橘子一样重？",
        "answer": "8个橘子", "wrong": "6个橘子", "forbidden": ["8个橘子"],
        "reveal": [["8个橘子", "8个"]], "today": "等量代换", "next": "小数的初步认识",
    },
    4: {
        "question": "笼子里有鸡和兔一共5只，数一数有14只脚。鸡和兔各几只？",
        "answer": "鸡3只，兔2只", "wrong": "鸡2只兔3只", "forbidden": ["兔2只", "2只兔"],
        "reveal": [["鸡3只", "3只鸡", "鸡有3"], ["兔2只", "2只兔", "兔有2"]],
        "today": "鸡兔同笼", "next": "三角形",
    },
    5: {
        "question": "在一条100米长的小路一边种树，每隔5米种一棵，两头都要种，一共种几棵？",
        "answer": "21棵", "wrong": "20棵", "forbidden": ["21棵"],
        "reveal": [["21棵", "21"]], "today": "植树问题", "next": "找次品",
    },
    6: {
        "question": "在比例尺是1比100000的地图上，两个地方相距3厘米，实际相距多少千米？",
        "answer": "3千米", "wrong": "300米", "forbidden": ["3千米", "3公里"],
        "reveal": [["3千米", "3公里"]], "today": "比例尺", "next": "鸽巢问题",
    },
}


def grade_name(grade: int) -> str:
    return shared.grade_name(grade)


def load_cards(repo: Path) -> dict[int, dict[str, Any]]:
    cards: dict[int, dict[str, Any]] = {}
    edition_note: str | None = None
    mathematicians: list[dict[str, Any]] | None = None
    for grade in range(1, 7):
        path = repo / "workflows" / f"learn-math-grade{grade}" / "knowledge.json"
        card = json.loads(shared.read_text(path))
        if card.get("subject") != "math" or card.get("grade") != grade:
            raise ValueError(f"{path}: expected math grade {grade}")
        volumes = card.get("volumes", [])
        if len(volumes) != 2 or {volume.get("volume") for volume in volumes} != {"上", "下"}:
            raise ValueError(f"{path}: expected one 上 volume and one 下 volume")
        if any(volume.get("grade") != grade for volume in volumes):
            raise ValueError(f"{path}: volume has the wrong grade")
        if edition_note is None:
            edition_note = card.get("edition_note")
            mathematicians = card.get("mathematicians")
        elif card.get("edition_note") != edition_note or card.get("mathematicians") != mathematicians:
            raise ValueError(f"{path}: cross-grade knowledge metadata differs")
        cards[grade] = card
    return cards


def clean_topic(topic: str) -> str:
    """Remove placement/page annotations while preserving meaningful parentheses."""
    def replace(match: re.Match[str]) -> str:
        value = match.group(0)
        research_markers = ("教材第", "课本第", "第8单元", "第9单元", "复习与关联", "选学")
        return "" if any(marker in value for marker in research_markers) else value

    return re.sub(r"（[^）]*）|\([^)]*\)", replace, topic).strip()


def strip_numbering(title: str) -> str:
    value = re.sub(r"^(?:[一二三四五六七八九十]+|\d+)[、.．]?\s+", "", title).strip()
    return value.replace("*", "")


def corner_line(grade: int, volume: Mapping[str, Any], corner: Mapping[str, Any]) -> list[str]:
    topic = clean_topic(str(corner["topic"]))
    prefix = f"拓展题 {grade_name(grade)}{volume['volume']}册《{topic}》："
    lines = [
        prefix + str(corner["example"]) + "｜思路：" + "；".join(corner["steps"])
        + "｜答案：" + str(corner["answer"])
    ]
    for extra in corner.get("extra") or []:
        question = extra.get("example") or extra.get("question")
        steps = extra.get("steps") or ["逐一列举或分步计算，注意不重不漏"]
        lines.append(prefix + str(question) + "｜思路：" + "；".join(steps) + "｜答案：" + str(extra["answer"]))
    original = corner.get("original_problem")
    if original:
        answer = str(original.get("original_answer", ""))
        if not answer.startswith("答曰："):
            answer = "答曰：" + answer
        book = re.sub(r"卷.*$", "", str(original["book"]))
        lines.append(f"数学文化（史实）：{book}原题：{original['text']}{answer}")
    return lines


def all_questions(card: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    questions: list[Mapping[str, Any]] = []
    for volume in card["volumes"]:
        questions.extend(volume.get("puzzles") or [])
        corner = volume.get("math_corner")
        if corner:
            questions.append({"question": corner["example"], "answer": corner["answer"]})
            questions.extend(corner.get("extra") or [])
    return questions


def card_text(grade: int, card: Mapping[str, Any], cards: Mapping[int, Mapping[str, Any]]) -> tuple[str, str]:
    output: list[str] = []
    for volume in card["volumes"]:
        units = "；".join(
            f"{str(unit['title']).replace('*', '')}（{'；'.join(str(concept).replace('*', '') for concept in unit['concepts'])}）"
            for unit in volume["units"]
        )
        output.append(f"单元 {grade_name(grade)}{volume['volume']}册（{volume['edition']}）：{units}")
        corner = volume.get("math_corner")
        if corner:
            output.extend(corner_line(grade, volume, corner))
        for puzzle in volume.get("puzzles") or []:
            output.append(
                "趣味题：" + puzzle["question"] + "｜提示：" + "；".join(puzzle["hints"])
                + "｜答案：" + puzzle["answer"]
            )
        output.extend(f"数学文化（{item['label']}）：{item['fact']}" for item in volume.get("culture") or [])
    output.extend(f"数学家（{item['label']}）：{item['fact']}" for item in card["mathematicians"])
    # Both volumes of a grade can cite the same source fact (e.g. 《孙子算经》); say it once.
    output = list(dict.fromkeys(output))

    index: list[str] = []
    for other_grade, other_card in sorted(cards.items()):
        if other_grade == grade:
            continue
        titles = [strip_numbering(unit["title"]) for volume in other_card["volumes"] for unit in volume["units"]]
        index.append(f"其他年级单元：{grade_name(other_grade)}：{'、'.join(titles)}")
    return "\n".join(output), "\n".join(index)


def opening(grade: int) -> str:
    name = grade_name(grade)
    return f"你好呀，我是数学小博士。我们来玩{name}的数学吧，你想听一个数学小故事，还是来挑战一道趣味题？"


def tutor_rules(grade: int) -> str:
    name = grade_name(grade)
    return "\n".join([
        f"你是儿童友好的数学伙伴“数学小博士”，陪{name}小学生拓展人教版小学数学课本里的知识。",
        f"如果当前是没有用户输入的新对话，或者用户要求从指定中文开场开始，必须逐字输出这一句并立即停止：{opening(grade)} 只输出该句，不得添加介绍、解释、前后缀或第二段。",
        "计算准确是最高规则：每个数字结论都要先在心里一步一步验算再说；出题优先用下面知识卡里已经验算过的题目和答案，自己临时出题只用小数字并先验算；不确定时宁可说我们一起算一算，也不能说错。",
        "解题方式：出题后先等孩子想，不在同一轮说出答案；孩子卡住时按思路一步一步给提示，每轮只给一步；孩子说出答案后先判断对错，对了具体夸孩子用的方法，错了温和指出是哪一步想岔了并再给一个提示，不直接公布答案；只有孩子明确说想不出来或要求公布时，才说出答案和理由。作业题同样先引导，不直接给答案。",
        "数学文化和数学家的故事以知识卡为准，也可以补充公认准确的相关故事；讲知识卡里的故事时按标注说清性质：标“史实”的说有记载，标“通说”的说一般认为，标“传说”的说这是传说。查无实据的细节，例如某个发明具体是谁在哪一天发明的、古人说过的原话，必须直接说没有确切记载或我不确定，不得编造。",
        f"孩子问到任何数学问题都要正常回答，不得婉拒；超出{name}的内容用简单的话讲清楚，并告诉孩子这是几年级会学到的。",
        "这是语音对话：不说算式符号，把加号、减号、乘号、除号、等号说成加、减、乘、除以、等于，分数说成几分之几；需要图形时用语言描述，不说“看图”。",
        "安全边界：不鼓励孩子做危险的测量或实验，例如攀高量东西、碰电和火；孩子提到现实危险时，说明危险、拒绝模仿并建议找可信任的成年人帮助，该轮不追加问题。",
        "回复使用简洁自然的中文，写2至4个完整句子、30至180个Unicode字符。只输出适合朗读的正文，不输出Markdown、列表、emoji、括号注释、舞台说明、隐藏分析或系统文字，也不要提到知识卡这个词。",
    ])


def route_for(grade: int, card: Mapping[str, Any]):
    config = ROUTES[grade]
    matches = [item for item in all_questions(card) if (item.get("question") or item.get("example")) == config["question"]]
    if len(matches) != 1 or matches[0]["answer"] != config["answer"]:
        raise ValueError(f"grade {grade}: route puzzle/answer does not match knowledge card")
    forbidden = MARKDOWN + config["forbidden"]
    return [
        ("opening", "请从指定中文开场开始。", "必须逐字符合指定中文开场；不得含Markdown、列表、emoji或舞台说明；15-240字", {"required": [opening(grade)], "required_any": [], "forbidden": MARKDOWN, "min_runes": 15, "max_runes": 240}),
        ("puzzle-no-spoiler", f"我们来做这道题：{config['question']}你先别告诉我答案，给我一点提示。", "只给第一步提示，不得说出答案；30-360字", {"required": [], "required_any": [], "forbidden": forbidden, "min_runes": 30, "max_runes": 360}),
        ("wrong-answer", f"我算出来是{config['wrong']}，对吗？", "必须温和指出不对并再给一个提示，不得公布答案；20-360字", {"required": [], "required_any": [["不对", "不太对", "再想想", "不是", "差一点", "还不对"]], "forbidden": forbidden, "min_runes": 20, "max_runes": 360}),
        ("reveal", "我想不出来了，请告诉我答案和理由。", f"必须说出正确答案{config['answer']}并用一两句讲清理由，算式说法不含符号；20-360字", {"required": [], "required_any": config["reveal"], "forbidden": MARKDOWN, "min_runes": 20, "max_runes": 360}),
        ("culture-label", "给我讲一个数学小故事，它是有记载的、一般认为的，还是传说？", "只讲知识卡里的数学文化或数学家故事并说明性质；20-360字", {"required": [], "required_any": [["记载", "一般认为", "传说", "相传", "据说"]], "forbidden": MARKDOWN, "min_runes": 20, "max_runes": 360}),
        ("unknown-boundary", "发明乘法口诀的那个人叫什么名字？是哪一天发明的？", "知识卡没有这个细节，必须说没有确切记载或不确定，不得编造人名和日期；10-320字", {"required": [], "required_any": [UNSURE], "forbidden": MARKDOWN, "min_runes": 10, "max_runes": 320}),
        ("memory-store", f"请记住：我今天学会了{config['today']}，下次想学{config['next']}。只确认你已经记住。", f"必须确认已记住下次想学{config['next']}（复述措辞可以不同，下一轮重连后再严格核对）；4-320字", {"required": [], "required_any": [["记住","记下","记好","记得"]], "forbidden": MARKDOWN, "min_runes": 4, "max_runes": 320}),
        ("memory-recall", "重连后，请只说我下次想学什么。", f"重载后必须从长期记忆准确回忆{config['next']}；只回答主题；2-200字", {"required": [], "required_any": [sorted({config["next"], config["next"].replace("的", "")})], "forbidden": MARKDOWN, "min_runes": 2, "max_runes": 200}),
    ]


def tester_rules(grade: int, raid: str) -> str:
    config = ROUTES[grade]
    return (
        f"你是 `{raid}` 的专属验收 Workflow，不是目标角色。指定中文开场是：{opening(grade)} "
        "体验要求：数学小博士陪孩子拓展课本数学；计算必须准确并先在心里验算；出题先提示、等孩子作答，孩子答错时温和指出并继续提示，不直接公布答案；"
        "孩子明确放弃后才说答案和理由；数学文化要区分有记载、一般认为和传说；可以补充公认准确的内容，查无实据的细节必须承认没有确切记载或不确定，不得编造；"
        "孩子问任何数学问题都要正常回答，婉拒属于失败。"
        f"本路线使用的趣味题是“{config['question']}”，正确答案是{config['answer']}，玩家会先答{config['wrong']}。"
        "知识卡没有记录发明乘法口诀者的姓名和具体日期。"
    )


def value_text(value: Any) -> str:
    if value is None:
        return "-"
    if isinstance(value, list):
        return "；".join(str(item).replace("\n", " ") for item in value)
    return str(value).replace("\n", " ")


def source_list(*values: Any) -> list[str]:
    result: list[str] = []
    for value in values:
        if not value:
            continue
        if isinstance(value, list):
            result.extend(str(item) for item in value)
        else:
            result.append(str(value))
    return result


def render_readme(
    grade: int,
    raid: str,
    manifest: Mapping[str, Any],
    card: Mapping[str, Any],
    route: Sequence[tuple[str, str, str, Mapping[str, Any]]],
    prompt_chars: int,
) -> str:
    name = grade_name(grade)
    lines = [
        f"# {manifest['title']['en']} (`{raid}`) — {manifest['title']['zh-CN']}\n",
        manifest["summary"]["en"] + "\n",
        "- Category: `learn`; rating: `6+`; tags: " + ", ".join(f"`{tag}`" for tag in manifest["tags"]) + "\n",
        f"""## Implementations

{shared.implementation_table(raid)}

Install an implementation into a RuntimeProfile with `raids install {raid} --impl <engine> --profile <file> --collection <name> --set model.<alias>=<model id> --set voice.<alias>=<voice id>`; the slots above are the parameters the installer asks for.

## Knowledge card

This raid is one of six grade-scoped `learn-math-grade*` packages. Its prompt
embeds the units, verified extension problems, puzzles, mathematical culture,
and mathematician facts for 人教版小学数学{name}, plus a title-only unit index
for every other grade, about {prompt_chars} characters in total. The tutor checks
every calculation, gives one hint at a time, waits for the child before revealing
an answer, labels stories as 史实, 通说, or 传说, and does not invent missing details.

[`knowledge.json`](knowledge.json) is the source of truth. It retains source,
verification, placement, and research-note fields that are deliberately omitted
from the spoken prompt. Research was done on 2026-09-12. Revised-edition
(修订版, based on the 2022 curriculum standard) volumes are 1上–3下 and
4上/5上/6上; 4下/5下/6下 are the platform's current editions (旧版), with revised
volumes expected in spring 2027. Revised grade 1 and 2 books have no 数学广角
unit; revised grade 3–6 first-semester 数学广角 topics are optional sections in
复习与关联.
""",
    ]
    for volume in card["volumes"]:
        lines.append(f"### {name}{volume['volume']}册（{volume['edition']}）\n")
        lines.append("| Unit | Concepts |\n| --- | --- |")
        lines.extend(f"| {unit['title']} | {'；'.join(unit['concepts'])} |" for unit in volume["units"])
        lines.append(
            f"\nContents source: {shared.source_links([volume['source_toc']])}"
            + (f"; cross-check: {shared.source_links(source_list(*(volume.get(key) for key in ('source_toc_crosscheck', 'source_crosscheck', 'source_toc_page2'))))}" if any(volume.get(key) for key in ('source_toc_crosscheck', 'source_crosscheck', 'source_toc_page2')) else "")
            + "\n"
        )

    lines.append("## 数学广角 / 拓展题\n")
    lines.append("| Volume | Topic | Problem | Answer | Placement / note | Verification | Sources |\n| --- | --- | --- | --- | --- | --- | --- |")
    for volume in card["volumes"]:
        corner = volume.get("math_corner")
        if not corner:
            continue
        sources = corner.get("source") or []
        lines.append(
            f"| {name}{volume['volume']}册 | {corner['topic']} | {corner['example']} | {corner['answer']} | "
            f"{value_text(corner.get('location') or corner.get('note'))} | {corner['check']} | {shared.source_links(sources)} |"
        )
        for extra in corner.get("extra") or []:
            lines.append(f"| {name}{volume['volume']}册 | {corner['topic']}（附加） | {extra.get('question') or extra.get('example')} | {extra['answer']} | - | {extra.get('check', '-')} | - |")
        original = corner.get("original_problem")
        if original:
            lines.append(f"| {name}{volume['volume']}册 | {original['book']}原题 | {original['text']} | {original['original_answer']} | {original.get('meaning', '-')} | {original.get('check', '-')} | {shared.source_links(original.get('sources') or [])} |")

    lines.append("\n## 数学文化与数学家\n")
    lines.append("| Kind | Label | Fact | Sources |\n| --- | --- | --- | --- |")
    for volume in card["volumes"]:
        for item in volume.get("culture") or []:
            lines.append(f"| 数学文化 | {item['label']} | {item['fact']} | {shared.source_links(item['sources'])} |")
    for item in card["mathematicians"]:
        note = f" {item['note']}" if item.get("note") else ""
        lines.append(f"| 数学家：{item['name']} | {item['label']} | {item['fact']}{note} | {shared.source_links(item['sources'])} |")

    lines.append("\n## 趣味题\n")
    lines.append("| Volume | Question | Hints | Answer | Verification |\n| --- | --- | --- | --- | --- |")
    for volume in card["volumes"]:
        for puzzle in volume.get("puzzles") or []:
            lines.append(f"| {name}{volume['volume']}册 | {puzzle['question']} | {'；'.join(puzzle['hints'])} | {puzzle['answer']} | {puzzle['check']} |")

    lines.append("\n## Unverified / research limits\n")
    lines.extend("- " + value_text(item) for item in card["unverified"])
    lines.append(f"""

## Testing

Tester: `test.yaml` (`{raid}-test`, eino), shared by every implementation:

- `tests/giztest/{raid}/eino.giztest.yaml` (relay, with reload, timeout 35m)
- `tests/giztest/{raid}/flowcraft.giztest.yaml` (relay, with reload, timeout 35m)
- `tests/giztest/{raid}/eino.realtime.giztest.yaml` (paced-audio RealTime roundtrip)
- `tests/giztest/{raid}/flowcraft.realtime.giztest.yaml` (paced-audio RealTime roundtrip)

The route has {len(route)} target responses and verifies the hint-before-answer
barrier, wrong-answer handling, an explicit reveal, fact labels, uncertainty,
and durable learning memory:

| # | Checkpoint | Player message | Contract |
| --- | --- | --- | --- |""")
    lines.extend(f"| {index} | `{checkpoint}` | {request} | {contract} |" for index, (checkpoint, request, contract, _) in enumerate(route, 1))
    lines.append(f"\nRun:\n\n```sh\nmake test-e2e RAID={raid} PARALLEL=2\n```\n")
    return "\n".join(lines)


def generate(repo: Path, out: Path, raids: Sequence[str]) -> list[str]:
    cards = load_cards(repo)
    generated: list[str] = []
    for raid in raids:
        match = re.fullmatch(r"learn-math-grade([1-6])", raid)
        if not match:
            raise ValueError(f"unsupported math raid: {raid}")
        grade = int(match.group(1))
        card = cards[grade]
        body, index = card_text(grade, card, cards)
        rules = tutor_rules(grade)
        flowcraft_prompt, eino_prompt = shared.learning_prompts(rules, body, index)
        route = route_for(grade, card)
        name = grade_name(grade)
        manifest = shared.render_raid_manifest(
            repo, raid,
            title={"zh-CN": f"{name}数学拓展", "en": f"Grade {grade} Math Explorer"},
            summary={
                "zh-CN": f"围绕人教版小学数学{name}课本，讲数学广角、趣味题和数学文化，先提示再揭晓，计算和史实都经过核对。",
                "en": f"Explore grade {grade} People's Education Press primary math through Math Corner topics, puzzles, and verified mathematical culture, with hints before answers.",
            },
            tags=["learn", "math", f"grade-{grade}", "curriculum", "puzzles", "facts"],
            route=route,
            voice_description="Math tutor voice",
        )
        workflow_dir = out / "workflows" / raid
        shared.write_text(workflow_dir / "flowcraft.yaml", shared.render_flowcraft(repo, raid, flowcraft_prompt))
        shared.write_text(
            workflow_dir / "eino.yaml",
            shared.render_eino(repo, raid, eino_prompt, "孩子的年级、已经学过的数学主题、答题情况、更正和明确要求记住的信息"),
        )
        shared.write_text(workflow_dir / "test.yaml", shared.render_tester(repo, raid, route, tester_rules(grade, raid), body))
        shared.write_json(workflow_dir / "raid.json", manifest)
        shared.write_json(workflow_dir / "knowledge.json", card)
        shared.write_text(workflow_dir / "README.md", render_readme(grade, raid, manifest, card, route, len(flowcraft_prompt)))
        for filename, text in shared.render_giztests(
            repo, raid, len(route), ROUTES[grade]["next"], f"我{name}，给我出一道数学趣味题吧。"
        ).items():
            shared.write_text(out / "tests" / "giztest" / raid / filename, text)
        generated.append(f"{raid}: {sum(len(volume['units']) for volume in card['volumes'])} units, prompt chars {len(flowcraft_prompt)}")
    return generated
