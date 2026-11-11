"""Generate the checked-in dual-Seed native-control Giztests for both Profiles."""
import argparse
from pathlib import Path

import yaml

from generate import ALIASES, ROOT, action, document, mhs_call, turn


def scenario():
    screen = lambda value: action("mhs", mhs_call("display.main", value))
    return {
        "id": "stateful-dual-seed-control",
        "tool_names": [name for name in ALIASES if name != "web.search"],
        "turns": [
            turn('请记住我喜欢轻音乐，暗号是${oracle}。现在不播放，只回复“已记住”。', contains="已记住"),
            turn("我要唱歌，但先别播放，先帮我确认需求。", ask="自己|练|播放|音乐|唱"),
            turn("我想从设备现有歌单里选，先列出选项让我挑，暂时不要播放。", ask="小星星|卡农|虫儿飞"),
            turn("我喜欢轻松一点的风格，但先别播放，也别筛选或重排；继续保留完整三首的原顺序和编号，让我选。", ask="选择|卡农|轻松|舒缓|哪|播放"),
            turn("先聊个纯知识问题：二加二等于几？不要播放。", ask="4|四"),
            turn("第二首，开始播放。", action("audioplayer.play", {"index": 1}), ask="卡农|第二首|播放"),
            turn("现在停止音乐。", action("audioplayer.stop", {})),
            turn("再帮我选一首，先别播放。", ask="哪|选|音乐|曲|歌"),
            turn("取消这次选歌，不选了。"),
            {**turn("第一首。", ask="想|确认|选择|播放|哪|什么"), "not_contains": ["已播放"]},
            turn("现在新请求：把本机屏幕亮度设为30%。", screen(30)),
            turn("我刚才喜欢哪种音乐？请只回答音乐类型，不操作任何设备。", contains="轻音乐"),
        ],
    }


def function_document(profile):
    case = scenario()
    doc = document(case, profile, 1, workflow_name="function-assistant")
    doc["name"] = "chat-assistant.function-chat." + profile
    enriched = []
    index = 0
    for step in doc["steps"]:
        enriched.append(step)
        if "peer_stream" not in step:
            continue
        reply = "selected_reply_" + str(index)
        doc["variables"][reply] = {"direction": "output", "type": "string"}
        step["peer_stream"]["wait_for_history"] = True
        step["capture"] = {reply: "/reply"}
        step["expect"]["/reply"] = {"non_empty": True, "not_contains": ["NO_DEVICE_ACTION"]}
        if index == 0:
            step["expect"]["/reply"]["pattern"] = "^已记住[。.!！]?$"
        step["expect"]["/response_count"] = {"equals": 1}
        step["expect"].setdefault("/text", {}).setdefault("not_contains", []).append("NO_DEVICE_ACTION")
        enriched.append({
            "id": "single_history_reply_" + str(index), "client": "peer",
            "rpc": {"method": "server.workspace.history.list", "request": {
                "workspace_name": "${workspace}", "order": "WORKSPACE_HISTORY_LIST_REQUEST_ORDER_ASC", "limit": 100,
            }},
            "expect": {
                "/available": {"equals": True}, "/has_next": {"equals": False},
                "/items": {"count": 2 * (index + 1)},
                f"/items/{2 * index}/type": {"equals": "PEER_RUN_HISTORY_ENTRY_TYPE_GEAR"},
                f"/items/{2 * index}/text": {"equals": case["turns"][index]["text"]},
                f"/items/{2 * index + 1}/type": {"equals": "PEER_RUN_HISTORY_ENTRY_TYPE_AGENT"},
                f"/items/{2 * index + 1}/text": {"equals": "${" + reply + "}"},
            },
        })
        if index == 3:
            enriched.append({"id": "reload_pending_intent", "client": "peer",
                             "rpc": {"method": "server.run.workspace.reload", "request": {}}})
        index += 1
    doc["steps"] = enriched
    return doc


def generate(check=False):
    directory = ROOT / "tests/giztest/function-chat"
    if not check:
        directory.mkdir(parents=True, exist_ok=True)
    for profile in ("default", "testing"):
        path = directory / (profile + ".giztest.yaml")
        content = ("# User Story:\n# As a function-chat user,\n"
                   "# I want parallel Seed answer/control lanes,\n"
                   "# So that exact native receipts prove control while one selected reply enters History.\n"
                   + yaml.safe_dump(function_document(profile), allow_unicode=True, sort_keys=False, width=100))
        if check:
            if not path.is_file() or path.read_text() != content:
                raise SystemExit("Stale function-chat Giztest: " + str(path.relative_to(ROOT)))
        else:
            path.write_text(content)
    print("validated" if check else "generated", "two dual-Seed function-chat Giztests")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    generate(parser.parse_args().check)
