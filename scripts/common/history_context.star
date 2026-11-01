# Exact input deduplication, not factual judgment or response rewriting.
def content(message):
    text = message.get("content", "")
    if not text:
        text = "".join([part.get("text", "") for part in message.get("parts", []) if part.get("type") == "text"])
    return text

def remember_pair(known, user, replies):
    if user and replies:
        known[(user, "".join(replies).strip())] = True
        known[(user, "\n".join(replies).strip())] = True

def deduplicate_records(memory, known, marker, user_marker, reply_marker):
    records = memory.split(marker)
    if len(records) == 1:
        return memory
    keep = [records[0]]
    for record in records[1:]:
        pair = record.split(reply_marker, 1)
        head = pair[0].split(user_marker, 1) if user_marker else ["", pair[0]]
        # The record marker may already have consumed the first delimiter.
        # Accept that exact boundary, without matching an unknown head prefix.
        if user_marker.startswith("；") and len(head) == 1:
            plain_marker = user_marker.split("；", 1)[1]
            if plain_marker and pair[0].startswith(plain_marker):
                head = pair[0].split(plain_marker, 1)
        if len(pair) == 2 and len(head) == 2 and (head[1].strip(), pair[1].strip()) in known:
            continue
        keep.append(marker + record)
    return "".join(keep).strip()

def deduplicate_memory(memory, history):
    # Preserve unrecognized records and everything outside the current History.
    known = {}
    user = ""
    replies = []
    for message in history:
        role = message.get("role")
        if role == "user":
            remember_pair(known, user, replies)
            user = content(message).strip()
            replies = []
        elif role == "assistant" and content(message).strip():
            replies.append(content(message))
    remember_pair(known, user, replies)
    if not known:
        return memory
    memory = deduplicate_records(memory, known, "- story_contract_v1；", "；用户本轮输入：", "；角色本轮叙事：\n")
    return deduplicate_records(memory, known, "- 用户：", "", "\n模型：")
