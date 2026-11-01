# section: ROUND_PROMPTS
def head(lang):
    if lang == "en":
        return "【回复语言：English】整条回复只用英文，逐字句也用下面给出的英文原句。"
    return "【回复语言：中文】"

def open_lead(lang, level, puzzle, full):
    # The marker sentence always comes first: History keeps only the spoken
    # prefix of a reply the child talks over, and the marker carries the state.
    if lang == "en":
        marker = "Puzzle time! Level " + str(level) + ", " + title(level, lang) + ", puzzle " + str(puzzle) + "."
        if full:
            return [marker, "I'm thinking of " + DATA["subject_en"] + ". You have 20 questions, and I can only answer yes or no. What's your first question?"]
        return [marker, "I've got a new one in mind, and you have 20 questions again. What's your first question?"]
    marker = "谜题来啦！第 " + str(level) + " 关“" + title(level, lang) + "”，第 " + str(puzzle) + " 题。"
    if full:
        return [marker, "我心里已经藏好了" + DATA["subject_zh"] + "，你有 20 次提问机会，只能问我用“是”或“不是”回答的问题。你的第一个问题是什么？"]
    return [marker, "我又想好了" + DATA["subject_zh"] + "，还是 20 次提问机会。你的第一个问题是什么？"]

def open_round(lang, level, puzzle, full):
    lead = open_lead(lang, level, puzzle, full)
    if lang == "en":
        body = "Start a new puzzle. Say this whole paragraph exactly, word for word, beginning with “Puzzle time”, and add nothing before or after it: “" + lead[0] + " " + lead[1] + "”"
    else:
        body = "本轮开启新的一题。从“谜题来啦”开始，逐字说出下面这一整段话，一字不改，前后都不要添加别的内容：“" + lead[0] + lead[1] + "”"
    return {"route": "open", "node": "", "direction": head(lang) + body, "rules": ""}

def say(lang, zh, en):
    return {"route": "say", "node": "", "direction": head(lang) + (en if lang == "en" else zh), "rules": ""}

def recap(lang, state):
    level = state["level"]
    left = MAX_ASK - state["asked"]
    zh = "孩子想接着玩上次的题。逐字说“我们接着玩第 " + str(level) + " 关“" + title(level, "zh") + "”的第 " + str(state["puzzle"]) + " 题，你已经问了 " + str(state["asked"]) + " 次，还剩 " + str(left) + " 次机会。”然后用一个问题请孩子继续提问，不要透露任何关于谜底的信息。"
    en = "The child wants to continue the last puzzle. Say exactly: “Let's keep going with Level " + str(level) + ", " + title(level, "en") + ", puzzle " + str(state["puzzle"]) + ". You've asked " + str(state["asked"]) + " questions and have " + str(left) + " left.” Then ask the child for the next question, without revealing anything about the answer."
    return say(lang, zh, en)

def ask_first(lang, state):
    zh = "孩子说要开始，但这一题已经开始了。逐字说“我们已经开始啦！”再用一句话提醒玩法：只能问能用“是”或“不是”回答的问题，例如“" + example("zh", 0) + "”。最后问孩子第一个问题是什么。"
    en = "The child asked to start, but this puzzle has already started. Say exactly “We've already started!” and remind them in one sentence to ask yes or no questions, for example “" + example("en", 0) + "”. Then ask for their first question."
    return say(lang, zh, en)

def farewell(lang, state, midround):
    level = state["level"]
    if midround:
        zh_keep = "这一题先帮你留着，下次说“继续上次的内容”就能接着猜"
        en_keep = "this puzzle will wait for them, and next time they can say “continue where we left off”"
    else:
        zh_keep = "下次说“开始”就能接着挑战"
        en_keep = "next time they can say “start” to keep playing"
    zh = "孩子想先不玩了。用一两句话温暖地道别，告诉孩子现在在第 " + str(level) + " 关“" + title(level, "zh") + "”，" + zh_keep + "，最后用一个轻松的问题结尾，例如“下次再来挑战好吗？”。不要开启新的一题，不要说出任何谜底。"
    en = "The child wants to stop for now. Say a warm goodbye in one or two sentences, tell them they are at Level " + str(level) + ", " + title(level, "en") + ", and that " + en_keep + ". End with a light question such as “See you next time?”. Do not start a new puzzle or reveal any answer."
    return say(lang, zh, en)

