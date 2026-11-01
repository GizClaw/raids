"""Render the selected science pilot with complete, topic-sized references."""

from __future__ import annotations

import json
from pathlib import Path

import yaml


def references(card: dict) -> list[dict[str, str]]:
    rows = []
    for volume in card["volumes"]:
        for unit in volume["units"]:
            rows.append({"title": unit["title"], "text": unit["title"] + "：" + "；".join(unit["concepts"])})
        for item in volume.get("experiments", []):
            text = ("实验《" + item["title"] + "》；材料：" + "、".join(item["materials"])
                    + "；步骤：" + "；".join(item["steps"]) + "；观察：" + item["observe"]
                    + "；解释：" + item["explain"] + "；安全：" + item["safety"])
            rows.append({"title": item["title"], "text": text})
        for item in volume.get("facts", []):
            rows.append({"title": item["fact"], "text": item["fact"]})
        for item in volume.get("misconceptions", []):
            rows.append({"title": item["wrong"], "text": "常见误解：" + item["wrong"] + "；解释：" + item["right"]})
    rows.extend({"title": item["name"], "text": "科学家（" + item["label"] + "）" + item["name"] + "：" + item["fact"]}
                for item in card["scientists"])
    return rows


def rules(opening: str) -> str:
    return ("你是科学小博士，陪一年级孩子探索；沿最新语种、进度与更正，不编孩子观察。中文初见先说：" + opening + "\n"
            "实验只用所附家庭方案：先材料、安全和预测，再依真实观察逐步解释。"
            "拒绝火电化学品刀具、爬高、尝不明物和直视太阳，改安全观察并请成人帮助。"
            "用生活例子温和纠错；常识可用，史实传说分清，未知直说仍答已知，不编人名日期引语。"
            "口语朗读，不用Markdown；承接已选行动。")


class _Dumper(yaml.SafeDumper):
    pass


def _string(dumper, value):
    return dumper.represent_scalar("tag:yaml.org,2002:str", value, style="|" if "\n" in value else None)


_Dumper.add_representer(str, _string)


def render(repo: Path, standard: str, card: dict, opening: str) -> str:
    document = yaml.safe_load(standard)
    source = (repo / "scripts/learn/templates/science-context.star").read_text()
    rows = references(card)
    index = "可选主题：" + "、".join(unit["title"] for volume in card["volumes"] for unit in volume["units"])
    index += "；家庭实验：" + "、".join(item["title"] for volume in card["volumes"] for item in volume.get("experiments", []))
    for key, value in [("RULES", rules(opening)), ("REFERENCES", rows), ("TOPIC_INDEX", index)]:
        source = source.replace("@@" + key + "@@", json.dumps(value, ensure_ascii=False))
    nodes = document["spec"]["eino"]["graph"]["nodes"]
    node = next(node for node in nodes if node["id"] == "build-prompt")
    node.clear()
    node.update(id="build-prompt", type="script",
                inputs={"text": {"from": "input.text"}, "history": {"from": "input.messages"},
                        "memory": {"from": "recalled"}, "safety_fence": {"from": "input.safety_fence"}},
                outputs={"messages": "answer-messages"}, language="starlark", entrypoint="run", source=source,
                limits={"max_execution_steps": 300000, "timeout": "250ms", "max_input_bytes": 1048576, "max_output_bytes": 1048576})
    nodes.insert(nodes.index(node) + 1, {
        "id": "apply-safety-fence", "type": "prompt",
        "inputs": {
            "safety_fence": {"from": "input.safety_fence"},
            "context": {"from": "answer-messages"},
            "history": {"from": "input.messages"},
        },
        "outputs": {"messages": "answer-messages"}, "format": "go_template",
        "messages": [
            {"role": "system", "template": "{{.safety_fence}}\n\n{{(index .context 0).Content}}"},
            {"placeholder": "history"},
        ],
    })
    edges = document["spec"]["eino"]["graph"]["edges"]
    edge = next(edge for edge in edges if edge["from"] == "build-prompt")
    target = edge["to"]
    edge["to"] = "apply-safety-fence"
    edges.append({"from": "apply-safety-fence", "to": target})
    return yaml.dump(document, Dumper=_Dumper, allow_unicode=True, sort_keys=False, width=120)
