"""Build real-model dialogs with exact typed device receipts as the action oracle."""
import argparse
import copy
import json
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[3]
ALIASES = {
    "light.brightness": "mhs", "light.get": "mhs", "music.play": "client_tool",
    "music.playlist": "client_tool", "music.status": "client_tool", "music.stop": "client_tool",
    "screen.brightness": "mhs", "screen.get": "mhs", "web.search": "http_request", "workflow.switch": "client_tool",
}
PROCEDURES = ["audioplayer.get", "audioplayer.playlist.get", "audioplayer.play", "audioplayer.stop", "run.workspace.set"]


def rpc(identifier, method, request, client="peer"):
    return {"id": identifier, "client": client, "rpc": {"method": method, "request": request}}


def mhs_call(target, value):
    return {"id": target, "hwd": "display" if target == "display.main" else "led",
            "args": {"brightness_percent": value}}


def action(group, arguments):
    return [group, arguments]


def turn(text, *actions, ask=None, contains=None):
    return {"text": text, "actions": list(actions), "ask": ask, "contains": contains}


def cases():
    screen = lambda value: action("mhs", mhs_call("display.main", value))
    light = lambda value: action("mhs", mhs_call("led.status", value))
    play = lambda index=None: action("audioplayer.play", {} if index is None else {"index": index})
    stop = action("audioplayer.stop", {})
    switch = action("run.workspace.set", {"workspace_name": "${story}", "kickoff": False})
    return [
        {"id": "screen-exact", "turns": [turn("把本机屏幕亮度设为30%。", screen(30))]},
        {"id": "light-exact", "turns": [turn("把本机状态灯亮度调到70%。", light(70))]},
        {"id": "screen-read", "turns": [turn("本机屏幕现在亮度多少？只查询不要改。", ask="50|五十|五成")], "read": "display.main"},
        {"id": "light-read", "turns": [turn("只查询本机状态灯现在的亮度。", ask="50|五十|五成")], "read": "led.status"},
        {"id": "screen-missing-value", "turns": [turn("帮我调一下屏幕亮度。", ask="多少|百分|数值|几成"), turn("30%。", screen(30))]},
        {"id": "light-missing-value", "turns": [turn("调一下本机状态灯的亮度。", ask="多少|百分|数值|几成"), turn("70%。", light(70))]},
        {"id": "missing-target", "turns": [turn("亮度调到30%。", ask="屏幕|状态灯|哪"), turn("我是说本机屏幕。", screen(30))]},
        {"id": "vague-target-and-value", "turns": [turn("有点暗，调亮一点。", ask="屏幕|状态灯|哪|多少|百分")]},
        {"id": "cancel-slots", "turns": [turn("帮我调屏幕亮度。", ask="多少|百分|数值"), turn("算了，不调了。"), turn("30%。", ask="什么|哪|屏幕|状态灯|确认|用途|数值")]},
        {"id": "new-request-after-cancel", "turns": [turn("帮我调屏幕亮度。", ask="多少|百分|数值"), turn("算了，不调了。"), turn("30%。", ask="屏幕|状态灯|哪"), turn("重新帮我调状态灯亮度。", ask="多少|百分|数值"), turn("40%。", light(40))]},
        {"id": "correction", "turns": [turn("把屏幕亮度设为30%。", screen(30)), turn("改成60%。", screen(60))]},
        {"id": "negative-request", "turns": [turn("不要把屏幕亮度改到30%，保持不动。")]},
        {"id": "record-preference", "turns": [turn("记住我喜欢屏幕亮度30%，现在不要调整。")]},
        {"id": "out-of-range", "turns": [turn("把屏幕亮度设为120%。", ask="100|范围|不能|多少|数值|合法|有效|超")]},
        {"id": "off-grid", "turns": [turn("屏幕亮度设为35%。", ask="档|10|30|40")]},
        {"id": "room-lamp-unsupported", "turns": [turn("把房间台灯亮度设为50%。", ask="无法|不能|不支持|台灯|没有")]},
        {"id": "play-default", "turns": [turn("播放音乐。", play())]},
        {"id": "play-named", "turns": [turn("播放列表里的卡农。", play(1))], "playlist": True},
        {"id": "play-next", "turns": [turn("播放小星星。", play(0)), turn("下一首。", play(1))], "playlist": True},
        {"id": "stop-music", "turns": [turn("播放音乐。", play()), turn("停止音乐。", stop)]},
        # A default play is an authorized attempt. The empty fixture returns a
        # real protocol error; one attempt and an honest failure reply are expected.
        {"id": "empty-playlist", "empty_playlist": True, "turns": [turn("播放音乐。", play(), ask="空|没有|无法|不能|失败|暂无|没能")]},
        {"id": "unknown-song", "turns": [turn("播放列表里的不存在歌曲天外来客。", ask="没有|不在|未找到|找不到|哪")]},
        {"id": "switch-exact", "turns": [turn("切换到 eino-story-aesop 剧本，暂时不要开口。", switch)]},
        {"id": "switch-vague", "turns": [turn("换个剧本。", ask="哪|什么|剧本|选择"), turn("切换到 eino-story-aesop，不要开口。", switch)]},
        {"id": "casual-story", "turns": [turn("伊索寓言是什么？只介绍知识，不切换剧本。", contains="寓言")]},
        {"id": "screen-unsupported", "unsupported": True, "turns": [turn("把屏幕亮度设为30%。", ask="不能|无法|不支持|不可用|没有|没办法|没法|缺少")]},
        {"id": "workspace-narrowing", "tool_names": ["music.stop"], "turns": [turn("把屏幕亮度设为30%。", ask="不能|无法|不支持|不可用|没有")]},
        {"id": "peer-isolation", "isolation": True, "turns": [turn("把本机屏幕亮度设为30%。", screen(30))]},
    ]