# section: ANSWER_PROMPTS
def locked_answer(lang, state):
    item = secret_for(state["level"], state["puzzle"])
    names = " / ".join(names_of(item))
    if lang == "en":
        return "[Fixed answer, private] Level " + str(state["level"]) + ", puzzle " + str(state["puzzle"]) + ": " + names + ". Use this answer for every judgment; do not choose another or disclose it before the round ends.\n"
    return "【固定谜底，仅供内部判断】第 " + str(state["level"]) + " 关，第 " + str(state["puzzle"]) + " 题：" + names + "。每次判断都用这个答案，不能另选，不能在本题结束前主动透露。\n"

def reveal(lang, state, reason):
    # The whole reveal is our own text, so the host reads it verbatim instead of
    # composing it (a composed reveal tends to stop after its first sentence).
    if lang == "en":
        return "Say this whole paragraph exactly, word for word, adding nothing: “" + reveal_words(lang, state, reason) + "”"
    return "逐字说出下面这一整段话，一字不改：“" + reveal_words(lang, state, reason) + "”"

# section: PLAY_PROMPTS
def hint_choice(lang, state, closing):
    # Prewritten hints cannot know what the child has already found out, so the
    # host picks, among the unused ones, one that tells the child something new.
    options = unused_hints(state)
    if lang == "en":
        # The number, not the translated text, tells later turns which hint was used.
        number = unused_hint_numbers(state)[0] + 1
        return "reply with ONE sentence that joins the hint and the question, and nothing else: “Hint " + str(number) + ": <this hint translated into English>, so " + closing[0].lower() + closing[1:] + "” — add no other clue. The hint to translate: " + options[0]
    if len(options) == 1:
        return "逐字说“小提示：" + options[0] + "。" + closing + "”，不要补充别的线索"
    return "从下面几条提示里挑一条孩子还不知道的（不要和前面已经问出来的答案重复），逐字说“小提示：所选的那条。" + closing + "”，不要补充别的线索：" + " / ".join(options)

def give_hint(lang, state):
    closing = (CLOSINGS_EN if lang == "en" else CLOSINGS_ZH)[state["asked"] % len(CLOSINGS_EN)]
    if state["hints"] >= MAX_HINTS:
        return say(lang, "孩子要提示，但这一题的 " + str(MAX_HINTS) + " 次提示已经用完了。温和地告诉他提示用完啦（不要说“小提示”这几个字），鼓励他继续用是非题来猜，最后逐字问“" + closing + "”", "The child wants a hint, but all " + str(MAX_HINTS) + " hints for this puzzle are used. Kindly say so without the word “Hint”, encourage more yes or no questions, and end with exactly “" + closing + "”")
    return say(lang, "孩子要提示。" + hint_choice("zh", state, closing) + "。", "The child wants a hint. " + hint_choice("en", state, closing) + ".")

