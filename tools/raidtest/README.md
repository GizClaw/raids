# raidtest

`raidtest` runs a local Raids Workflow against a real GizClaw Server without
overwriting the deployed Workflow. It is a candidate validator, not a catalog
installer, deployment tool, or replacement for complete product E2E.

## Build

The module pins `gizclaw-go v0.3.3`, which provides the generic Admin Resource
API, Workspace Toolkit policy, and Peer `client_rpc` handlers used by paired
acceptance. Its
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
Use `make build-raidtest` for live qualification: it injects the repository
revision and pre-build dirty state because Go does not discover VCS metadata
automatically from this nested module. `RAIDTEST_OUTPUT=/absolute/path` writes
the candidate outside the checkout without changing that evidence.

The race detector requires CGO and the real Git LFS payloads from the exact
`gizclaw-go v0.3.3` tag. Preserve the repository-relative resource layout in a
temporary tree so tests can still resolve the checked-in suite resources, and
so `go mod edit` does not mutate this checkout:

```sh
RACE_ROOT=$(mktemp -d)
git clone --depth 1 --branch v0.3.3 https://github.com/GizClaw/gizclaw-go.git "$RACE_ROOT/gizclaw-go"
git -C "$RACE_ROOT/gizclaw-go" lfs pull
mkdir -p "$RACE_ROOT/raids/tools"
cp -R tools/raidtest "$RACE_ROOT/raids/tools/raidtest"
cp -R workflows runtime-profiles registration-tokens tool-resources memory-layouts "$RACE_ROOT/raids/"
cd "$RACE_ROOT/raids/tools/raidtest"
go mod edit -replace "github.com/GizClaw/gizclaw-go=$RACE_ROOT/gizclaw-go"
go test -race ./...
```

## Run

```sh
export RAIDTEST_ADMIN_PRIVATE_KEY='private key text supplied by the operator'

./raidtest run \
  --server server-bj-01.dev.gizclaw.com:9820 \
  --peer-server edge-bj-01.dev.gizclaw.com:9821 \
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

Flowcraft and Eino scripted Workflows use distinct plan drivers so a benchmark
cannot accidentally run against the wrong engine. The public Eino Journey
Workflows under `../../workflows/eino` use the same Default Model resource and
`max_tokens: 2048`, but vary History and Memory work to isolate first-response
latency. The Eino benchmark plan deliberately leaves `workflow_id` unset so
the same turns and judge dimensions apply to all three Eino variants. The
matching benchmark plans require the first non-empty assistant
text token within six seconds. This metric is text TTFT; it is not first-audio
latency. Eino's public Workflow schema currently has no Flowcraft-compatible
`voice_adapter`, so these Workflows qualify the text path rather than claiming
drop-in spoken Journey parity.

Plans marked `paired: true` contain only checkpoint order, reload/Recall
barriers, deterministic facts and rune limits, and latency gates. Natural
player messages and semantic judgment live in each target's dedicated Eino
Tester Workflow rather than being duplicated in an external plan. Committed
paired plans cover Aesop, Alice in Wonderland, Space Rescue, Monster Maze, and
Castle Mystery with thirteen target responses each, including the formal
opening. Raidtest
creates an isolated GizClaw Workspace for every Workflow case; one turn in each
plan reloads that same Workspace and checks the durable chapter, stage, or area.
The Eino variants use History and Memory Recall, an invocation-local
deterministic route script, one narrator model, a progress extraction script,
and asynchronous Memory observation. This keeps explicit graph progress and
durable state without a redundant 2-pass model chain on the response path.

## Paired Eino Tester suite

Issue #62's suite runs each candidate Workflow against its own independent Eino
Tester in the same GizClaw cluster:

```sh
export RAIDTEST_ADMIN_PRIVATE_KEY='private key text supplied by the operator'

./raidtest run \
  --server server-bj-01.dev.gizclaw.com:9820 \
  --peer-server ap.dev.gizclaw.com:9821 \
  --admin-private-key-env RAIDTEST_ADMIN_PRIVATE_KEY \
  --suite suites/pr61-paired.yaml \
  --report pr61-paired-report.json