def fixtures(case):
    mhs = {"instances": {
        "display.main": {"hwd": "display", "value": {"brightness_percent": 50}, "write_fields": ["brightness_percent"]},
        "led.status": {"hwd": "led", "value": {"brightness_percent": 50}, "write_fields": ["brightness_percent"]},
    }}
    if case.get("unsupported"):
        del mhs["instances"]["display.main"]
    audio = {"audio_player": {"items": [] if case.get("empty_playlist") else
        [{"url": f"https://media.example.com/{index}.mp3", "title": title, "source_ref": "${oracle}"}
         for index, title in enumerate(["小星星", "卡农", "虫儿飞"])]}}
    if not case.get("empty_playlist"):
        audio["audio_player"]["current_index"] = 0
    return mhs, audio


def observer(identifier, method, response, count=0, procedure=None, client="peer"):
    operation = {"method": method, "response": response, "expect_calls": count}
    if procedure:
        operation["tool"] = procedure
    return {"id": identifier, "client": client, "timeout": "5s", "client_rpc": operation,
            "expect": {"/calls": {"equals": count}}}


def receipt_assertions(expected, group):
    result = {}
    for index, args in enumerate(expected):
        if group == "mhs":
            for key in ["id", "hwd", "args"]:
                result[f"/requests/{index}/{key}"] = {"equals": args[key]}
        elif group == "audioplayer.play":
            result[f"/requests/{index}/effective_index"] = {"equals": args.get("index", 0)}
            if "index" in args:
                result[f"/requests/{index}/args/index"] = {"equals": args["index"]}
        else:
            result[f"/requests/{index}/args"] = {"equals": args}
    return result