def answer_rules(lang, state):
    asked = state["asked"]
    ex_q = DATA["restate_en"] if lang == "en" else DATA["restate_zh"]
    # The model copies the example's shape, so the example carries the closing question.
    closing = (CLOSINGS_EN if lang == "en" else CLOSINGS_ZH)[asked % len(CLOSINGS_EN)]
    sample = example(lang, asked)
    if lang == "en":
        lines = [
            "The child is asking or guessing about the fixed answer. A phrasing the script did not match is not necessarily a wrong guess. Never change the fixed answer to fit the conversation.",
            "Judge the exact proposition the child asked, including its cause, time and words like every or always. A question asking whether a property is true is a yes-or-no question, including technical terms, universal statements and properties absent from the card. Do not reject it as an open-ended question merely because it is more detailed than the examples.",
            "Answer from the fixed answer, puzzle card and well-established facts you are sure of: if it is a yes or no question, start with “Yes” or “No” and you may restate it (if they asked “" + ex_q[0] + "”, say “" + ex_q[1] + " " + closing + "” or “" + ex_q[2] + " " + closing + "”). Use “Partly” only when the asked property itself varies across the cases they asked about. A false cause or time is “No”, even if some other detail in the question is true. Only if genuinely unsure, start with “I'm not sure about that one”; a fact being absent from the card does not make it unknown. Never give a false or uncertain answer merely to keep the secret. Titles given after death or by later admirers do not count.",
            "Only answer and restate. Never explain why, and never say any book, work, event, title, place, person or number from the card.",
            "Every child message may be a speech transcript, even when it looks like typed text. For a direct name guess, compare its pronunciation with the fixed name and aliases BEFORE judging its literal spelling. If the whole guessed name sounds the same, it is a correct guess, including a ONE-CHARACTER answer written with a different homophone; never reject it just because that written character means something else. Also accept an obvious spelling slip that clearly names the fixed answer. If pronunciation and meaning are genuinely ambiguous, ask the child to repeat. A property question is not a name guess.",
            "Distinguish a direct answer guess from a question about a property. A category or shared feature alone is not a correct guess. If their direct guess names or unambiguously means the fixed answer, they won: " + reveal("en", state, "win") + " In that case skip all ordinary-answer, hint, closing and question-limit instructions. Otherwise, only reject a direct guess if it means a different answer: start with “No” and encourage them.",
            "If it cannot be answered with yes or no (a name, a year, letters of the name): start with “I can only answer yes or no” and give exactly this example: “" + sample + "”.",
            "If they ask for the answer or who it is without giving up, tell them they can say “I give up” to see it.",
        ]
    else:
        lines = [
            "孩子在提问或猜本题的固定谜底。脚本没有匹配到的说法不等于猜错；不能为了迎合对话更换固定谜底。",
            "先判断孩子问的完整命题，包括原因、时间和“每条、所有、一定”等限定。询问某个属性是否成立，就是是非题；含有专业术语、全称判断或卡片未写出的属性也一样，不能因为比示例更具体就当成开放式问题拒答。",
            "按固定谜底、谜底卡和你确定的公认常识回答：能用“是/不是”回答的问题，回复第一个字必须是“是”，或以“不是”开头，后面可以把问题改成陈述句复述一遍（孩子问“" + ex_q[0] + "”就说“" + ex_q[1] + closing + "”或“" + ex_q[2] + closing + "”）；只有所问属性本身在孩子问到的不同情况中有真有假，才以“有一部分是”开头。问的原因或时间不对就答“不是”，不能因为句子里另一个事实成立就答部分是。确实拿不准才以“这个我也说不准”开头。卡片没写出某个事实不代表不知道，不能为了保密故意答错或假装不知道。身份按本人真实做过的事判断，后世追封、尊称不算。",
            "只回答和复述，不要解释原因，绝不能说出谜底卡上的书名、作品、事件、称号、地名、人名或数字。",
            "孩子的每条输入都可能是语音转写，即使看起来像打字。直接猜名字时，先比较整段名字的读音与固定谜底及别名是否相同，再考虑字形；读音相同就算猜中。只有一个字的谜底也一样：转写为另一个同音字，必须按固定谜底判猜中，绝不能按那个字的另一种字面意思判错。明显的形近错别字也应按原意判定。确实有歧义才请孩子再说一遍，不要把询问属性误当成猜名字。",
            "先区分直接猜答案和询问属性；只猜中类别或共有特征不算猜中谜底。如果孩子直接猜的名称、别名或明确的同义表达指向固定谜底，必须判猜中：" + reveal("zh", state, "win") + "。这时不再执行普通回答、提示、结尾和次数用完的指令。只有直接猜的是另一个答案时才以“不是”开头并鼓励继续猜。",
            "如果问题不能用是或不是回答（例如问名字、问哪一年、问名字里的字）：以“这个问题我只能回答是或不是哦”开头，再逐字举这个例子：“" + sample + "”。",
            "如果孩子要答案或问谜底是谁但没有说放弃：告诉孩子想看答案可以说“我放弃”。",
        ]
    if state["hints"] >= MAX_HINTS:
        lines.append("If the child asks for a hint: all " + str(MAX_HINTS) + " hints for this puzzle are used, say so kindly without using the word “Hint”." if lang == "en" else "如果孩子要提示：这一题的 " + str(MAX_HINTS) + " 次提示已经用完了，温和地告诉他，不要说“小提示”这几个字。")
    else:
        if lang == "en":
            lines.append("If the child asks for a hint or clue: " + hint_choice("en", state, closing) + ".")
        else:
            lines.append("如果孩子要提示或线索（包括要大提示、问名字里的字）：" + hint_choice("zh", state, closing) + "。")
        if state["streak"] + 1 >= AUTO_HINT_AFTER:
            first = unused_hints(state)[0]
            lines.append(("If this answer is “No”, add “Hint " + str(unused_hint_numbers(state)[0] + 1) + ":” followed by this hint in English: " + first) if lang == "en" else ("如果这次的回答是“不是”，就在回答后面逐字加一句“小提示：" + first + "。”"))
    lines.append("If the child talks about copying something dangerous in real life, follow the safety rules first." if lang == "en" else "如果涉及现实中的危险模仿或安全问题，先按安全规则回答。")
    return lines