```

Repeat `--pair <target-workflow-id>` for a smoke subset. Omitting it runs the
entire suite; the release qualification uses the unfiltered command.

To select a memory provider for a suite run, pass a complete RuntimeProfile
resource with `--runtime-profile-file`, or set `RAIDTEST_RUNTIME_PROFILE_FILE`
to that file path. The runner rewrites its ID, creates a run-owned
RuntimeProfile and RegistrationToken, and deletes both after the run. `--keep`
retains them for diagnosis. This makes the provider choice explicit in the
RuntimeProfile (for example, `driver: volc_mem0`) without changing the deployed
`default` or checked-in `testing` profile. Keep provider credentials out of the
repository and supply the rendered profile through the test environment.

Paired suite cases are serial by default. Dev-only stall reproduction may use
bounded case concurrency after a healthy serial baseline:

```sh
./raidtest run \
  --server server-bj-01.dev.gizclaw.com:9820 \
  --peer-server ap.dev.gizclaw.com:9821 \
  --admin-private-key-env RAIDTEST_ADMIN_PRIVATE_KEY \
  --suite suites/pr61-paired.yaml \
  --case-parallelism 4 \
  --case-ramp-up 250ms \
  --diagnostic-probe-interval 1s \
  --keep \
  --report parallel-4.json
