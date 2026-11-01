# Generated from workflows/@@RAID@@/puzzles.json by scripts/guess/generate.py.
@@STATE_DESCRIPTION@@DATA = @@DATA@@
@@LIMIT_CONSTANTS@@SPACES = [" ", "　", "\t", "\n", "\r"]
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
@@CLOSING_CONSTANTS@@HINT_CUES = ["提示", "线索", "帮帮我", "帮我一下", "猜不到", "猜不出", "想不出", "太难了", "hint", "clue", "helpme", "imstuck"]
ANSWER_REQUEST_CUES = ["告诉我答案", "答案是什么", "直接告诉我", "到底是谁", "到底是什么", "你说答案", "tellmetheanswer", "whatistheanswer", "justtellme", "whoisit", "whatisit"]
GIVE_UP_CUES = @@GIVE_UP_CUES@@
# Strip wrappers only at the edges, never words from inside an answer or a
# property question. Matching a wrapper is optional; the model can judge an
# equivalent guess using the privately supplied fixed answer.
GUESS_PREFIXES = ["我想问", "请问", "所以", "那么", "你选的", "你想的", "你藏的", "这个东西", "这个物质", "是不是", "我猜", "我觉得", "答案", "谜底", "应该", "会不会", "难道", "那", "就是", "是", "他", "她", "它", "这个人", "这个成语", "这个故事", "成语", "故事", "这个", "这种", "那个", "一只", "一头", "一条", "一种", "一个", "一位", "一匹", "一块", "一座", "一颗", "一台", "一辆", "一件", "一项", "一本", "一张", "coulditbe", "couldit", "woulditbe", "wouldit", "isit", "itis", "theansweris", "iguess", "ithink", "maybe", "is", "it", "be", "the", "an", "a"]
GUESS_SUFFIXES = ["的故事", "对不对", "对吗", "吗", "呀", "啊", "呢", "吧", "嘛"]
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

@@HISTORY_STATE@@def title(level, lang):
    lv = DATA["levels"][level - 1]
    return lv["title_en"] if lang == "en" else lv["title_zh"]

def example(lang, index):
    examples = DATA["examples_en"] if lang == "en" else DATA["examples_zh"]
    return examples[index % len(examples)]

@@ROUND_PROMPTS@@def is_guess(text, item):
    word = compact(text)
    names = [compact(n) for n in names_of(item) if n != ""]
    # Each pass shortens the input, so its byte length bounds the work.
    for unused in range(len(word) + 1):
        if word in names:
            return True
        trimmed = False
        for prefix in sorted(GUESS_PREFIXES, key=len, reverse=True):
            if word.startswith(prefix):
                word = word[len(prefix):]
                trimmed = True
                break
        for suffix in sorted(GUESS_SUFFIXES, key=len, reverse=True):
            if word.endswith(suffix):
                word = word[:-len(suffix)]
                trimmed = True
                break
        if not trimmed:
            break
    # An explicitly named different puzzle stays wrong even if it sounds
    # similar. Only a whole name, after removing grammatical wrappers, can
    # be recognized as a transcription of this puzzle's name.
    for level in DATA["levels"]:
        for other in level["items"]:
            for name in names_of(other):
                if word == compact(name) and word not in names:
                    return False
    for name in names:
        if same_pronunciation(word, name):
            return True
    return False

def same_pronunciation(word, name):
    # Compare the whole direct guess, not a name found inside a property or
    # negated question. Alternatives come from the full pronunciation data,
    # not from the regression's example spellings. Mandarin ASR can lose tone.
    given = list(word.codepoints())
    expected = list(name.codepoints())
    if len(given) != len(expected) or len(given) == 0:
        return False
    changed = False
    for a, b in zip(given, expected):
        if a == b:
            continue
        if a not in DATA["homophones"].get(b, ""):
            return False
        changed = True
    return changed

@@ANSWER_PROMPTS@@@@REVEAL_WORDS@@@@HINT_STATE@@@@PLAY_PROMPTS@@def matches_any(word, words):
    for candidate in words:
        if candidate in word:
            return True
    return False

@@RUN_CONTROLLER@@