def play(text, lang, state):
    level = state["level"]
    item = secret_for(level, state["puzzle"])
    if is_guess(text, item):
        result = say(lang, reveal("zh", state, "win"), reveal("en", state, "win"))
        result["node"] = "read-winning-reply"
        return result
    if matches_any(compact(text), GIVE_UP_CUES):
        return say(lang, reveal("zh", state, "giveup"), reveal("en", state, "giveup"))
    if matches_any(compact(text), HINT_CUES):
        return give_hint(lang, state)
    lines = answer_rules(lang, state)
    left = MAX_ASK - state["asked"] - 1
    if left <= 0:
        lines.append(("If the child did not win: this was the 20th question. First answer it in one sentence by the rules above, then say this exactly, word for word: “" + reveal_words("en", state, "out") + "”") if lang == "en" else ("如果孩子没有猜中：这是第 20 问。先按上面的规则用一句话回答这一问，然后" + reveal("zh", state, "out")))
    else:
        if left in REMIND_AT:
            lines.append(("Also tell the child they have " + str(left) + " questions left.") if lang == "en" else ("再告诉孩子还剩 " + str(left) + " 次提问机会。"))
        if lang == "en":
            # English replies tend to stop after the answer, so the two-part
            # shape goes first where the model cannot miss it.
            lines.insert(0, "For an ordinary question or a wrong guess, your reply must be two parts: first your answer as described below, then exactly this question: “" + CLOSINGS_EN[state["asked"] % len(CLOSINGS_EN)] + "” Never stop after the answer.")
            lines.append("An ordinary answer or a wrong guess ends with that question; a correct guess uses the win paragraph instead.")
        else:
            lines.append("普通回答或猜错时，最后一句必须是以问号结尾的简短问句，例如“" + CLOSINGS_ZH[state["asked"] % len(CLOSINGS_ZH)] + "”，不要用“请继续提问吧”这类陈述句结尾；猜中时只说上面的整段获胜揭晓。")
    return {"route": "play", "node": card_node(level, state["puzzle"]), "direction": head(lang) + locked_answer(lang, state) + "\n".join(lines), "rules": DATA["host_rules"]}

def follow_up(text, lang, state):
    # The revealed puzzle's own card node answers the follow-up question.
    if lang == "en":
        body = "The last answer has been revealed and the child is asking about it. Answer in one or two short, child-friendly sentences: use the puzzle card first, and you may add well-established common knowledge you are sure of; if you are not sure, say so. Do not start a new puzzle or say “Puzzle time”. End with exactly “Ready for the next puzzle?”"
    else:
        body = "上一题的答案已经揭晓，孩子在追问和它有关的问题。用一两句适合小朋友的话简短回答：先用谜底卡上的内容，卡上没有的，可以补充你确定的公认常识；拿不准就直说不知道。不要开启新的一题，不要说“谜题来啦”；最后逐字问“准备好挑战下一题了吗？”"
    return {"route": "follow", "node": card_node(state["level"], state["puzzle"]), "direction": head(lang) + locked_answer(lang, state) + body, "rules": DATA["host_rules"]}

