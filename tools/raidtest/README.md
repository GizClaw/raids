# raidtest

`raidtest` runs a local Raids Workflow against a real GizClaw Server without
overwriting the deployed Workflow. It is a candidate validator, not a catalog
installer, deployment tool, or replacement for complete product E2E.

## Build

The module pins `gizclaw-go v0.2.5`, the oldest supported target Server. Its
two WebRTC `replace` directives mirror that released SDK's public dependency
contract because Go does not propagate replacements from dependency modules.
The released SDK archive also contains native audio placeholders that are not
needed by raidtest's text Peer stream, so reproducible builds disable CGO:

```sh
CGO_ENABLED=0 go build ./cmd/raidtest
CGO_ENABLED=0 go test ./...
CGO_ENABLED=0 go vet ./...
```

The repository shortcuts are `make build-raidtest` and `make test-raidtest`.

## Run

```sh
export RAIDTEST_ADMIN_PRIVATE_KEY='private key text supplied by the operator'

./raidtest run \
  --server edge-bj-01.dev.gizclaw.com:9821 \
  --admin-private-key-env RAIDTEST_ADMIN_PRIVATE_KEY \
  --workflow ../../workflows/flowcraft/murder-mystery.yaml \
  --runtime-profile default \
  --runtime-profile-file ../../runtime-profiles/default.yaml \
  --memory-layout ../../memory-layouts/adventure.yaml \
  --plan plans/default/murder-mystery.yaml \
  --report murder-report.json
```

`--server`, `--workflow`, `--plan`, and exactly one Admin private-key source
are required. A source can be an environment variable name, a file, or stdin;
raw private keys are intentionally not accepted as flag values. The deployed
base profile defaults to `default`. A local profile file and repeatable local
MemoryLayout files extend the candidate closure.

The plan's `workflow_id` selects only cases owned by the supplied Workflow.
For `plans/default/translations.yaml`, run the command once for each of the
seven AST Workflow files; the bidirectional auto Workflow executes both of its
cases in one run.

Add `--agent-model` to generate turns that provide only an `intent`, or
`--judge-model` for semantic checks. Either option requires an OpenAI key
source. The base URL defaults to `http://<server>/openai/v1`; model discovery
uses `/models`, while an explicit model ID makes reports reproducible.

## Lifecycle and reports

The normal lifecycle is:

1. upload and read back the shadow Workflow and local MemoryLayouts;
2. rewrite the source Workflow and supplied memory aliases in a shadow
   RuntimeProfile, then upload and read it back;
3. create a random RegistrationToken bound to that shadow profile;
4. register a random peer, create its candidate Workspace, and select it;
5. run every independent case to a terminal status;
6. delete Workspace, peer, token, profile, Workflow, and MemoryLayouts in
   reverse order, continuing after cleanup failures.

`--keep` retains run-owned resources and identifies them in the report. It
never enables in-place updates. JSON reports are mode `0600` and contain
schema version, stable case/turn IDs, source and shadow IDs/digests, timings,
transcripts, deterministic checks, semantic checks, and the full lifecycle
ledger. Deterministic fact, correction, rune, script, and latency failures
remain failures even if a semantic judge likes the answer.

AST plans evaluate raw translated text and require the configured s2s route to
finish with non-empty TTS audio. The report records source text, translated
text, TTS status, MIME type, and byte count separately; optional round-trip
transcription remains a separate status and never rewrites the raw translation
result.

No credential is committed, expanded from Raids Credential YAML, serialized
into a report, or deliberately printed. Treat reports as test artifacts
because their transcripts can still contain user-supplied content.
