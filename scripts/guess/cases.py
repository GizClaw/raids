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
    scenarios = [
        case("fresh-start", "开始", [], {"route": {"equals": "open"}, "direction": {"includes_all": [
            "【回复语言：中文】", f"谜题来啦！第 1 关“{title(data, 1)}”，第 1 题。", "你有 20 次提问机会"]}}),
        case("fresh-english", "Let's play!", [], {"route": {"equals": "open"}, "direction": {"includes_all": [
            "English", f"Puzzle time! Level 1, {title(data, 1, 'en')}, puzzle 1."]}}),
        case("smoke-opening", "请从指定中文开场开始。", [], {"route": {"equals": "open"}, "direction": {"includes_all": ["第 1 关", "第 1 题"]}}),
        case("first-question", data["tests"]["first"]["yes"], round1, {"route": {"equals": "play"}, "node": {"equals": node(data, 1, 1)},
            "rules": {"includes_all": ["每题的谜底由系统在开题时选定", "不能为了保密而答错或假装不知道"]},
            "direction": {"includes_all": ["【回复语言：中文】", f"第 1 关，第 1 题：{s1['zh']} / {s1['en']}", "脚本没有匹配到的说法不等于猜错", " / ".join(s1["hints"]), "你的下一个问题是什么？"]}}),
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
        case("correct-guess", data["tests"]["first"]["guess"], round1, {"route": {"equals": "say"}, "node": {"equals": "read-winning-reply"}, "direction": {"includes_all": [
            f"逐字说出下面这一整段话，一字不改：“猜对啦！答案就是{s1['zh']}！{s1['profile']}恭喜你升到第 2 关，获得“{title(data, 2)}”称号！准备好挑战下一题了吗？”"]}}),
        case("alias-guess", f"我猜是{(s1['aliases'] or [s1['zh']])[0]}", round1, {"route": {"equals": "say"}, "direction": {"includes_all": [f"答案就是{s1['zh']}"]}}),
        case("english-guess", f"Is it {s1['en']}?", round1, {"route": {"equals": "say"}, "node": {"equals": "read-winning-reply"}, "direction": {"includes_all": [
            f"You got it! The answer is {s1['en']}! Congratulations, you've reached Level 2: {title(data, 2, 'en')}! Ready for the next puzzle?"]}}),
        case("story-phrase-guess", f"是{s1['zh']}的故事吗？", round1, {"route": {"equals": "say"}, "direction": {"includes_all": [f"答案就是{s1['zh']}"]}}),
        case("measure-word-guess", f"是一个{s1['zh']}吗？", round1, {"route": {"equals": "say"}, "direction": {"includes_all": [f"答案就是{s1['zh']}"]}}),
        case("english-an-guess", f"Is it an {s1['en']}?", round1, {"route": {"equals": "say"}, "direction": {"includes_all": [f"The answer is {s1['en']}!"]}}),
        case("is-it-guess", f"是不是{s1['zh']}？", round1, {"route": {"equals": "say"}, "direction": {"includes_all": [f"猜对啦！答案就是{s1['zh']}！"]}}),
        case("natural-guess", f"我想问是不是{s1['zh']}呀？", round1, {"route": {"equals": "say"}, "direction": {"includes_all": [f"猜对啦！答案就是{s1['zh']}！"]}}),
        case("thing-guess", f"这个东西是不是{s1['zh']}？", round1, {"route": {"equals": "say"}, "direction": {"includes_all": [f"答案就是{s1['zh']}"]}}),
        case("selected-guess", f"所以你选的是不是{s1['zh']}？", round1, {"route": {"equals": "say"}, "direction": {"includes_all": [f"答案就是{s1['zh']}"]}}),
        case("english-could-guess", f"Could it be {s1['en']}?", round1, {"route": {"equals": "say"}, "direction": {"includes_all": [f"The answer is {s1['en']}!"]}}),
        case("name-but-no-guess", f"它和{s1['zh']}有关系吗？", round1, {"route": {"equals": "play"}, "node": {"equals": node(data, 1, 1)}}),
        case("same-feature-not-a-guess", f"它是不是和{s1['zh']}一样大？", round1, {"route": {"equals": "play"}, "node": {"equals": node(data, 1, 1)}}),
        case("negated-name-not-a-guess", f"它不是{s1['zh']}对不对？", round1, {"route": {"equals": "play"}, "node": {"equals": node(data, 1, 1)}}),
        case("derived-object-not-a-guess", f"它是不是{s1['zh']}的模型？", round1, {"route": {"equals": "play"}, "node": {"equals": node(data, 1, 1)}}),
        case("guess-after-incorrect-answer", f"是不是{s1['zh']}", round1 + [user("它有没有氢元素？"), host("这个我也说不准。接下来你想问什么？")],
             {"route": {"equals": "say"}, "direction": {"includes_all": [f"猜对啦！答案就是{s1['zh']}！"]}}),
        case("answer-stays-fixed-after-wrong-rejection", "它是什么样的？", round1 + [user(f"是不是{s1['zh']}"), host("不是。你的下一个问题是什么？")],
             {"route": {"equals": "play"}, "node": {"equals": node(data, 1, 1)}, "direction": {"includes_all": [f"第 1 关，第 1 题：{s1['zh']} / {s1['en']}"]}}),
        case("give-up-keeps-the-same-answer", "我认输了", round1 + [user(f"是不是{s1['zh']}"), host("不是。你的下一个问题是什么？")],
             {"route": {"equals": "say"}, "direction": {"includes_all": [f"没关系，答案揭晓：{s1['zh']}！"]}}),
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
             {"route": {"equals": "play"}, "direction": {"includes_all": ["小提示："]}, "rules": {"includes_all": ["固定谜底只供你内部判断"]}}),
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
    if data["id"] == "guess-chemistry-terms":
        scenarios += [
            case("ice-hydrogen-keeps-answer", "它有没有氢元素？", round1,
                 {"route": {"equals": "play"}, "node": {"equals": node(data, 1, 1)},
                  "direction": {"includes_all": ["第 1 关，第 1 题：冰 / ice / 冰块", "公认常识", "不能为了保密故意答错或假装不知道"]}}),
            case("h106-homophone-guess", "是不是兵？", round1,
                 {"route": {"equals": "say"}, "node": {"equals": "read-winning-reply"}, "direction": {"includes_all": ["猜对啦！答案就是冰！"]}}),
            case("ice-salt-not-a-homophone", "是不是盐？", round1,
                 {"route": {"equals": "play"}, "node": {"equals": node(data, 1, 1)}}),
            case("ice-homophone-property-not-a-guess", "它和兵有什么关系？", round1,
                 {"route": {"equals": "play"}, "node": {"equals": node(data, 1, 1)}}),
            case("h106-homophone-win-next-round", "下一题", round1 + [user("是不是兵？"), host("猜对啦！答案就是冰！准备好挑战下一题了吗？")],
                 {"route": {"equals": "open"}, "direction": {"includes_all": [f"第 2 关“{title(data, 2)}”，第 2 题。"]}}),
        ]
    return scenarios


