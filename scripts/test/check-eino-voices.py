"""Check cross-resource spoken Eino Voice ownership without provider access.

Resource YAML schemas are checked by GizClaw; these checks cover the catalog's
canonical scalar/default Voice and RuntimeProfile binding layout using stdlib.
"""
import json
import re
import subprocess
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
    text = re.split(r"^    \S", text, maxsplit=1, flags=re.M)[0]
    aliases = re.findall(r"^      ([^\s:]+):", text, re.M)
    assert len(set(aliases)) == len(aliases), f"{path}: duplicate Voice alias"
    # Profiles can share bindings through YAML anchors (Journey variants).
    # Ruby/Psych is already used by the catalog closure checks and is offline.
    result = subprocess.run(
        ["ruby", "-ryaml", "-rjson", "-e",
         "puts JSON.generate(YAML.load_file(ARGV[0]).fetch('spec').fetch('resources').fetch('voices'))",
         str(path)], check=True, capture_output=True, text=True,
    )
    return {alias: binding["resource_id"] for alias, binding in json.loads(result.stdout).items()}


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
            # Multi-role resource IDs retain the full suffix; aliases use -mr
            # to fit the alias-length contract enforced by voice-bindings.rb.
            namespace = impl["workflow_id"]
            if impl["file"].endswith(".multi-role.yaml"):
                namespace = namespace.removesuffix("-multi-role") + "-mr"
            alias = namespace + "." + role
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
