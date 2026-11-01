# section: ROUND_PROMPTS
def head(lang):
    return "用英文：" if lang == "en" else "用中文："

def announce(lang, words, route = "say"):
    # Keep decisions in the controller and leave their delivery to the host.
    return {"route": route, "node": "read-announcement", "direction": head(lang) + words, "rules": ""}

def open_lead(lang, level, puzzle, full):
    if lang == "en":
        marker = "Puzzle time! Level " + str(level) + ", " + title(level, lang) + ", puzzle " + str(puzzle) + "."
        body = "I've picked " + DATA["subject_en"] + ". Ask yes-or-no questions until you guess it, or say you give up. What's your first question?"
        return [marker, body]
    marker = "谜题来啦！第 " + str(level) + " 关“" + title(level, lang) + "”，第 " + str(puzzle) + " 题。"
    body = "我已选定了" + DATA["subject_zh"] + "，你可以一直问是非题，猜中或主动放弃后揭晓。你的第一个问题是什么？"
    return [marker, body]

def open_round(lang, level, puzzle, full):
    lead = open_lead(lang, level, puzzle, full)
    return announce(lang, "开题标记须原样保留：" + lead[0] + " 其余自然表达：" + lead[1], "open")

def say(lang, zh, en):
    return {"route": "say", "node": "", "direction": head(lang) + (en if lang == "en" else zh), "rules": ""}

def recap(lang, state):
    level = state["level"]
    if state["phase"] != "p":
        words = "We're still at Level " + str(level) + ", " + title(level, lang) + ", puzzle " + str(state["puzzle"]) + ". That answer was revealed; the next puzzle waits for your choice." if lang == "en" else "我们仍在第 " + str(level) + " 关“" + title(level, lang) + "”的第 " + str(state["puzzle"]) + " 题。上一题已揭晓，下一题等你选择开启。"
        return announce(lang, words)
    words = "Let's keep going with the same answer at Level " + str(level) + ", " + title(level, lang) + ", puzzle " + str(state["puzzle"]) + ". What's your next question?" if lang == "en" else "我们接着玩第 " + str(level) + " 关“" + title(level, lang) + "”的第 " + str(state["puzzle"]) + " 题，答案还是刚才选定的那个。你的下一个问题是什么？"
    return announce(lang, words)

def ask_first(lang, state):
    body = "同一题已开始，不换题不泄底；提醒问是非题，举例：" + example(lang, 0) + "。邀请提问。"
    return say(lang, body, body)

def farewell(lang, state, midround):
    body = "温暖道别，不强留、不开题、不泄底。当前关卡：" + str(state["level"]) + "，" + title(state["level"], lang) + "。" + ("保留本题，下次可说继续上次的内容。" if midround else "下次可说开始继续挑战。")
    return say(lang, body, body)

# section: ANSWER_PROMPTS
def locked_answer(lang, state):
    item = secret_for(state["level"], state["puzzle"])
    return "秘密：" + item["zh"] + "/" + item["en"] + "。"

# section: PLAY_PROMPTS
def hint_marker(lang, number):
    return ("Hint " + str(number + 1) + ":") if lang == "en" else ("小提示" + str(number + 1) + "：")

def win(lang, state):
    words = reveal_words(lang, state, "win")
    state["level"] = min(state["level"] + 1, len(DATA["levels"]))
    state["puzzle"] += 1
    state["phase"] = "p"
    state["hintmask"] = 0
    # Lock the next deck position in the same checkpoint, before speaking.
    secret_for(state["level"], state["puzzle"])
    return announce(lang, words)

def play(text, lang, state):
    item = secret_for(state["level"], state["puzzle"])
    if is_guess(text, item):
        return win(lang, state)
    if matches_any(compact(text), GIVE_UP_CUES):
        state["phase"] = "g"
        return announce(lang, reveal_words(lang, state, "giveup"))
    start = "Yes/No" if lang == "en" else "是/不是"
    marker = "You got it! The answer is" if lang == "en" else "猜对啦！答案就是"
    next_round = "新题" if state["level"] == len(DATA["levels"]) else "下一关新题"
    body = "属性先依整句、卡及常识答" + start + "，部分属实才部分是，未知直说；可解释所问。索答须明确放弃。仅全名/同义/同音猜中才以“" + marker + "”加谜底揭晓、祝贺并开" + next_round + "；属性不算。"
    numbers = unused_hint_numbers(state)
    if len(numbers) > 0:
        number = numbers[0]
        body += " 求助/卡住可接“" + hint_marker(lang, number) + item["hints"][number] + "”原义，不添线索/字音，不必每轮提示。"
    else:
        body += " 卡住可整理已确认线索，不新增提示或泄底。"
    return {"route": "play", "node": card_node(state["level"], state["puzzle"]), "direction": head(lang) + locked_answer(lang, state) + body, "rules": DATA["host_rules"]}