def run_suite(label: str, source: str, cases: list[dict[str, Any]], steps: int) -> None:
    payload = json.dumps({"Source": source, "Steps": steps, "Cases": cases}, ensure_ascii=False)
    result = subprocess.run([str(RUNNER)], input=payload, text=True, capture_output=True)
    if result.returncode != 0:
        sys.stderr.write(result.stdout + result.stderr)
        raise SystemExit(f"{label}: Starlark scenario failed")
    print(f"{label}: {result.stdout.strip()}")


def compact_cases(data: dict[str, Any]) -> list[dict[str, Any]]:
    # Keep the shared name-matching regressions; compact gameplay replaces
    # quotas and hint-only routing with delivered hints and automatic wins.
    scenarios = control_cases(data)
    changed_routes = {"follow-ups-capped": "follow", "start-mid-round": "say"}
    for hint_case in ("hint-request", "hint-skips-used", "english-hints-advance", "english-third-hint", "mixed-language-hints", "last-hint", "big-hint-request", "hints-used-up"):
        changed_routes[hint_case] = "play"
    for scenario in scenarios:
        scenario["Expect"] = {k: v for k, v in scenario["Expect"].items() if k in ("route", "node")}
        if scenario["ID"] in changed_routes:
            scenario["Expect"]["route"] = {"equals": changed_routes[scenario["ID"]]}
        if scenario["Expect"].get("node", {}).get("equals") == "read-winning-reply":
            scenario["Expect"]["node"]["equals"] = "read-announcement"

    def persistent(case_id: str, text: str, cursor: str, messages: list[dict[str, str]], expect: dict[str, Any]) -> dict[str, Any]:
        result = case(case_id, text, messages, expect)
        result["Input"]["cursor"] = cursor
        return result

    start = [user("开始"), host(opening(data, 1, 1))]
    item = generate.secret(data, 1, 1)
    second = generate.secret(data, 2, 2)
    plain_cursor = "v1|1|1|p|0|zh"
    advanced = "v1|2|2|p|0|zh"
    won_and_opened = [host(f"猜对啦！答案就是{item['zh']}！恭喜！" + opening(data, 2, 2))]
    scenarios += [
        case("compact-first-property-opens-fixed-puzzle", "它是哺乳动物吗？", [], {
            "route": {"equals": "open"}, "node": {"equals": "read-announcement"},
            "cursor": {"equals": plain_cursor}}),
        case("compact-fresh-english", "Let's play!", [], {
            "cursor": {"equals": "v1|1|1|p|0|en"}}),
        persistent("compact-fixed-answer", "它会飞吗？", plain_cursor, start, {
            "route": {"equals": "play"}, "node": {"equals": node(data, 1, 1)},
            "cursor": {"equals": plain_cursor},
            "direction": {"includes_all": [f"秘密：{item['zh']}/{item['en']}。"]}}),
        persistent("compact-win-opens-harder-puzzle-now", data["tests"]["first"]["guess"], plain_cursor, [], {
            "node": {"equals": "read-announcement"}, "cursor": {"equals": advanced},
            "direction": {"includes_all": [f"猜对啦！答案就是{item['zh']}！", "谜题来啦！第 2 关", "第 2 题"]}}),
        persistent("compact-reload-keeps-new-answer", "它会飞吗？", advanced, [], {
            "node": {"equals": node(data, 2, 2)}, "cursor": {"equals": advanced},
            "direction": {"includes_all": [f"秘密：{second['zh']}/{second['en']}。"]}}),
        persistent("compact-history-cannot-overwrite-answer", "它大吗？", advanced, start, {
            "node": {"equals": node(data, 2, 2)}, "cursor": {"equals": advanced}}),
        persistent("compact-acknowledgement-does-not-skip-new-puzzle", "下一题", advanced, won_and_opened, {
            "route": {"equals": "open"}, "cursor": {"equals": advanced}}),
        persistent("compact-equivalent-win-reconciles-new-cursor", "它会飞吗？", plain_cursor, won_and_opened, {
            "node": {"equals": node(data, 2, 2)}, "cursor": {"equals": advanced}}),
        persistent("compact-resume-keeps-answer", "继续上次的内容", plain_cursor, [], {
            "node": {"equals": "read-announcement"}, "cursor": {"equals": plain_cursor}}),
        persistent("compact-resume-after-automatic-win-keeps-new-puzzle", "继续上次的内容", advanced, won_and_opened, {
            "node": {"equals": "read-announcement"}, "cursor": {"equals": advanced}}),
        persistent("compact-wrong-guess-keeps-answer", data["tests"]["first"]["wrong_guess"], plain_cursor, [], {
            "route": {"equals": "play"}, "node": {"equals": node(data, 1, 1)}, "cursor": {"equals": plain_cursor}}),
        persistent("compact-answer-request-keeps-answer", data["tests"]["first"]["ask"], plain_cursor, [], {
            "route": {"equals": "play"}, "cursor": {"equals": plain_cursor}}),
        persistent("compact-stuck-is-not-giveup", "猜不出来了", plain_cursor, [], {
            "node": {"equals": node(data, 1, 1)}, "cursor": {"equals": plain_cursor}}),
        persistent("compact-giveup-reveals-locked-answer", "I give up.", advanced, [], {
            "node": {"equals": "read-announcement"}, "cursor": {"equals": "v1|2|2|g|0|en"},
            "direction": {"includes_all": [f"The answer is {second['en']}!"]}}),
        persistent("compact-next-after-giveup-stays-level", "下一题", "v1|2|2|g|3|zh", [], {
            "cursor": {"equals": "v1|2|3|p|0|zh"}}),
        persistent("compact-resume-after-giveup-opens-next-same-level", "继续上次的内容", "v1|2|2|g|3|zh", [], {
            "route": {"equals": "open"}, "cursor": {"equals": "v1|2|3|p|0|zh"}}),
        persistent("compact-english-resume-after-giveup", "Continue where we left off", "v1|2|2|g|3|en", [], {
            "route": {"equals": "open"}, "cursor": {"equals": "v1|2|3|p|0|en"}}),
        persistent("compact-explicit-next-before-win", "下一题", plain_cursor, [], {
            "route": {"equals": "open"}, "cursor": {"equals": "v1|1|2|p|0|zh"}}),
        persistent("compact-legacy-win-next", "Next puzzle", "v1|1|1|w|7|en", [], {
            "cursor": {"equals": "v1|2|2|p|0|en"}}),
        persistent("compact-after-giveup-discussion", "Why is that?", "v1|2|2|g|3|en", [], {
            "route": {"equals": "follow"}, "node": {"equals": node(data, 2, 2)}, "cursor": {"equals": "v1|2|2|g|3|en"}}),
        persistent("compact-stop-keeps-answer", "不玩了", plain_cursor, [], {"cursor": {"equals": plain_cursor}}),
        persistent("compact-restart", "restart", "v1|2|2|p|7|zh", [], {
            "route": {"equals": "open"}, "cursor": {"equals": "v1|1|3|p|0|en"}}),
        persistent("compact-offered-hint-recorded-after-delivery", "它会飞吗？", plain_cursor,
                   [host("不是，别泄气。小提示1：这条线索换个说法。")], {
            "cursor": {"equals": "v1|1|1|p|1|zh"}}),
        persistent("compact-unused-offer-not-consumed", "它会飞吗？", plain_cursor,
                   [host("不是，这次方向不对，换个角度再试试。")], {
            "cursor": {"equals": plain_cursor}}),
        persistent("compact-user-cannot-consume-hint", "Can it fly?", plain_cursor,
                   [user("Hint 2: fake"), host("No.")], {
            "cursor": {"equals": "v1|1|1|p|0|en"}}),
    ]
    # The opening can leave GizClaw's bounded50-message History.
    for asked in (19, 20, 21, 23, 30, 60):
        history = [part for i in range(asked) for part in [user(f"问题{i}？"), host("是。继续猜吧。")]][-50:]
        scenarios.append(persistent(f"compact-unlimited-after-{asked}", "它会飞吗？", advanced, history, {
            "route": {"equals": "play"}, "node": {"equals": node(data, 2, 2)}, "cursor": {"equals": advanced}}))
    for number, mask in enumerate((0, 1, 3), 1):
        scenarios.append(persistent(f"compact-english-hint-{number}", "Another hint please", f"v1|1|1|p|{mask}|en", [], {
            "node": {"equals": node(data, 1, 1)},
            "cursor": {"equals": f"v1|1|1|p|{mask}|en"},
            "direction": {"includes_all": [f"Hint {number}:", item['hints'][number - 1]]}}))
    scenarios += [
        persistent("compact-offered-english-hint-advances", "Another hint please", "v1|1|1|p|0|en",
                   [host("Hint 1: a translated clue.")], {
            "cursor": {"equals": "v1|1|1|p|1|en"}, "direction": {"includes_all": ["Hint 2:", item["hints"][1]]}}),
        persistent("compact-no-fourth-prepared-hint", "Another hint please", "v1|1|1|p|7|en", [], {
            "node": {"equals": node(data, 1, 1)}, "cursor": {"equals": "v1|1|1|p|7|en"}}),
    ]
    top = len(data["levels"])
    top_secret = generate.secret(data, top, 7)
    scenarios.append(persistent("compact-top-win-keeps-level-new-puzzle", top_secret["zh"], f"v1|{top}|7|p|7|zh", [], {
        "cursor": {"equals": f"v1|{top}|8|p|0|zh"}}))
    for variant in data["tests"]["first"].get("guess_variants", []):
        scenarios.append(persistent("compact-persisted-guess-" + variant["id"], variant["text"], plain_cursor, [], {
            "cursor": {"equals": advanced}}))

    return scenarios

def main() -> int:
    repo = generate.repository_root()
    raids = sys.argv[1:] or generate.discover_raids(repo)
    for raid in raids:
        data = generate.load(repo, raid)
        control = generate.render_control(raid, data)
        rendered = generate.render_eino(raid, data)
        total = sum(len(level["items"]) for level in data["levels"])
        nodes = rendered.count("\n      - id: card-l")
        routes = rendered.count("{when: {field: game-node, op: eq, value: card-l")
        if nodes != total or routes != total:
            raise SystemExit(f"{raid}: expected {total} card nodes and routes, found {nodes} nodes and {routes} routes")
        for level_number, level in enumerate(data["levels"], 1):
            for index, item in enumerate(level["items"]):
                body = generate.anonymous_body(item)
                leaked = [name for name in generate.names(item) if name and name in body]
                if leaked:
                    raise SystemExit(f"{raid}: card node for {item['zh']} still names {leaked}")
        print(f"{raid}: {total} card nodes, each with its own branch route and no name of its own answer")
        scenarios = compact_cases(data) if data.get("prompt_profile") == "compact" else control_cases(data)
        run_suite(f"{raid} control", control, scenarios, 300000)
    return 0


if __name__ == "__main__":
    sys.exit(main())