```

`--case-parallelism` accepts `1..8`; each case owns two Peers and two
Workspaces, so the cap permits at most 16 of each case-owned resource at once.
`--case-ramp-up` delays each admission after the first and rejects negative
durations. `--diagnostic-probe-interval` is disabled at `0`; enabled values
must be at least `100ms`. All three flags are suite-only, including when an
explicit default value is supplied.

The sampler performs an immediate credential-free request to the Peer
`/server-info` endpoint before case admission. It classifies 2xx, HTTP errors,
timeouts, and sanitized transport failures without retaining headers or bodies.
The first unhealthy transition stops new admissions but does not overwrite
active-case ownership; active cases finish their bounded cleanup or retain
path. Parent cancellation also stops admission and cancels active case
contexts. Independent case failures remain non-fail-fast while the probe is
healthy.

Reports keep `raidtest.report/v1` and add candidate VCS metadata, configured and
peak concurrency, selected/admitted counts, per-case UTC intervals, the first
failure, and coalesced probe transitions. Cases, lifecycle groups, companion
reports, terminal output, and joined errors remain in suite ordinal order even
when cases finish out of order. A missing revision or dirty local binary is
useful for diagnostics but is not accepted live-qualification evidence.

Run the complete suite separately at `N=1` with ramp `0`, then—only after
manual report and Server-health review—at `N=2`, `4`, and `8` with a `250ms`
ramp. Never automate advancement between levels. Stop after the first matching
EOF plus `/server-info` timeout/5xx signature or after one complete `N=8` run.

Raids does not collect process profiles. GizClaw v0.5.2 production Dev must
already be writing its private startup baseline and five-minute
heap/allocs/goroutine sets to the deployment-owned `process-profiles`
ObjectStore. Candidate validation disables that collector. Operators correlate
completed manifest-verified profile sets and Server logs with the report run ID
and UTC interval; missing or mismatched profile evidence makes that live step a
`SKIP`. No profile, ObjectStore credential, or arbitrary network error is
written to a raidtest report.

Suite mode applies the stable `testing` RuntimeProfile,
`testing-runtime` RegistrationToken, `raidtest-acceptance-report` Tool,
the 14 canonical targets, and their 14 `<target>-test` Eino Workflows. Apply
is an idempotent in-place Dev update; these stable resources are retained.
Every repeat creates distinct target and Tester peers and Workspaces. Every
target Workflow carries an explicit deny-all Toolkit policy (the v0.3.3 RPC
readback may omit an empty Workspace override), while the Tester Workspace
exposes only the scoped `raidtest-acceptance-report` binding. Admin resource
digests and static policy validation reject any target widening or missing
Tester allowlist; the v0.3.3 `GetWorkspace` response does not expose either
Workspace policy reliably. Its
`raidtest_acceptance_report` Peer handler validates correlation and records
the Tester's ToolCall before relaying `next_message` to the target. Each Tester
invocation receives the runner's explicit target transcript through the current
payload and does not replay its own acknowledgement history. `target_history`
contains only previously completed target turns; `target_request` carries the
actual current player utterance, and the current target reply is present exactly
once in `target_response` on the `TARGET_RESPONSE` envelope. This preserves
cross-turn evidence without losing the request under judgment, duplicating the
answer, or degrading Tool selection in long episodes. A correlated ToolCall
remains authoritative even when the Tester emits no trailing assistant prose.

The paired path never creates, updates, shadows, or deletes MemoryLayouts or
provider connections. It reuses and verifies the `story-teller` and `adventure`
bindings declared by the live stable testing Profile. The checked-in `default`
and `testing` Profiles currently declare `driver: flowcraft` with
`connection.type: flowcraft_bbh`; suite mode neither replaces that binding nor
infers which vendor service may exist behind Flowcraft. The checked-in
MemoryLayouts remain deployment inputs: their asynchronous Flowcraft write mode
keeps extraction off the response path, but this suite does not apply or claim
live qualification of that setting. Apply/readback digests
and pre-turn `candidate_changed` barriers stop a pair if a canonical resource
drifts concurrently. It also rejects all external OpenAI
agent, judge, TTS, and key flags: dialogue generation and semantic acceptance
come from the cluster's configured Eino models. External mechanics still gate
target text TTFT at six seconds and total response time at ninety seconds.
Murder Mystery keeps its complete dialogue in the configured Flowcraft History
store and observes only the explicit corrected shoe-size state into the reused
Memory provider. This avoids a redundant whole-transcript extraction after the
reply is already published while preserving the pre-reload Recall proof.
Timing and intermediate semantic failures are retained per response while the
Tester continues the declared route. This prevents one early violation from
hiding later history, correction, reload, or conclusion failures. Only the
final Tester response terminates the route with `pass` or `fail`; that action
describes the final response, while the runner aggregates every retained Tool
check and external timing result into the case status.

Five story/adventure pairs run 13 target responses per engine, the three Eino
Journey variants run 10 target responses each, and Murder Mystery runs 26
target responses with a durable `39码` recall barrier and reload before
response 20. Every story/adventure engine target repeats in three independently
isolated peer/Workspace pairs; Murder Mystery repeats in five. Their Testers
parse the active checkpoint deterministically, route to bootstrap, evidence,
correction, challenge, conclusion, or Tool-retry judging, and carry two
scenario-specific negative-control rules for stale facts and unsupported
behavior. Reports retain complete target and Tester text, Tool
checks and evidence, separate target/Tester timings, both Peer/Workspace IDs,
resource digests, ownership attribution, credential-scan status, and lifecycle
failures. The aggregate report and every `<report-base>.d/<case>.json` file use
mode `0600`; the companion directory uses mode `0700`.

`--server` is the authoritative Admin control-plane endpoint. When peers reach
the Server through a separate Edge ingress, pass that address with
`--peer-server`; it defaults to `--server` for single-endpoint deployments.

The plan's `workflow_id` selects only cases owned by the supplied Workflow.
For `plans/default/translations.yaml`, run the command once for each of the
seven AST Workflow files; the bidirectional auto Workflow executes both of its
directional cases in one run.

Add `--agent-model` to generate turns that provide only an `intent`, or
`--judge-model` for semantic checks. The default base URL is the Peer/Edge
`/openai/v1` surface; without an OpenAI key source, `raidtest` exchanges its
temporary Peer identity for a short-lived cluster session bound to the candidate
profile by the run-owned registration token. It verifies requested Model and
Voice aliases before the first turn. External OpenAI-compatible endpoints still
require an explicit key source. Explicit model IDs are recorded in the report.
Semantic checks receive a bounded, chronological transcript of the completed
turns in the current Case, including failed turns, so continuity and correction
judgments can evaluate the current answer against what actually happened. The
same bounded history grounds generated player utterances so the simulator cannot
invent prior testimony or evidence while asking a follow-up question.

Realtime and AST translation Workflows require spoken input. Pass an OpenAI
speech model with `--input-tts-model` and a Voice with `--input-tts-voice`.
For the cluster endpoint, the Voice is a RuntimeProfile alias; for an external
endpoint, use that provider's model, Voice, and key. `raidtest` requests Ogg
Opus, extracts the raw Opus packets, and sends them to the Peer in paced 20 ms
frames. Each utterance is synthesized once per run and reused across modes so
PTT and realtime compare the same audio fixture. AST acceptance runs create
separate `push-to-talk` and `realtime` Workspaces by default. Repeat
`--ast-input-mode` to restrict that matrix, for
example `--ast-input-mode realtime` or both explicit values. Push-to-talk must
publish nothing before input EOS; realtime reads provider events concurrently
with paced audio input and records whether its first response preceded input
EOS. The tool never treats a text-only echo as translation evidence.
Successive turns in one Case reuse the same Peer stream, matching a device's
long-lived conversational connection; selecting or reloading a Workspace
closes that stream and establishes a new one.
Plans that require durable post-reload memory can declare
`persisted_before_reload` and `persistence_timeout`. Before reloading, raidtest
polls the Workspace Recall RPC until every declared fact is retrievable or the
bounded checkpoint fails. This preserves asynchronous response-path writes
without mistaking an arbitrary sleep or same-stream history for durable recall.
The committed Default AST matrix runs ten utterances in each of eight language
directions: 80 logical turns, or 160 mode-specific turns per environment. This
qualifies sustained translation transport and output invariants; it does not
claim to evaluate narrative direction or long-form conversational quality.

## Lifecycle and reports

The legacy single-candidate lifecycle is:

1. upload and read back the shadow Workflow and local MemoryLayouts;
2. rewrite the source Workflow and supplied memory aliases in a shadow
   RuntimeProfile, then upload and read it back;
3. create a random RegistrationToken bound to that shadow profile;
4. register a random peer through `--peer-server`, create one owner-scoped
   candidate Workspace per Case through Peer RPC, and select it; AST creates
   one isolated Workspace per Case and requested input mode, so conversation
   history cannot leak between independent scenarios;
5. run every independent case to a terminal status;
6. delete Workspace, token, profile, Workflow, and MemoryLayouts in reverse
   dependency order, then delete the peer last, continuing after cleanup
   failures.

`--keep` retains run-owned resources and identifies them in the report. It
never enables in-place updates. JSON reports are mode `0600` and contain
schema version, stable case/turn IDs, source and shadow IDs/digests, timings,
transcripts, deterministic checks, semantic checks, and the full lifecycle
ledger. Deterministic fact, correction, rune, script, and latency failures
remain failures even if a semantic judge likes the answer.

AST plans evaluate raw translated text and require the configured s2s route to
finish with non-empty TTS audio. The committed Default plan is a route-level
acceptance test: it uses simple spoken phrases to gate target-language output,
bounded text, and completed target audio. The deployed provider model has known
variability for names, places, numbers, times, and negation, so exact preservation
of those facts is diagnostic evidence rather than a Raids release gate. The
report records source text, provider source transcript when present, translated
text, AST input mode, input-EOS timing, TTS status, MIME type, and byte count
separately; optional round-trip transcription remains a separate status and
never rewrites the raw translation result. PTT and realtime cases have distinct
IDs and terminal statuses, so one mode cannot hide the other mode's failure.

No credential is committed, expanded from Raids Credential YAML, serialized
into a report, or deliberately printed. Treat reports as test artifacts
because their transcripts can still contain user-supplied content.