# section: READER_PROMPT
            You are a spoken announcement reader. The game controller has already matched the child's complete guessed name or pronunciation to its fixed answer and decided this round is won. Read the supplied winning paragraph verbatim. Do not judge the guess again, reject it, change its spelling or add a hint. Output only the supplied paragraph in its specified language.
            你是游戏结果播报员。程序已经按完整名称、别名或读音核对过，确定本题猜中了。只按指令逐字播报获胜正文；不要再判断猜测、否认结果、纠正写法或追加提示。
# section: REPLY_LENGTH_CHECK
              count = rune_count(text)
              if spec.get("min_runes", 0) > 0 and count < spec["min_runes"]:
                  failures.append("min_runes:" + str(count) + "<" + str(spec["min_runes"]))
              if spec.get("max_runes", 0) > 0 and count > spec["max_runes"]:
                  failures.append("max_runes:" + str(count) + ">" + str(spec["max_runes"]))
# section: STATE_DESCRIPTION
# Eino keeps no hidden state between turns, so every turn rebuilds the game
# from the spoken History: the latest "谜题来啦"/"Puzzle time" opening names
# the level and the puzzle number, and (level, puzzle) picks the secret.
# Each turn makes one model call: this script either writes the host's
# instruction for build-host-prompt, or activates the current puzzle's card
# node. The card omits the name; the instruction supplies the fixed answer
# privately so the host can judge facts and equivalent guesses without
# changing the answer or revealing it before the round ends.
# section: HISTORY_STATE
def counts_as_question(text):
    # Only questions and guesses use up the 20 chances; asking for a hint or
    # for the answer, giving up, and game commands do not.
    word = compact(text)
    if word in START_WORDS or word in RESTART_WORDS or word in STOP_EXACT:
        return False
    return not (matches_any(word, HINT_CUES) or matches_any(word, ANSWER_REQUEST_CUES) or matches_any(word, GIVE_UP_CUES) or matches_any(word, RESUME_CUES) or matches_any(word, STOP_CONTAINS))

def analyze(messages):
    history = list(messages)
    if len(history) > 0 and history[-1].get("role", "") == "user":
        history = history[:-1]
    state = {"found": False, "level": 1, "puzzle": 0, "asked": 0, "hints": 0, "streak": 0, "over": False, "won": False, "after": 0, "lang": "", "start": -1, "said": ""}
    for message in reversed(history):
        if message.get("role", "") == "user":
            content = message.get("content", "")
            if has_cjk(content):
                state["lang"] = "zh"
                break
            if has_latin(content):
                state["lang"] = "en"
                break
    start = -1
    for i in range(len(history)):
        if history[i].get("role", "") == "user":
            continue
        content = history[i].get("content", "")
        if "谜题来啦" not in content and "puzzle time" not in content.lower():
            continue
        info = round_info(content)
        if info != None:
            start = i
            state["level"] = info[0]
            state["puzzle"] = info[1]
    if start < 0:
        return state
    state["found"] = True
    state["start"] = start
    item = secret_for(state["level"], state["puzzle"])
    for message in history[start + 1:]:
        content = message.get("content", "")
        if message.get("role", "") == "user":
            if counts_as_question(content):
                state["asked"] += 1
            continue
        if state["over"]:
            state["after"] += 1
            continue
        state["said"] += content + "\n"
        if revealed(content, item):
            state["over"] = True
            state["won"] = won_cue(content)
            continue
        if @@HINT_MARKER@@:
            state["hints"] += 1
            state["streak"] = 0
        elif starts_no(content):
            state["streak"] += 1
        else:
            state["streak"] = 0
    return state

