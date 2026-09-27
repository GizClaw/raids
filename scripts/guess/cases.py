#!/usr/bin/env python3
"""Run offline Starlark scenarios against every guess-* control script.

The cases replay spoken History the way GizClaw hands it to Eino and check the
route, the card node the script activates, and the host instruction.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))

import generate  # noqa: E402

RUNNER = generate.repository_root() / "scripts" / "test" / "test-starlark-routing.sh"


def user(text: str) -> dict[str, str]:
    return {"role": "user", "content": text}


def host(text: str) -> dict[str, str]:
    return {"role": "assistant", "content": text}


def node(data: dict[str, Any], level: int, puzzle: int) -> str:
    size = len(data["levels"][level - 1]["items"])
    return generate.card_node_id(level, (puzzle - 1) * generate.level_step(size) % size)


def title(data: dict[str, Any], level: int, lang: str = "zh") -> str:
    return data["levels"][level - 1]["title"][lang]


def opening(data: dict[str, Any], level: int, puzzle: int) -> str:
    return f"谜题来啦！第 {level} 关“{title(data, level)}”，第 {puzzle} 题。我心里已经藏好了{data['subject_zh']}，你的第一个问题是什么？"


def case(case_id: str, text: str, messages: list[dict[str, str]], expect: dict[str, Any]) -> dict[str, Any]:
    # GizClaw appends the current user text to input.messages.
    return {"ID": case_id, "Input": {"text": text, "messages": messages + [user(text)]}, "Expect": expect}


def control_cases(data: dict[str, Any]) -> list[dict[str, Any]]:
    s1, s2 = generate.secret(data, 1, 1), generate.secret(data, 2, 2)
    s3 = generate.secret(data, 2, 3)
    top = len(data["levels"])
    top_secret = generate.secret(data, top, 7)
    round1 = [user("开始"), host(opening(data, 1, 1))]
    won = round1 + [user(f"是{s1['zh']}吗？"), host(f"猜对啦！答案就是{s1['zh']}！恭喜你升到第 2 关，获得“{title(data, 2)}”称号！准备好了吗？")]
    round2 = won + [user("好的，下一题！"), host(opening(data, 2, 2))]
    lost = round2 + [user("我放弃"), host(f"没关系，答案揭晓：{s2['zh']}！还在第 2 关，要不要再来一题？")]
    noes = round1 + [item for pair in [[user(f"问题{i}？"), host("不是。你的下一个问题是什么？")] for i in range(5)] for item in pair]
    hinted = round1 + [user("给我提示"), host("小提示：这是一个提示。还想问什么？"), user("问题？"), host("不是。继续问吧？")]
    return [
        case("fresh-start", "开始", [], {"route": {"equals": "open"}, "direction": {"includes_all": [
            "【回复语言：中文】", f"谜题来啦！第 1 关“{title(data, 1)}”，第 1 题。", "你有 20 次提问机会"]}}),
        case("fresh-english", "Let's play!", [], {"route": {"equals": "open"}, "direction": {"includes_all": [
            "English", f"Puzzle time! Level 1, {title(data, 1, 'en')}, puzzle 1."]}}),
        case("smoke-opening", "请从指定中文开场开始。", [], {"route": {"equals": "open"}, "direction": {"includes_all": ["第 1 关", "第 1 题"]}}),
        case("first-question", data["tests"]["first"]["yes"], round1, {"route": {"equals": "play"}, "node": {"equals": node(data, 1, 1)},
            "rules": {"includes_all": ["你不知道谜底的名字"]}, "direction": {"includes_all": ["【回复语言：中文】", "系统已经核对过", " / ".join(s1["hints"]), "你的下一个问题是什么？"]}}),
        case("hint-request", "给我一个提示吧", round1, {"route": {"equals": "say"}, "direction": {"includes_all": ["挑一条孩子还不知道的", " / ".join(s1["hints"])]}}),
        case("hint-skips-used", "再给我一个提示", round1 + [user("提示"), host("小提示：" + s1["hints"][0] + "。还想问什么？")],
             {"route": {"equals": "say"}, "direction": {"includes_all": [" / ".join(s1["hints"][1:])]}}),
        case("english-hints-advance", "Another hint please", round1 + [user("Give me a hint"), host("Hint 1: something translated. What's your next question?")],
             {"route": {"equals": "say"}, "direction": {"includes_all": ["“Hint 2: <this hint translated into English>, so", s1["hints"][1]]}}),
        case("english-third-hint", "One more hint", round1 + [user("hint"), host("Hint 1: one."), user("hint"), host("Hint 2: two.")],
             {"route": {"equals": "say"}, "direction": {"includes_all": ["“Hint 3: <this hint translated into English>, so", s1["hints"][2]]}}),
        case("mixed-language-hints", "Give me another hint", round1 + [user("hint"), host("Hint 1: one."), user("提示"), host("小提示：" + s1["hints"][2] + "。")],
             {"route": {"equals": "say"}, "direction": {"includes_all": ["“Hint 2: <this hint translated into English>, so", s1["hints"][1]]}}),
        case("last-hint", "提示", round1 + [user("提示"), host("小提示：" + s1["hints"][0] + "。"), user("提示"), host("小提示：" + s1["hints"][2] + "。")],
             {"route": {"equals": "say"}, "direction": {"includes_all": ["逐字说“小提示：" + s1["hints"][1] + "。"]}}),
        case("big-hint-request", data["tests"]["first"]["big_hint"], round1, {"route": {"equals": "say"}, "direction": {"includes_all": ["小提示：所选的那条", s1["hints"][0]]}}),
        case("correct-guess", data["tests"]["first"]["guess"], round1, {"route": {"equals": "say"}, "direction": {"includes_all": [
            f"逐字说出下面这一整段话，一字不改：“猜对啦！答案就是{s1['zh']}！{s1['profile']}恭喜你升到第 2 关，获得“{title(data, 2)}”称号！准备好挑战下一题了吗？”"]}}),
        case("alias-guess", f"我猜是{(s1['aliases'] or [s1['zh']])[0]}", round1, {"route": {"equals": "say"}, "direction": {"includes_all": [f"答案就是{s1['zh']}"]}}),
        case("english-guess", f"Is it {s1['en']}?", round1, {"route": {"equals": "say"}, "direction": {"includes_all": [
            f"You got it! The answer is {s1['en']}! Congratulations, you've reached Level 2: {title(data, 2, 'en')}! Ready for the next puzzle?"]}}),
        case("story-phrase-guess", f"是{s1['zh']}的故事吗？", round1, {"route": {"equals": "say"}, "direction": {"includes_all": [f"答案就是{s1['zh']}"]}}),
        case("measure-word-guess", f"是一个{s1['zh']}吗？", round1, {"route": {"equals": "say"}, "direction": {"includes_all": [f"答案就是{s1['zh']}"]}}),
        case("english-an-guess", f"Is it an {s1['en']}?", round1, {"route": {"equals": "say"}, "direction": {"includes_all": [f"The answer is {s1['en']}!"]}}),
        case("name-but-no-guess", f"它和{s1['zh']}有关系吗？", round1, {"route": {"equals": "play"}, "node": {"equals": node(data, 1, 1)}}),
        case("give-up", "我放弃", round1, {"route": {"equals": "say"}, "direction": {"includes_all": [f"没关系，答案揭晓：{s1['zh']}！", "第 1 关"]}}),
        case("english-give-up", "I give up.", round1, {"route": {"equals": "say"}, "direction": {"includes_all": [f"No worries! The answer is {s1['en']}!"]}}),
        case("chinese-numerals", "它是什么？", [user("开始"), host(f"谜题来啦！第一关“{title(data, 1)}”，第一题。你的第一个问题是什么？")],
             {"route": {"equals": "play"}, "node": {"equals": node(data, 1, 1)}}),
        case("english-question", "Is it big?", round1, {"route": {"equals": "play"}, "direction": {"includes_all": ["English", "start with “Yes” or “No”"]}}),
        case("after-win", "好的，下一题！", won, {"route": {"equals": "open"}, "direction": {"includes_all": [
            f"第 2 关“{title(data, 2)}”，第 2 题。我又想好了"]}}),
        case("follow-up-after-win", f"{s1['zh']}是哪个朝代的人呀？", won, {"route": {"equals": "follow"}, "node": {"equals": node(data, 1, 1)},
             "direction": {"includes_all": ["追问", "公认常识", "准备好挑战下一题了吗？"]}}),
        case("next-after-follow-up", "可以再来一题吗？", won + [user("是哪个朝代的？"), host("春秋时期。准备好下一题了吗？")],
             {"route": {"equals": "open"}, "direction": {"includes_all": [f"第 2 关“{title(data, 2)}”，第 2 题。"]}}),
        case("follow-ups-capped", "那他有几个学生？", won + [user("是哪个朝代的？"), host("春秋时期。准备好了吗？"), user("他住在哪？"), host("鲁国。准备好了吗？")],
             {"route": {"equals": "open"}, "direction": {"includes_all": ["第 2 题。"]}}),
        case("level-two-secret", "问题？", round2, {"route": {"equals": "play"}, "node": {"equals": node(data, 2, 2)}}),
        case("level-two-guess", f"是{s2['zh']}吗？", round2, {"route": {"equals": "say"}, "direction": {"includes_all": [f"答案就是{s2['zh']}", "第 3 关"]}}),
        case("after-give-up-resume", "继续上次的内容", lost, {"route": {"equals": "open"}, "direction": {"includes_all": [
            f"第 2 关“{title(data, 2)}”，第 3 题。"]}}),
        case("level-two-third-secret", "问题？", lost + [user("继续上次的内容"), host(opening(data, 2, 3))],
             {"route": {"equals": "play"}, "node": {"equals": node(data, 2, 3)}}),
        case("restart", "从头开始", round2, {"route": {"equals": "open"}, "direction": {"includes_all": [f"第 1 关“{title(data, 1)}”，第 3 题。"]}}),
        case("start-before-asking", "开始", round1, {"route": {"equals": "say"}, "direction": {"includes_all": ["我们已经开始啦"]}}),
        case("start-mid-round", "开始", round1 + [user("问题？"), host("不是。还想问什么？")],
             {"route": {"equals": "open"}, "direction": {"includes_all": [f"第 1 关“{title(data, 1)}”，第 2 题。"]}}),
        case("resume-mid-round", "继续上次的内容", round1 + [user("问题？"), host("是。还想问什么？")],
             {"route": {"equals": "say"}, "direction": {"includes_all": ["你已经问了 1 次，还剩 19 次机会"]}}),
        case("stop-between-rounds", "不玩了", lost, {"route": {"equals": "say"}, "direction": {"includes_all": [f"第 2 关“{title(data, 2)}”", "下次说“开始”"]}}),
        case("decline-between-rounds", "不要", lost, {"route": {"equals": "say"}}),
        case("stop-mid-round", "我不玩了", round1 + [user("问题？"), host("是。还想问什么？")],
             {"route": {"equals": "say"}, "direction": {"includes_all": ["继续上次的内容"]}}),
        case("no-streak", "问题？", noes, {"route": {"equals": "play"}, "direction": {"includes_all": ["如果这次的回答是“不是”，就在回答后面逐字加一句“小提示：" + s1["hints"][0]]}}),
        case("hint-count", "问题？", hinted, {"route": {"equals": "play"}, "direction": {"includes_all": [" / ".join(s1["hints"])]}}),
        case("hints-used-up", "再给个提示", hinted + [user("提示"), host("小提示：二。还想问什么？"), user("提示"), host("小提示：三。还想问什么？")],
             {"route": {"equals": "say"}, "direction": {"includes_all": ["3 次提示已经用完了"]}}),
        case("hints-used-up-in-play", "他是男的吗？", hinted + [user("提示"), host("小提示：二。还想问什么？"), user("提示"), host("小提示：三。还想问什么？")],
             {"route": {"equals": "play"}, "direction": {"includes_all": ["3 次提示已经用完了"]}}),
        case("remaining-five", "问题？", round1 + [item for pair in [[user(f"问题{i}？"), host("是。还想问什么？")] for i in range(14)] for item in pair],
             {"route": {"equals": "play"}, "direction": {"includes_all": ["还剩 5 次提问机会"]}}),
        case("hints-keep-chances", "问题？", round1 + [item for pair in [[user(f"问题{i}？"), host("是。还想问什么？")] for i in range(18)] for item in pair]
             + [user("给我一个提示"), host("小提示：" + s1["hints"][0] + "。还想问什么？")],
             {"route": {"equals": "play"}, "direction": {"includes_all": ["还剩 1 次提问机会"]}}),
        case("answer-request-keeps-chances", "问题？", round1 + [user(data["tests"]["first"]["ask"]), host("想看答案可以说“我放弃”哦。你的下一个问题是什么？"), user("问题？"), host("是。还想问什么？")],
             {"route": {"equals": "play"}, "direction": {"includes_all": ["小提示："]}, "rules": {"includes_all": ["你不知道谜底的名字"]}}),
        case("resume-after-answer-request", "继续上次的内容", round1 + [user(data["tests"]["first"]["ask"]), host("想看答案可以说“我放弃”哦。"), user("问题？"), host("是。")],
             {"route": {"equals": "say"}, "direction": {"includes_all": ["你已经问了 1 次，还剩 19 次机会"]}}),
        case("last-question", "问题？", round1 + [item for pair in [[user(f"问题{i}？"), host("是。还想问什么？")] for i in range(19)] for item in pair],
             {"route": {"equals": "play"}, "direction": {"includes_all": [f"20 次机会用完啦，答案揭晓：{s1['zh']}！"]}}),
        case("top-level", "问题？", [user("开始"), host(opening(data, top, 7))],
             {"route": {"equals": "play"}, "node": {"equals": node(data, top, 7)}}),
        case("top-level-guess", top_secret["zh"], [user("开始"), host(opening(data, top, 7))],
             {"route": {"equals": "say"}, "direction": {"includes_all": [f"答案就是{top_secret['zh']}", f"你已经是最高的第 {top} 关"]}}),
        case("top-level-win-stays", "下一题", [user("开始"), host(opening(data, top, 7)), user("猜"), host(f"猜对啦！答案就是{top_secret['zh']}！太厉害了！")],
             {"route": {"equals": "open"}, "direction": {"includes_all": [f"第 {top} 关“{title(data, top)}”，第 8 题。"]}}),
    ]


def run_suite(label: str, source: str, cases: list[dict[str, Any]], steps: int) -> None:
    payload = json.dumps({"Source": source, "Steps": steps, "Cases": cases}, ensure_ascii=False)
    result = subprocess.run([str(RUNNER)], input=payload, text=True, capture_output=True)
    if result.returncode != 0:
        sys.stderr.write(result.stdout + result.stderr)
        raise SystemExit(f"{label}: Starlark scenario failed")
    print(f"{label}: {result.stdout.strip()}")


def main() -> int:
    repo = generate.repository_root()
    raids = sys.argv[1:] or generate.discover_raids(repo)
    for raid in raids:
        data = generate.load(repo, raid)
        control = generate.fill(generate.template("control.star"), {"RAID": raid, "DATA": generate.dumps(generate.starlark_data(data))})
        rendered = generate.render_eino(raid, data)
        total = sum(len(level["items"]) for level in data["levels"])
        nodes = rendered.count("\n      - id: card-l")
        routes = rendered.count("\n            field: game-node\n")
        if nodes != total or routes != total:
            raise SystemExit(f"{raid}: expected {total} card nodes and routes, found {nodes} nodes and {routes} routes")
        for level_number, level in enumerate(data["levels"], 1):
            for index, item in enumerate(level["items"]):
                body = generate.anonymous_body(item)
                leaked = [name for name in generate.names(item) if name and name in body]
                if leaked:
                    raise SystemExit(f"{raid}: card node for {item['zh']} still names {leaked}")
        print(f"{raid}: {total} card nodes, each with its own branch route and no name of its own answer")
        run_suite(f"{raid} control", control, control_cases(data), 300000)
    return 0


if __name__ == "__main__":
    sys.exit(main())
