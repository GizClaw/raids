"""Check cross-resource spoken Eino Voice ownership without provider access.

Resource YAML schemas are checked by GizClaw; these checks cover the catalog's
canonical scalar/default Voice and RuntimeProfile binding layout using stdlib.
"""
import json
import re
from pathlib import Path


def scalar(value):
    value = value.strip()
    if value.startswith('"'):
        return json.loads(value)
    if value.startswith("'") and value.endswith("'"):
        return value[1:-1].replace("''", "'")
    return value


def default_voice(path):
    matches = re.findall(r"^      default_voice: (\S+)$", path.read_text(), re.M)
    assert len(matches) == 1, f"{path}: expected one default Voice"
    return matches[0]


def voice_bindings(path):
    text = path.read_text().split("    voices:\n", 1)[1]
    # Stop at the next resource map; do not accept a Model/Workflow binding.
    text = re.split(r"^    \S", text, maxsplit=1, flags=re.M)[0]
    pairs = re.findall(r"^      (\S+):\n        resource_id: ([^\n]+)$", text, re.M)
    assert len(dict(pairs)) == len(pairs), f"{path}: duplicate Voice alias"
    return {alias: scalar(resource_id) for alias, resource_id in pairs}


def main():
    profiles = {
        p: voice_bindings(p)
        for p in (Path("runtime-profiles/default.yaml"), Path("runtime-profiles/testing.yaml"))
    }
    voice_ids = set()
    for p in Path("voices").glob("*/*.yaml"):
        match = re.search(r"^  id: ([^\n]+)$", p.read_text(), re.M)
        assert match, f"{p}: missing Voice ID"
        voice_ids.add(scalar(match[1]))
    count = 0
    for manifest in sorted(Path("workflows").glob("*/raid.json")):
        data = json.loads(manifest.read_text())
        implementations = data["implementations"]
        einos = [v for v in implementations.values() if v["driver"] == "eino"]
        if not einos:
            continue
        flow = implementations["flowcraft"]
        flow_alias = default_voice(manifest.parent / flow["file"])
        role = flow_alias.split(".", 1)[1]
        for impl in einos:
            path = manifest.parent / impl["file"]
            alias = impl["workflow_id"] + "." + role
            assert default_voice(path) == alias, f"{path}: wrong Voice namespace/role"
            declared = impl["parameters"]["voices"]
            assert alias in declared, f"{manifest}: missing {alias}"
            assert declared[alias]["role"] == role, f"{manifest}: wrong Voice role"
            for profile, bindings in profiles.items():
                assert alias in bindings, f"{profile}: missing {alias}"
                assert bindings[alias] in voice_ids, f"{profile}: unresolved {alias}"
                assert bindings[alias] == bindings[flow_alias], f"{profile}: default Voice mismatch for {alias}"
            count += 1
    assert count > 0, "no spoken Eino implementations found"
    print(f"validated {count} Eino default Voices, manifests and profile bindings")


if __name__ == "__main__":
    main()
