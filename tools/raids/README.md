# raids

`raids` is the Raids package manager. A raid package is one directory
`workflows/<raid>/` with a `raid.json` manifest, one Workflow per engine
implementation (`flowcraft.yaml`, `eino.yaml`, …), the scenario's shared
Tester (`test.yaml`), and a README. The manifest declares the package's
implementations and the **slots** each one needs — model aliases, voice
aliases, and the MemoryLayout it depends on — without binding them to concrete
resources. `raids install` binds those slots inside a RuntimeProfile.

The tool only edits RuntimeProfile YAML (yaml.v3 node-level edits that keep
unrelated content, order, and flow styles). It never contacts a Server; Terraform
or `gizclaw admin apply` deploy the result.

```sh
make build-raids            # tools/raids/raids
make check-raids            # validate every raid.json and both committed profiles (part of make ci)

raids validate                               # all raid.json manifests
raids list  --profile runtime-profiles/default.yaml
raids check --profile runtime-profiles/default.yaml --profile runtime-profiles/testing.yaml

raids install story-aesop --impl flowcraft --profile runtime-profiles/default.yaml \
  --collection story-teller \
  --set model.flowcraft-story-aesop.model=doubao-seed-2-0-lite \
  --set voice.flowcraft-story-aesop.storyteller=volc-tenant:volc-cn-beijing:zh_female_shaoergushi_mars_bigtts

raids install story-aesop --impl eino --tester --profile runtime-profiles/testing.yaml \
  --collection raidtest-targets \
  --set model.eino-story-aesop.model=doubao-seed-2-0-lite \
  --set model.story-aesop-test.model=doubao-seed-2-0-lite

raids uninstall story-aesop --impl eino --tester --profile runtime-profiles/testing.yaml

# The committed profiles are generated: a raid-free base + an install plan.
profile-plans/regenerate.sh            # raids generate --plan profile-plans/*.plan.yaml
profile-plans/regenerate.sh --check    # what CI runs: fail when runtime-profiles/*.yaml are stale
```

`profile-plans/<id>.base.yaml` holds everything raid packages do not own
(system Workflows, `asr`, extraction aliases, translation/assistant/chatroom
bindings, memories, gameplay, tools); `profile-plans/<id>.plan.yaml` lists the
`raids install` calls (raid, impl, collection, binding name, tester, slot
values). `raids generate` replays the plan on the base and writes the
`output`; the profile text comes from each `raid.json`, so editing a manifest
and regenerating updates every profile consistently.

`install` upserts the Workflow binding under `--name` (default: the Workflow
id; `default.yaml` for example binds `flowcraft-story-aesop` as `story.aesop`
in the `story` collection) with the manifest's `title`/`summary` as `i18n`
(`--display-name`/`--description <lang>=<text>` override it; existing text is
kept otherwise), every model/voice alias slot, and — with `--tester` — the
`<raid>-test` binding in `raidtest-testers` (override with `--tester-collection`).
Missing slot values are an error that lists them; existing bindings are kept
when no `--set` overrides them; resource ids must exist under `models/`,
`voices/`, and the implementation's MemoryLayout binding must already be present
in `spec.resources.memories` (driver/connection are deployment policy).
`uninstall` removes every binding of the implementation (or only the one in
`--collection`) and drops its alias slots once no binding remains. `check` fails when an installed
implementation has a missing slot or a binding to a resource that is not in the
catalog; `--dry-run` prints the edited profile instead of writing it.

## raid.json

```json
{
  "schema": "raids.raid/v1alpha1",
  "id": "story-aesop",
  "category": "story",
  "title": {"en": "Aesop's Fables", "zh-CN": "伊索寓言"},
  "summary": {"en": "…", "zh-CN": "…"},
  "rating": {"age": "6+", "scheme": "raids-age-v1", "content": ["mild-peril"]},
  "tags": ["fable", "animals"],
  "language": ["zh-CN"],
  "implementations": {
    "flowcraft": {
      "file": "flowcraft.yaml", "workflow_id": "flowcraft-story-aesop", "driver": "flowcraft",
      "input": ["text", "push-to-talk"],
      "memory": {"layout_id": "story-teller"},
      "parameters": {
        "models": {"flowcraft-story-aesop.model": {"kind": "llm", "role": "narrator", "description": "…"}},
        "voices": {"flowcraft-story-aesop.storyteller": {"role": "storyteller", "language": "zh-CN", "description": "…"}}
      }
    }
  },
  "tester": {"file": "test.yaml", "workflow_id": "story-aesop-test", "driver": "eino",
             "parameters": {"models": {"story-aesop-test.model": {"kind": "llm", "role": "judge"}}},
             "route": {"responses": 13, "checkpoints": ["opening", "…"]}},
  "tests": [{"file": "tests/giztest/story-aesop/flowcraft.giztest.yaml", "implementation": "flowcraft", "topology": "relay", "reload": true}]
}
```

`go test ./...` proves the tool against the committed profiles: rendering a
profile through the tool is byte-identical, and uninstalling plus reinstalling
every raid implementation of `testing.yaml` and `default.yaml` with the values
read from the file reproduces the same bindings and resource ids.

Rules enforced by `raids validate`: the id matches the directory; every
implementation/tester file is a `Workflow` whose `metadata.id` matches; slot
aliases are namespaced by their Workflow id (`<workflow-id>.<role>`); the tester
id is `<raid>-test`.