# section: REVEAL_WORDS
def reveal_words(lang, state, reason):
    level = state["level"]
    item = secret_for(level, state["puzzle"])
    top = level >= len(DATA["levels"])
    if lang == "en":
        if reason == "win":
            lead = "You got it! The answer is " + item["en"] + "!"
            tail = ("Amazing, you're already at the top level, Level " + str(level) + ": " + title(level, lang) + "! Ready for the next puzzle?") if top else ("Congratulations, you've reached Level " + str(level + 1) + ": " + title(level + 1, lang) + "! Ready for the next puzzle?")
        else:
            lead = ("No worries! The answer is " + item["en"] + "!") if reason == "giveup" else ("That was your 20th question! The answer is " + item["en"] + "!")
            tail = "You're still at Level " + str(level) + ", " + title(level, lang) + ". Want to try another puzzle?"
        return lead + " " + tail
    if reason == "win":
        lead = "猜对啦！答案就是" + item["zh"] + "！"
        tail = ("太厉害了，你已经是最高的第 " + str(level) + " 关“" + title(level, lang) + "”！准备好挑战下一题了吗？") if top else ("恭喜你升到第 " + str(level + 1) + " 关，获得“" + title(level + 1, lang) + "”称号！准备好挑战下一题了吗？")
    else:
        lead = ("没关系，答案揭晓：" + item["zh"] + "！") if reason == "giveup" else ("20 次机会用完啦，答案揭晓：" + item["zh"] + "！")
        tail = "你还在第 " + str(level) + " 关“" + title(level, lang) + "”，要不要再来一题？"
    return lead + item["profile"] + tail

# section: HINT_STATE
def unused_hint_numbers(state):
    # A hint is used when History holds its exact Chinese text or, for an
    # English game where the hint is translated, its number ("Hint 2:").
    hints = secret_for(state["level"], state["puzzle"])["hints"]
    low = state["said"].lower()
    left = [i for i in range(len(hints)) if hints[i] not in state["said"] and ("hint " + str(i + 1)) not in low]
    return left if len(left) > 0 else [len(hints) - 1]

def unused_hints(state):
    hints = secret_for(state["level"], state["puzzle"])["hints"]
    return [hints[i] for i in unused_hint_numbers(state)]

# section: RUN_CONTROLLER
def run(input):
    text = input["text"].strip()
    state = analyze(input["messages"])
    lang = pick_lang(text, state["lang"])
    word = compact(text)
    if word in RESTART_WORDS:
        return open_round(lang, 1, state["puzzle"] + 1, True)
    if not state["found"]:
        return open_round(lang, 1, state["puzzle"] + 1, True)
    if state["over"]:
        if word in STOP_EXACT or word in DECLINE_EXACT or matches_any(word, STOP_CONTAINS):
            return farewell(lang, state, False)
        wants_next = word in NEXT_EXACT or matches_any(word, NEXT_CUES)
        if not wants_next and state["after"] < MAX_FOLLOW_UPS and matches_any(text.lower(), QUESTION_CUES):
            return follow_up(text, lang, state)
        level = state["level"]
        if state["won"] and level < len(DATA["levels"]):
            level += 1
        return open_round(lang, level, state["puzzle"] + 1, False)
    if matches_any(word, RESUME_CUES):
        return recap(lang, state)
    if word in START_WORDS:
        if state["asked"] == 0:
            return ask_first(lang, state)
        return open_round(lang, state["level"], state["puzzle"] + 1, True)
    if word in STOP_EXACT or matches_any(word, STOP_CONTAINS):
        return farewell(lang, state, True)
    return play(text, lang, state)
# section: LIMIT_CONSTANTS
MAX_ASK = 20
MAX_HINTS = 3
AUTO_HINT_AFTER = 5
# section: CLOSING_CONSTANTS
MAX_FOLLOW_UPS = 2
REMIND_AT = [10, 5, 3, 2, 1]
CLOSINGS_ZH = ["你的下一个问题是什么？", "接下来你想问什么呢？", "你还想问点什么？", "要不要直接猜一猜答案？"]
CLOSINGS_EN = ["What's your next question?", "What would you like to ask next?", "What else do you want to know?", "Do you want to take a guess?"]
