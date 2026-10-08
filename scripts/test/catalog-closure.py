"""Check catalog resource references against both shipped RuntimeProfiles."""
import json
from pathlib import Path

import yaml


def check(condition, message):
    if not condition:
        raise SystemExit(message)


def walk(value):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk(child)


resources = {}
retired = "flow" + "craft"
directories = ("credentials", "tenants", "models", "voices", "memory-layouts",
               "tools", "workflows", "runtime-profiles", "registration-tokens")
files = sorted(file for directory in directories for file in Path(directory).rglob("*.yaml"))
files.append(Path("runtime-profile.example.yaml"))
for file in files:
    document = yaml.safe_load(file.read_text())
    check(retired not in file.name.lower() and retired not in json.dumps(document).lower(),
          f"{file}: retired configuration or reference")
    identity = (document["kind"], document["metadata"]["id"])
    check(identity not in resources, f"{file}: duplicate Resource {identity}")
    resources[identity] = document

for file in sorted(Path("workflows").glob("*/raid.json")):
    manifest = json.loads(file.read_text())
    check(retired not in json.dumps(manifest).lower(), f"{file}: retired manifest entry")
    for implementation in manifest["implementations"].values():
        workflow = resources.get(("Workflow", implementation["workflow_id"]))
        check(workflow is not None, f"{file}: unresolved Workflow")
        check((file.parent / implementation["file"]).is_file(), f"{file}: missing implementation file")
        check(workflow["spec"]["driver"] == implementation["driver"], f"{file}: driver mismatch")
    for test in manifest["tests"]:
        check(Path(test["file"]).is_file(), f"{file}: missing Giztest {test['file']}")

profile_count = 0
for (kind, identifier), document in resources.items():
    if kind != "RuntimeProfile":
        continue
    spec = document["spec"]
    bindings = spec["resources"]
    for group, resource_kind in (("models", "Model"), ("voices", "Voice")):
        for alias, binding in bindings.get(group, {}).items():
            check((resource_kind, binding["resource_id"]) in resources,
                  f"{identifier}: unresolved {group}.{alias}")
    devices = {device["id"]: device for device in spec.get("mhs", {}).get("v0", {}).get("devices", [])}
    for alias, binding in bindings.get("tools", {}).items():
        sources = [source for source in ("resource_id", "mhs", "client_tool") if source in binding]
        check(len(sources) == 1, f"{identifier}: tools.{alias} must select exactly one source")
        if sources[0] == "resource_id":
            check(("Tool", binding["resource_id"]) in resources, f"{identifier}: unresolved tools.{alias}")
        elif sources[0] == "mhs":
            target = binding["mhs"]
            check(target["id"] in devices, f"{identifier}: tools.{alias} references undeclared MHS instance")
            check(target["operation"] in ("read", "write"), f"{identifier}: tools.{alias} invalid MHS operation")
            check(bool(target.get("fields")) if target["operation"] == "write" else "fields" not in target,
                  f"{identifier}: tools.{alias} must select write fields and omit them for reads")
        else:
            check(bool(binding["client_tool"].get("name")), f"{identifier}: tools.{alias} missing ClientTool name")
    for alias, binding in bindings.get("memories", {}).items():
        layout = resources.get(("MemoryLayout", binding["layout_id"]))
        check(layout is not None, f"{identifier}: unresolved MemoryLayout {alias}")
        connection = binding["connection"]["type"]
        check(connection in layout["spec"], f"{identifier}: missing {connection} policy for {alias}")
        driver = "volc_mem0" if connection == "volc_mem0" else "mem0"
        check(binding["driver"] == driver, f"{identifier}: Memory driver/connection mismatch for {alias}")
    for alias, binding in spec["workflows"].items():
        workflow = resources.get(("Workflow", binding["resource_id"]))
        check(workflow is not None, f"{identifier}: unresolved Workflow {alias}")
        workflow_spec = workflow["spec"]
        allowed = binding.get("toolkit", {}).get("tool_names", [])
        check(set(allowed) <= bindings.get("tools", {}).keys(),
              f"{identifier}/{alias}: injected Tool alias is not bound")
        verifier = binding.get("toolkit", {}).get("verification_model")
        if verifier:
            check(verifier in bindings.get("models", {}),
                  f"{identifier}/{alias}: unresolved Tool verification Model")
        if workflow_spec.get("memory") is not None:
            check(workflow_spec["memory"] in bindings.get("memories", {}),
                  f"{identifier}/{alias}: unresolved Memory alias")
        if workflow_spec["driver"] != "eino":
            continue
        eino = workflow_spec["eino"]
        for node in walk(eino["graph"]):
            if node.get("type") in ("chat_model", "match"):
                check(node["model"] in bindings["models"],
                      f"{identifier}/{alias}: unresolved Model {node['model']}")
        adapter = eino.get("voice_adapter", {})
        if adapter.get("asr_model"):
            check(adapter["asr_model"] in bindings["models"], f"{identifier}/{alias}: unresolved ASR")
        voices = list(adapter.get("node_voices", {}).values()) + list(adapter.get("speaker_voices", {}).values())
        if adapter.get("default_voice"):
            voices.append(adapter["default_voice"])
        check(set(voices) <= bindings.get("voices", {}).keys(), f"{identifier}/{alias}: unresolved Voice")
    profile_count += 1

for file in sorted(Path("tests/giztest").rglob("*.giztest.yaml")):
    check(retired not in file.name.lower() and retired not in file.read_text().lower(),
          f"{file}: retired Giztest configuration or reference")
print(f"validated {len(resources)} Resources and {profile_count} complete RuntimeProfile closures")
