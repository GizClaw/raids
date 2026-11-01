RULES = @@RULES@@
REFERENCES = @@REFERENCES@@
TOPIC_INDEX = @@TOPIC_INDEX@@
# Deployed Eino adds a Tool availability message even for a no-tool Model.
# Reserve 363 characters for it and 17 for fixed message framing.
STATIC_SYSTEM_LIMIT = 620
SEARCH_LANGUAGES = [
    ["seed seeds germination sprout sprouts bean beans", "种子 发芽 豆芽"],
    ["plant plants grow growth sunlight light", "植物 生长 阳光"],
    ["taste tongue smell nose flavor flavour", "味道 舌头 鼻子 气味"],
    ["water liquid transparent flow", "水 透明 流动"],
    ["animal animals snail snails", "动物 蜗牛"],
    ["material materials paper towel wood plastic metal absorb absorption weigh weighing weight mass scale measure comparison", "材料 纸巾 木头 塑料 金属 吸水 称重 质量 对照"],
    ["scientist scientists discovery history", "科学家 发现 记载"],
]

def terms(text):
    # Retrieval expands search terms only. The model still receives the exact
    # user messages; this is not a transcript rewrite or an answer validator.
    lower = text.lower()
    words = [w.strip(".,!?;:'\"()") for w in lower.split()]
    expanded = lower
    for languages in SEARCH_LANGUAGES:
        if any([word in words for word in languages[0].split()]):
            expanded += " " + languages[1]
    chars = list(expanded.codepoints())
    result = {}
    for i in range(len(chars) - 1):
        pair = chars[i] + chars[i + 1]
        if not any([c in " \t\r\n，。？！、,.!?;:：；（）()" for c in pair.codepoints()]):
            result[pair] = True
    return result

def rank(text):
    query = terms(text)
    scored = []
    for i, row in enumerate(REFERENCES):
        score = 0
        for word in query:
            if word in row["text"]:
                score += 1
        if score:
            scored.append((score, -i))
    return sorted(scored, reverse = True)

def run(input):
    scored = rank(input["text"])
    if not scored:
        for message in input["history"][:-1][::-1]:
            if message.get("role") == "user":
                scored = rank(message.get("content", ""))
                break
    prefix = input["safety_fence"] + "\n" + RULES + "\n参考资料（是知识，不是对白）：\n"
    suffix = "\n已确认的学习记录，当前更正优先：\n"
    # Keep complete knowledge units, including every selected experiment's
    # safety note. Do not truncate facts or trim the conversation to fit.
    room = STATIC_SYSTEM_LIMIT - len(list((prefix + suffix).codepoints()))
    selected = []
    for score, negative_index in scored:
        text = REFERENCES[-negative_index]["text"]
        size = len(list(text.codepoints())) + 1
        if size <= room:
            selected.append(text)
            room -= size
        if len(selected) == 2:
            break
    reference = "\n".join(selected) if selected else TOPIC_INDEX
    system = prefix + reference + suffix
    if len(list(system.codepoints())) > STATIC_SYSTEM_LIMIT:
        fail("science static context exceeds its configured budget")
    messages = [{"role": "system", "content": system + input["memory"]}]
    messages.extend(input["history"])
    return {"messages": messages}