def document(case, profile_name, repeat):
    profile = yaml.safe_load((ROOT / "runtime-profiles" / (profile_name + ".yaml")).read_text())["spec"]
    token = "9c845896-1447-5a7e-b799-a1df42694fb8" if profile_name == "testing" else "28c4e4e9-a05f-5a7e-815e-9cf9afb6878f"
    mhs, audio = fixtures(case)
    variables = {name: {"direction": "input", "type": "string", "generate": "token"} for name in ["workspace", "story", "oracle", "other_workspace"]}
    variables["endpoint"] = {"direction": "input", "type": "string", "env": "GIZCLAW_TEST_ENDPOINT"}
    steps = [rpc("register", "server.register", {"token": token})]
    steps += [observer("install_read", "client.mhs.v0.read", mhs),
              observer("install_write", "client.mhs.v0.write", mhs)]
    for procedure in PROCEDURES:
        response = {"run_workspace": True} if procedure == "run.workspace.set" else audio
        steps.append(observer("install_" + procedure.replace(".", "_"), "client.tool.v0.invoke", response, procedure=procedure))
    parameters = {"eino_workspace_parameters": {
        "agent_type": "EINO_WORKSPACE_PARAMETERS_AGENT_TYPE_EINO",
        "input": "WORKSPACE_INPUT_MODE_PUSH_TO_TALK"}}
    if profile.get("safety_fences"):
        parameters["eino_workspace_parameters"]["safety_fence_level"] = "off"
    create = {"name": "${workspace}", "workflow_name": "general-assistant", "parameters": parameters}
    if "tool_names" in case:
        create["toolkit"] = {"tool_names": {"value": case["tool_names"]}}
    steps += [rpc("create", "server.workspace.create", create),
              rpc("create_story", "server.workspace.create", {"name": "${story}", "workflow_name": "eino-story-aesop", "parameters": parameters}),
              rpc("select", "server.run.workspace.set", {"workspace_name": "${workspace}"}),
              rpc("reload", "server.run.workspace.reload", {})]
    catalog = rpc("catalog", "server.tool.list", {"workspace_name": "${workspace}", "limit": 100})
    aliases = sorted(case.get("tool_names", ALIASES))
    catalog["expect"] = {"/items": {"count": len(aliases)}, "/has_next": {"equals": False}}
    for index, alias in enumerate(aliases):
        catalog["expect"][f"/items/{index}/name"] = {"equals": alias}
        catalog["expect"][f"/items/{index}/source"] = {"equals": ALIASES[alias]}
        available = not (case.get("unsupported") and alias.startswith("screen."))
        catalog["expect"][f"/items/{index}/available"] = {"equals": available}
    steps.append(catalog)
    clients = {"peer": {"identity": "ephemeral", "connection": "webrtc", "access_point": "${endpoint}"}}
    if case.get("isolation"):
        clients["other"] = copy.deepcopy(clients["peer"])
        steps += [rpc("other_register", "server.register", {"token": token}, "other"),
                  observer("other_mhs_read", "client.mhs.v0.read", mhs, client="other"),
                  observer("other_mhs_write", "client.mhs.v0.write", mhs, client="other")]
        other_catalog = rpc("other_catalog", "server.tool.list", {"limit": 100}, "other")
        other_catalog["expect"] = {"/items": {"count": 10}, "/items/2/name": {"equals": "music.play"},
                                   "/items/2/available": {"equals": False}}
        steps.append(other_catalog)
        foreign_scope = rpc("foreign_workspace_scope", "server.tool.list", {"workspace_name": "${workspace}"}, "other")
        foreign_scope["expect_error"] = {"code": 3}
        steps.append(foreign_scope)
    totals = {"mhs": [], "audioplayer.play": [], "audioplayer.stop": [], "run.workspace.set": []}
    for index, item in enumerate(case["turns"]):
        current = {"id": f"turn_{index}", "client": "peer", "timeout": "90s",
                   "peer_stream": {"mode": "text", "input": item["text"], "require_text": True, "require_audio": False},
                   "expect": {"/text_eos": {"equals": True}}}
        if item.get("ask"):
            current["expect"]["/text"] = {"pattern": item["ask"]}
        if item.get("contains"):
            current["expect"].setdefault("/text", {})["contains"] = item["contains"]
        steps.append(current)
        for group, args in item["actions"]:
            totals[group].append(args)
        for group, expected in totals.items():
            method = "client.mhs.v0.write" if group == "mhs" else "client.tool.v0.invoke"
            response = mhs if group == "mhs" else {"run_workspace": True} if group == "run.workspace.set" else audio
            check = observer(f"{group.replace('.', '_')}_{index}", method, response, len(expected), None if group == "mhs" else group)
            check["expect"].update(receipt_assertions(expected, group))
            steps.append(check)
        if any(group == "run.workspace.set" for group, _ in item["actions"]):
            selected = rpc(f"selected_program_{index}", "server.run.workspace.get", {})
            selected["expect"] = {"/selected_workspace_name": {"equals": "${story}"}}
            steps.append(selected)
    if case.get("read"):
        check = observer("actual_read", "client.mhs.v0.read", mhs)
        del check["client_rpc"]["expect_calls"]
        check["expect"] = {"/calls": {"minimum": 1}, "/requests/0/id": {"equals": case["read"]}}
        steps.append(check)
    if case.get("playlist"):
        check = observer("actual_playlist", "client.tool.v0.invoke", audio, procedure="audioplayer.playlist.get")
        del check["client_rpc"]["expect_calls"]
        check["expect"] = {"/calls": {"minimum": 1}}
        steps.append(check)
    if case["id"] == "play-next":
        check = observer("actual_current_index", "client.tool.v0.invoke", audio, procedure="audioplayer.get")
        del check["client_rpc"]["expect_calls"]
        check["expect"] = {"/calls": {"minimum": 1}}
        steps.append(check)
    if case.get("isolation"):
        steps.append(observer("other_received_no_write", "client.mhs.v0.write", mhs, client="other"))
    finally_steps = [rpc("stop", "server.run.stop", {}),
                     rpc("delete_chat", "server.workspace.delete", {"name": "${workspace}"}),
                     rpc("delete_story", "server.workspace.delete", {"name": "${story}"}),
                     rpc("delete_peer", "server.peer.delete", {})]
    if case.get("isolation"):
        finally_steps.append(rpc("delete_other", "server.peer.delete", {}, "other"))
    return {"version": "gizclaw.test/v1alpha1", "name": f"chat-assistant.tools.{profile_name}.{case['id']}",
            "clients": clients, "variables": variables, "repeat": repeat, "timeout": "12m",
            "steps": steps, "finally": finally_steps}


def generate(directory, repeat=3, case_filter=""):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    all_cases = cases()
    requested = set(case_filter.split(",")) if case_filter else set()
    unknown = requested - {case["id"] for case in all_cases}
    if unknown:
        raise ValueError("Unknown Chat E2E cases: " + ", ".join(sorted(unknown)))
    selected = [case for case in all_cases if not requested or case["id"] in requested]
    for profile in ["default", "testing"]:
        for case in selected:
            doc = document(case, profile, repeat)
            path = directory / f"{profile}.{case['id']}.giztest.yaml"
            path.write_text("# User Story:\n# As a Raids Chat device owner,\n# I want the shipped real-model Chat to use its bound Tools,\n# So that exact typed receipts prove the requested action and current Peer isolation.\n" +
                            yaml.safe_dump(doc, allow_unicode=True, sort_keys=False))
    return len(selected) * 2 * repeat


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory")
    options = parser.parse_args()
    print(f"generated {generate(options.directory, repeat=1)} Chat Tool Giztest documents")