def follow_up(text, lang, state):
    body = "已揭晓，可依卡及可靠常识回答追问，未知直说；不重开。最后问是否准备好下一题。"
    return {"route": "follow", "node": card_node(state["level"], state["puzzle"]), "direction": head(lang) + locked_answer(lang, state) + body, "rules": DATA["host_rules"]}

# section: READER_PROMPT
            你是亲切机灵的猜谜搭档。下方游戏结果和线索已确定，不重新判题；只把表达和衔接说自然，可轻松逗趣，不挤兑孩子。
            指定标记原样保留，数字和结果不变；只给指定线索，不添属性、不泄未揭晓谜底。输出可朗读正文。

# section: REPLY_LENGTH_CHECK
              if not text.strip():
                  failures.append("empty_reply")

# section: STATE_DESCRIPTION
# The existing game-route field persists only a compact puzzle cursor:
# version, level, puzzle number, phase, used-hint mask and reply language.
# The deck function picks the answer before the opening model call. History
# supplies dialogue, not a replacement answer when its opening is evicted.

# section: HISTORY_STATE
def analyze(messages):
    # Migrate existing spoken History once, before the first cursor commit.
    history = list(messages)
    if len(history) > 0 and history[-1].get("role", "") == "user":
        history = history[:-1]
    state = {"found": False, "level": 1, "puzzle": 0, "phase": "p", "hintmask": 0, "lang": ""}
    start = -1
    for i in range(len(history)):
        message = history[i]
        if message.get("role", "") == "user":
            state["lang"] = pick_lang(message.get("content", ""), state["lang"])
            continue
        info = round_info(message.get("content", ""))
        if info != None:
            start = i
            state["found"] = True
            state["level"] = info[0]
            state["puzzle"] = info[1]
    if not state["found"]:
        return state
    item = secret_for(state["level"], state["puzzle"])
    hinted = 0
    for message in history[start + 1:]:
        if message.get("role", "") == "user":
            continue
        content = message.get("content", "")
        if revealed(content, item):
            state["phase"] = "w" if won_cue(content) else "g"
        if "小提示" in content or "hint:" in content.lower() or any([("hint " + str(n + 1) + ":") in content.lower() for n in range(MAX_HINTS)]):
            hinted += 1
        for i in range(MAX_HINTS):
            bit = [1, 2, 4][i]
            if (item["hints"][i] in content or ("hint " + str(i + 1) + ":") in content.lower()) and state["hintmask"] // bit % 2 == 0:
                state["hintmask"] += bit
    # Legacy unnumbered hints may lack their exact preserved Chinese phrase.
    for i in range(MAX_HINTS):
        used = len([n for n in range(MAX_HINTS) if state["hintmask"] // [1, 2, 4][n] % 2 == 1])
        if used < hinted and state["hintmask"] // [1, 2, 4][i] % 2 == 0:
            state["hintmask"] += [1, 2, 4][i]
    return state

def load_cursor(cursor, messages):
    if cursor == "":
        return analyze(messages)
    parts = cursor.split("|")
    if len(parts) != 6 or parts[0] != "v1":
        fail("invalid persisted guess cursor")
    for index in [1, 2, 4]:
        if not parts[index] or not all([ch in "0123456789" for ch in parts[index].codepoints()]):
            fail("invalid persisted guess cursor number")
    level = int(parts[1])
    puzzle = int(parts[2])
    mask = int(parts[4])
    if level < 1 or level > len(DATA["levels"]) or puzzle < 1 or mask > 7 or parts[3] not in ["p", "w", "g"] or parts[5] not in ["zh", "en"]:
        fail("invalid persisted guess cursor value")
    state = {"found": True, "level": level, "puzzle": puzzle, "phase": parts[3], "hintmask": mask, "lang": parts[5]}
    # Reconcile delivered optional hints and model-recognized equivalent wins.
    # These are protocol markers, not guesses about the content of the reply.
    history = list(messages)
    if len(history) > 0 and history[-1].get("role", "") == "user":
        history = history[:-1]
    if state["phase"] == "p" and len(history) > 0:
        message = history[-1]
        content = message.get("content", "")
        if message.get("role", "") == "assistant":
            if revealed(content, secret_for(level, puzzle)) and won_cue(content):
                state["level"] = min(level + 1, len(DATA["levels"]))
                state["puzzle"] += 1
                state["hintmask"] = 0
            else:
                for number in unused_hint_numbers(state):
                    if hint_marker("zh", number) in content or hint_marker("en", number).lower() in content.lower():
                        state["hintmask"] += [1, 2, 4][number]
    return state

def checkpoint(result, state, lang):
    result["cursor"] = "|".join(["v1", str(state["level"]), str(state["puzzle"]), state["phase"], str(state["hintmask"]), lang])
    return result

def new_puzzle(lang, level, puzzle, full):
    state = {"level": level, "puzzle": puzzle, "phase": "p", "hintmask": 0}
    # Resolve the deterministic deck position before any model sees the turn.
    secret_for(level, puzzle)
    return checkpoint(open_round(lang, level, puzzle, full), state, lang)

# section: REVEAL_WORDS
def reveal_words(lang, state, reason):
    level = state["level"]
    item = secret_for(level, state["puzzle"])
    if reason == "win":
        lead = ("You got it! The answer is " + item["en"] + "!") if lang == "en" else ("猜对啦！答案就是" + item["zh"] + "！")
        tail = "已在最高关，继续同级新题。" if level >= len(DATA["levels"]) else "恭喜升关，下一关的题目会更有挑战。"
        next_level = min(level + 1, len(DATA["levels"]))
        secret_for(next_level, state["puzzle"] + 1)
        opening = open_lead(lang, next_level, state["puzzle"] + 1, False)[0]
        return "猜中已确定，保留“" + lead + "”，自然祝贺。" + tail + "随即开下一题，保留开题标记“" + opening + "”；新谜底已选定不透露，邀请提问，无需再确认准备好。"
    if lang == "en":
        return "No worries! The answer is " + item["en"] + "! You're still at Level " + str(level) + ", " + title(level, lang) + ". Want to try another puzzle?"
    return "没关系，答案揭晓：" + item["zh"] + "！" + item["profile"] + "你还在第 " + str(level) + " 关“" + title(level, lang) + "”，要不要再来一题？"

# section: HINT_STATE
def unused_hint_numbers(state):
    return [i for i in range(MAX_HINTS) if state["hintmask"] // [1, 2, 4][i] % 2 == 0]

# section: RUN_CONTROLLER
def requested_restart(word):
    cues = RESTART_WORDS + ["重新开局", "重新开一局", "重开", "再开一局"]
    for cue in cues:
        position = word.find(cue)
        if position >= 0 and not any([word[:position].endswith(prefix) for prefix in ["不", "别", "不要", "不用", "不想", "不要再", "别再", "dont", "donot", "not"]]):
            return True
    return False

def run(input):
    text = input["text"].strip()
    state = load_cursor(input.get("cursor", ""), input["messages"])
    lang = pick_lang(text, state["lang"])
    word = compact(text)
    if requested_restart(word):
        return new_puzzle(lang, 1, state["puzzle"] + 1, True)
    if not state["found"]:
        return new_puzzle(lang, 1, 1, True)
    if word in STOP_EXACT or word in DECLINE_EXACT or matches_any(word, STOP_CONTAINS):
        return checkpoint(farewell(lang, state, state["phase"] == "p"), state, lang)
    if matches_any(word, RESUME_CUES):
        if state["phase"] != "p":
            level = min(state["level"] + (1 if state["phase"] == "w" else 0), len(DATA["levels"]))
            return new_puzzle(lang, level, state["puzzle"] + 1, False)
        return checkpoint(recap(lang, state), state, lang)
    next_words = ["下一题", "下一个谜题", "换一题", "再来一题", "nextpuzzle", "anotherpuzzle", "newpuzzle", "nextone"]
    wants_next = matches_any(word, next_words) or (state["phase"] != "p" and (word in NEXT_EXACT or word in START_WORDS or word in NEXT_CUES))
    if wants_next:
        # An acknowledgement immediately after automatic advancement must not
        # skip the puzzle that was just opened in the winning reply.
        history = [m for m in input["messages"] if m.get("role", "") == "assistant"]
        if state["phase"] == "p" and len(history) > 0 and won_cue(history[-1].get("content", "")):
            return checkpoint(open_round(lang, state["level"], state["puzzle"], False), state, lang)
        level = min(state["level"] + (1 if state["phase"] == "w" else 0), len(DATA["levels"]))
        return new_puzzle(lang, level, state["puzzle"] + 1, False)
    if state["phase"] != "p":
        result = follow_up(text, lang, state)
    elif word in START_WORDS:
        result = ask_first(lang, state)
    else:
        result = play(text, lang, state)
    return checkpoint(result, state, lang)

def run_graph(input):
    # Export only declared graph ports; route is a controller diagnostic.
    result = run(input)
    return {"cursor": result["cursor"], "node": result["node"],
            "direction": result["direction"], "rules": result["rules"]}

# section: LIMIT_CONSTANTS
MAX_HINTS = 3

# section: CLOSING_CONSTANTS
