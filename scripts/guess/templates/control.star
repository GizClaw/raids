# Generated from workflows/@@RAID@@/puzzles.json by scripts/guess/generate.py.
# Eino keeps no hidden state between turns, so every turn rebuilds the game
# from the spoken History: the latest "谜题来啦"/"Puzzle time" opening names
# the level and the puzzle number, and (level, puzzle) picks the secret.
# Each turn makes one model call: this script either writes the host's
# instruction for build-host-prompt, or activates the current puzzle's card
# node, whose card has the name removed so the host cannot say it.
DATA = @@DATA@@
MAX_ASK = 20
MAX_HINTS = 3
AUTO_HINT_AFTER = 5
SPACES = [" ", "　", "\t", "\n", "\r"]
DIGITS = {"0": 0, "1": 1, "2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7, "8": 8, "9": 9, "０": 0, "１": 1, "２": 2, "３": 3, "４": 4, "５": 5, "６": 6, "７": 7, "８": 8, "９": 9}
CN_NUM = {"零": 0, "〇": 0, "一": 1, "二": 2, "两": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9}
DROP = " \t\n\r　。，,.!！?？、~～…\"'“”‘’:：;；()（）《》「」·•・-"
LATIN = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
RESTART_WORDS = ["从头开始", "重新开始", "从第一关开始", "restart", "startover", "请从指定中文开场开始"]
START_WORDS = ["开始", "开始吧", "开始游戏", "start", "letsstart", "startgame", "letsplay"]
RESUME_CUES = ["继续上次", "continuewhere", "leftoff"]
STOP_CONTAINS = ["不玩了", "不想玩", "结束游戏", "退出游戏", "stopplaying", "dontwanttoplay"]
STOP_EXACT = ["结束", "再见", "拜拜", "退出", "stop", "bye", "goodbye", "quit"]
NEXT_CUES = ["下一题", "下一个", "再来", "开始", "继续", "准备好", "好的", "好啊", "好呀", "可以", "来吧", "next", "another", "ready", "letsgo", "sure", "okay", "yes"]
NEXT_EXACT = ["好", "嗯", "行", "要", "ok", "yeah", "yep"]
QUESTION_CUES = ["？", "?", "吗", "什么", "哪", "谁", "为什么", "怎么", "多少", "几", "what", "who", "when", "where", "why", "how", "which"]
MAX_FOLLOW_UPS = 2
REMIND_AT = [10, 5, 3, 2, 1]
CLOSINGS_ZH = ["你的下一个问题是什么？", "接下来你想问什么呢？", "你还想问点什么？", "要不要直接猜一猜答案？"]
CLOSINGS_EN = ["What's your next question?", "What would you like to ask next?", "What else do you want to know?", "Do you want to take a guess?"]
HINT_CUES = ["提示", "线索", "帮帮我", "帮我一下", "猜不到", "猜不出", "想不出", "太难了", "hint", "clue", "helpme", "imstuck"]
GIVE_UP_CUES = ["我放弃", "放弃了", "不猜了", "认输", "猜不出来了", "igiveup", "giveup"]
# What may surround the secret's name in a guess such as “是孔子吗” or “Is it Confucius?”.
GUESS_FILLERS = ["是不是", "我猜是", "我猜", "我觉得是", "我觉得", "答案是", "谜底是", "应该是", "会不会是", "难道是", "那就是", "就是", "是", "吗", "呀", "啊", "呢", "吧", "嘛", "他", "她", "它", "这个人", "这个", "这种", "那个", "一只", "一头", "一条", "一种", "一个", "一位", "一匹", "一块", "一座", "一颗", "一台", "一辆", "一件", "一项", "一本", "一张", "theansweris", "isit", "itis", "iguess", "ithink", "maybe", "is", "it", "the", "an", "a"]
DECLINE_EXACT = ["不要", "不想", "不了", "不用了", "先不了", "no", "nope", "notnow", "nothanks"]

def compact(text):
    out = []
    for ch in text.lower().codepoints():
        if ch in DROP:
            continue
        out.append(ch)
    return "".join(out)

def has_cjk(text):
    for ch in text.codepoints():
        code = ord(ch)
        if code >= 19968 and code <= 40959:
            return True
    return False

def has_latin(text):
    for ch in text.codepoints():
        if ch in LATIN:
            return True
    return False

def pick_lang(text, previous):
    if has_cjk(text):
        return "zh"
    if has_latin(text):
        return "en"
    if previous != "":
        return previous
    return "zh"

def read_int(chars, start):
    i = start
    for ch in chars[start:]:
        if ch in SPACES:
            i += 1
        else:
            break
    value = 0
    count = 0
    for ch in chars[i:]:
        if ch in DIGITS:
            value = value * 10 + DIGITS[ch]
            count += 1
        else:
            break
    if count > 0:
        return [value, i + count]
    seq = []
    for ch in chars[i:]:
        if ch in CN_NUM or ch == "十":
            seq.append(ch)
        else:
            break
    if len(seq) == 0:
        return [-1, i]
    if "十" in seq:
        pos = seq.index("十")
        tens = 1
        if pos > 0:
            tens = CN_NUM.get(seq[pos - 1], 1)
        ones = 0
        if pos + 1 < len(seq):
            ones = CN_NUM.get(seq[pos + 1], 0)
        return [tens * 10 + ones, i + len(seq)]
    return [CN_NUM[seq[0]], i + len(seq)]

def numbers_after(content, prefix, suffix):
    found = []
    chars = list(content.codepoints())
    pchars = list(prefix.codepoints())
    schars = list(suffix.codepoints())
    plen = len(pchars)
    for i in range(len(chars)):
        if chars[i:i + plen] != pchars:
            continue
        got = read_int(chars, i + plen)
        if got[0] < 0:
            continue
        j = got[1]
        for ch in chars[j:]:
            if ch in SPACES:
                j += 1
            else:
                break
        if len(schars) == 0 or chars[j:j + len(schars)] == schars:
            found.append(got[0])
    return found

def round_info(content):
    low = content.lower()
    levels = []
    puzzles = []
    if "谜题来啦" in content:
        levels = numbers_after(content, "第", "关")
        puzzles = numbers_after(content, "第", "题")
    elif "puzzle time" in low:
        levels = numbers_after(low, "level", "")
        puzzles = numbers_after(low, "puzzle", "")
    if len(levels) == 0 or len(puzzles) == 0:
        return None
    return [min(max(levels[0], 1), len(DATA["levels"])), max(puzzles[0], 1)]

def secret_index(level, puzzle):
    lv = DATA["levels"][level - 1]
    return (lv["offset"] + (puzzle - 1) * lv["step"]) % len(lv["items"])

def secret_for(level, puzzle):
    return DATA["levels"][level - 1]["items"][secret_index(level, puzzle)]

def two(n):
    return ("0" + str(n)) if n < 10 else str(n)

def card_node(level, puzzle):
    # Each puzzle has its own prompt node holding only its background card;
    # the branch after this script activates exactly that one.
    return "card-l" + two(level) + "-p" + two(secret_index(level, puzzle))

def names_of(item):
    return [item["zh"], item["en"]] + item["aliases"]

def mentions(text, item):
    low = text.lower()
    for name in names_of(item):
        if name != "" and name.lower() in low:
            return True
    return False

def revealed(content, item):
    low = content.lower()
    cue = "答案就是" in content or "答案揭晓" in content or "the answer is" in low or "the answer was" in low
    return cue and mentions(content, item)

def won_cue(content):
    return "猜对啦" in content or "you got it" in content.lower()

def starts_no(content):
    low = content.strip().lower()
    if content.strip().startswith("不是"):
        return True
    for head in ["no,", "no.", "no!", "no ", "nope"]:
        if low.startswith(head):
            return True
    return low == "no"

def counts_as_question(text):
    # Only questions and guesses use up the 20 chances; asking for a hint,
    # giving up, and game commands do not.
    word = compact(text)
    if word in START_WORDS or word in RESTART_WORDS or word in STOP_EXACT:
        return False
    return not (matches_any(word, HINT_CUES) or matches_any(word, GIVE_UP_CUES) or matches_any(word, RESUME_CUES) or matches_any(word, STOP_CONTAINS))

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
        if "小提示" in content or "hint:" in content.lower():
            state["hints"] += 1
            state["streak"] = 0
        elif starts_no(content):
            state["streak"] += 1
        else:
            state["streak"] = 0
    return state

def title(level, lang):
    lv = DATA["levels"][level - 1]
    return lv["title_en"] if lang == "en" else lv["title_zh"]

def example(lang, index):
    examples = DATA["examples_en"] if lang == "en" else DATA["examples_zh"]
    return examples[index % len(examples)]

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

def is_guess(text, item):
    word = compact(text)
    for name in sorted([compact(n) for n in names_of(item) if n != ""], key=len, reverse=True):
        if name == "" or name not in word:
            continue
        rest = word.replace(name, "")
        # Longest first, so "an" is not cut down to a stray "n" by "a".
        for filler in sorted(GUESS_FILLERS, key=len, reverse=True):
            rest = rest.replace(filler, "")
        return rest == ""
    return False

def reveal(lang, state, reason):
    # The whole reveal is our own text, so the host reads it verbatim instead of
    # composing it (a composed reveal tends to stop after its first sentence).
    if lang == "en":
        return "Say this whole paragraph exactly, word for word, adding nothing: “" + reveal_words(lang, state, reason) + "”"
    return "逐字说出下面这一整段话，一字不改：“" + reveal_words(lang, state, reason) + "”"

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

def unused_hints(state):
    hints = secret_for(state["level"], state["puzzle"])["hints"]
    left = [hint for hint in hints if hint not in state["said"]]
    return left if len(left) > 0 else hints[-1:]

def hint_choice(lang, state, closing):
    # Prewritten hints cannot know what the child has already found out, so the
    # host picks, among the unused ones, one that tells the child something new.
    options = unused_hints(state)
    if lang == "en":
        pick = "this hint translated into English" if len(options) == 1 else "the one hint below, translated into English, that tells the child something they have not found out yet"
        return "say “Hint:” followed by " + pick + ", then “" + closing + "” — add no other clue: " + " / ".join(options)
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
            "The child is asking or guessing. The system has already checked that the child did NOT name the answer.",
            "Answer from the puzzle card: if it is a yes or no question, start with “Yes” or “No” and you may restate it (if they asked “" + ex_q[0] + "”, say “" + ex_q[1] + " " + closing + "” or “" + ex_q[2] + " " + closing + "”). Mostly true with a clear exception: start with “Partly”. Not on the card and not sure: start with “I'm not sure about that one”. Titles given after death or by later admirers do not count.",
            "Only answer and restate. Never explain why, and never say any book, work, event, title, place, person or number from the card.",
            "If the child names an answer to guess, it is wrong: start with “No”, say that is not it, and encourage them.",
            "If it cannot be answered with yes or no (a name, a year, letters of the name): start with “I can only answer yes or no” and give exactly this example: “" + sample + "”.",
            "If they ask for the answer or who it is without giving up, tell them they can say “I give up” to see it.",
        ]
    else:
        lines = [
            "孩子在提问或猜答案。系统已经核对过：孩子这句话没有说中谜底。",
            "按谜底卡回答：能用“是/不是”回答的问题，回复第一个字必须是“是”，或以“不是”开头，后面可以把问题改成陈述句复述一遍（孩子问“" + ex_q[0] + "”就说“" + ex_q[1] + closing + "”或“" + ex_q[2] + closing + "”）；大体对但有明显例外就以“有一部分是”开头；卡上没写到、拿不准就以“这个我也说不准”开头。身份按本人真实做过的事判断，后世追封、尊称不算。",
            "只回答和复述，不要解释原因，绝不能说出谜底卡上的书名、作品、事件、称号、地名、人名或数字。",
            "如果孩子是直接说出一个答案来猜，那一定猜错了：以“不是”开头，说“不是某某哦”（某某换成孩子猜的答案），再鼓励一句。",
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
            lines.append(("If this answer is “No”, add “Hint:” followed by this hint in English: " + first) if lang == "en" else ("如果这次的回答是“不是”，就在回答后面逐字加一句“小提示：" + first + "。”"))
    lines.append("If the child talks about copying something dangerous in real life, follow the safety rules first." if lang == "en" else "如果涉及现实中的危险模仿或安全问题，先按安全规则回答。")
    return lines

def play(text, lang, state):
    level = state["level"]
    item = secret_for(level, state["puzzle"])
    if is_guess(text, item):
        return say(lang, reveal("zh", state, "win"), reveal("en", state, "win"))
    if matches_any(compact(text), GIVE_UP_CUES):
        return say(lang, reveal("zh", state, "giveup"), reveal("en", state, "giveup"))
    if matches_any(compact(text), HINT_CUES):
        return give_hint(lang, state)
    lines = answer_rules(lang, state)
    left = MAX_ASK - state["asked"] - 1
    if left <= 0:
        lines.append(("This was the 20th question. First answer it in one sentence by the rules above, then say this exactly, word for word: “" + reveal_words("en", state, "out") + "”") if lang == "en" else ("这是第 20 问。先按上面的规则用一句话回答这一问，然后" + reveal("zh", state, "out")))
    else:
        if left in REMIND_AT:
            lines.append(("Also tell the child they have " + str(left) + " questions left.") if lang == "en" else ("再告诉孩子还剩 " + str(left) + " 次提问机会。"))
        if lang == "en":
            # English replies tend to stop after the answer, so the two-part
            # shape goes first where the model cannot miss it.
            lines.insert(0, "Your reply must be two parts: first your answer as described below, then exactly this question: “" + CLOSINGS_EN[state["asked"] % len(CLOSINGS_EN)] + "” Never stop after the answer.")
            lines.append("Every reply ends with that question.")
        else:
            lines.append("最后一句必须是以问号结尾的简短问句，例如“" + CLOSINGS_ZH[state["asked"] % len(CLOSINGS_ZH)] + "”，不要用“请继续提问吧”这类陈述句结尾。")
    return {"route": "play", "node": card_node(level, state["puzzle"]), "direction": head(lang) + "\n".join(lines), "rules": DATA["host_rules"]}

def follow_up(text, lang, state):
    # The revealed puzzle's own card node answers the follow-up question.
    if lang == "en":
        body = "The last answer has been revealed and the child is asking about it. Answer in one or two short, child-friendly sentences: use the puzzle card first, and you may add well-established common knowledge you are sure of; if you are not sure, say so. Do not start a new puzzle or say “Puzzle time”. End with exactly “Ready for the next puzzle?”"
    else:
        body = "上一题的答案已经揭晓，孩子在追问和它有关的问题。用一两句适合小朋友的话简短回答：先用谜底卡上的内容，卡上没有的，可以补充你确定的公认常识；拿不准就直说不知道。不要开启新的一题，不要说“谜题来啦”；最后逐字问“准备好挑战下一题了吗？”"
    return {"route": "follow", "node": card_node(state["level"], state["puzzle"]), "direction": head(lang) + body, "rules": DATA["host_rules"]}

def matches_any(word, words):
    for candidate in words:
        if candidate in word:
            return True
    return False

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
