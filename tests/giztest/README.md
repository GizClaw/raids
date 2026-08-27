# Declarative Giztest corpus

Every Raids live test is one `gizclaw.test/v1alpha1` document under this
directory. `gizclaw test run <dir> --parallel N` gives each file (and each
`repeat` task) its own ephemeral Peers, Workspaces, variables, and bounded
`finally` cleanup, so one cluster can run the whole catalog concurrently under
one global worker pool. This corpus replaced the retired `tools/raidtest` Go
runner, which owned paired, catalog, and default qualification before the raid
package layout.

Requires GizClaw v0.6.0 or later, the first release containing the declarative
runner, assertion matchers, and `workspace_relay` operation (GizClaw #916,
#921, #923). The bounded story-role latency probes additionally require the
`peer_stream.completion: first_response` contract from GizClaw #991/#992,
first released in v0.7.13. CI uses GizClaw v0.7.19, which also contains the
RuntimeProfile reload repair from GizClaw #994/#997 and the modality-selective
first-response contract from GizClaw #1003/#1004 for text-only Eino probes.
`make test-unit-resources` validates the corpus offline.

## Layout

One directory per scenario (raid), mirroring `workflows/<raid>/`, with one
`.giztest.yaml` per engine implementation or per single-client case:

```text
tests/giztest/<raid>/<engine>.giztest.yaml            # relay: candidate <engine> vs. workflows/<raid>/test.yaml
tests/giztest/<raid>/<engine>.realtime.giztest.yaml   # paced-audio RealTime roundtrip for that implementation
tests/giztest/<raid>/<engine>.<case>.giztest.yaml     # extra scenarios for the same implementation
tests/giztest/ast-translate/<pair>.<case>.giztest.yaml
tests/giztest/doubao-realtime/conversation.<case>.giztest.yaml
tests/giztest/h106/…                                  # targets outside this catalog
```

| Group | Files | Topology |
| --- | --- | --- |
| 30 story/adventure raids × `flowcraft` + `eino` | 60 | `workspace_relay` against the raid's `<raid>-test` Tester |
| 30 story/adventure raids × `flowcraft.realtime` + `eino.realtime` | 60 | warmed, paced-audio RealTime roundtrip; Flowcraft enforces 2 s text / 3 s audio first response and Eino enforces 2 s text first response |
| 19 `story-*` Flowcraft role probes | 19 | three isolated narrator/character Workspaces requiring complete text/audio EOS evidence plus bounded 2 s text / 3 s audio first-response probes |
| `story-aesop/flowcraft.transitions` | 1 | stateful natural-progress, negated-choice, adjacent-transition, and same-chapter continuation contract |
| `story-wizard-oz/english-restart*` | 2 | direct Flowcraft audio plus Eino relay preserving English restart and non-reset continuation |
| `journey-guide/` (`flowcraft`, `eino-history`, `eino-memory-recall`, `eino-memory-async`, `flowcraft.benchmark-6s`) | 5 | 4 relays sharing `journey-guide-test` + 1 single-client TTFT benchmark |
| `murder-mystery/`, `chat-assistant/`, `pet-care/` | 3 | relay (pet-care adopts a run-owned Pet) |
| `doubao-realtime/` | 2 | single client, realtime audio |
| `ast-translate/` | 8 | single client, push-to-talk audio, one per direction |
| `h106/` | 2 | single client; external targets |

The giztest files live beside `tests/giztest` rather than inside `workflows/`
only because the deploy catalog walker reads every `*.yaml` under `workflows/`
as an Admin resource; once it skips `*.giztest.yaml` they move next to the
Workflows they test.

## Relay protocol

A paired file creates two Workspaces from the stable `testing` RuntimeProfile
(`raidtest-targets` collection for the candidate, `raidtest-testers` for the
Tester), selects both, and runs bounded `workspace_relay` steps with
`first_client: tester`. The Tester receives the brief, emits the first scripted
player message, and the runner forwards every assistant text fragment as the
other side's user input until a checkpoint. Story segments end in strict
`CHECKPOINT PASS`; their final segment ends in strict `PASS`.

Every product-under-test Workspace is explicitly warmed with
`server.run.workspace.reload` before its first conversational operation. The
reload constructs the selected Agent without adding a user or assistant turn,
so cold-start time stays visible as a dedicated setup step while TTFT and first
audio assertions measure the ready runtime. Relay Tester Workspaces are not
warmed: they are test drivers rather than latency targets, and retaining their
original lifecycle avoids changing the judge's long-form semantic behavior.
Reloads that are part of a scenario's persistence contract remain separate
later steps and are not replaced by this initial warm-up.

### RealTime roundtrip contract

Every story/adventure implementation has an independent
`<engine>.realtime.giztest.yaml`. The document synthesizes one short Chinese
Opus fixture, pushes it through `peer_stream mode: realtime` at 20 ms pacing,
and verifies a non-empty terminal assistant response after an explicit warm-up.
Flowcraft already declares an ASR/TTS `voice_adapter`, so its terminal check
requires text EOS, audio EOS, and positive audio bytes; a second
`completion: first_response` turn requires text within 2 seconds and audio
within 3 seconds. Eino remains text-only: its Workflow declares `asr_model:
asr` for realtime input, while the test sets `require_audio: false` and requires
non-empty assistant text plus text EOS. A second text-only
`completion: first_response` turn requires Eino text within 2 seconds while
leaving audio out of the acceptance contract. This avoids representing absent
Eino TTS as an audio pass.

The relay-protocol Tester Workflows (`workflows/<raid>/test.yaml`, one per
scenario and shared by its Flowcraft and Eino implementations) are generated
from the previous Tool-protocol Testers and plans and share one Eino graph: `route-turn` (Starlark) → `build-prompt` → `judge-model` → `finalize`.

- `route-turn` derives the turn index from its own History (`input.messages`):
  the last assistant message is matched against the scripted request list, with
  the assistant-message count as fallback. Scripted turns emit the exact
  request; `intent` turns (Journey `river`/`shelter`) ask the model for one
  grounded player utterance.
- The final turn re-reads the whole visible transcript, runs the plan's
  deterministic contracts (required / required_any / forbidden / rune window,
  ported from the retired runner's deterministic checks), and builds one holistic judge
  prompt from the scenario rules and per-checkpoint contracts.
- `finalize` makes the output deterministic: scripted text passes through
  unchanged, generated utterances are trimmed to one line, and the verdict is
  reduced to exactly `PASS` or `FAIL`. Any deterministic failure forces `FAIL`
  regardless of the model's opinion.

### Long story and role-probe contract

Each of the 18 ordinary story pairs runs 16 target responses, checkpoints at
response 8, reloads the candidate before response 9, then verifies the current
chapter and corrected durable state at response 16. Arabian Nights runs 64
responses with checkpoints at 8, 16, 32, and 48, reloads before response 33,
and ends at response 64. Checkpoints keep each audit inside the 50-message Eino
History window; a missing round, deterministic failure, timeout, or non-strict
verdict fails that segment.

Every `flowcraft.roles.giztest.yaml` uses three isolated Workspaces so a prior
speaker cannot influence the next probe. The narrator Workspace also proves
that a fresh direct chapter-two request remains in chapter one until the
completion conditions are satisfied. A natural direct request reaches the
narrator or one named character, while `peer_stream mode: text` requires text
EOS, audio EOS, positive `audio_bytes`, and role-specific text. After each
role's complete semantic response, a final
`peer_stream.completion: first_response` step on that isolated Workspace
requires the first non-empty assistant text within 2 seconds and the first
non-empty assistant audio within 3 seconds. The runner closes that latency-only
stream after both signals; it does not replace or weaken the preceding terminal
semantic check. The report supports “expected role/alias backed by static
mapping”; it does not expose the selected alias or prove voiceprint similarity.

Giztest owns the transport evidence: `/terminal/text` must match `^\s*PASS\s*$`,
`/completed_turns` and per-client counts must match the route, and the
`/turns/candidate/{first_text_ms,text_runes}` `{min,max}` aggregates carry the
plan's 6 s TTFT gate and the global rune window. Reports never contain relayed
text, prompts, or Tester reasoning.

### Reload and recall barriers

Plans with `reload_before` split into two relay steps: the first ends on the
candidate's response before the reload (`terminal_client: candidate`), its
terminal text is captured into `reload_handoff`, `server.run.workspace.reload`
restarts the candidate, and the second relay feeds that handoff to the Tester
so its History stays continuous. `persisted_before_reload` facts become one
`server.run.workspace.recall` step per fact that expects `/available: true` and
non-empty `/hits` before the reload.

### Known limits of the relay migration

- Eino History is capped at 50 messages. Long stories therefore use bounded
  checkpoint segments; Murder Mystery still crosses the window and its final
  audit sees the latest 25 rounds only.
- The recall barrier is a single RPC after the first relay segment; the retired
  runner polled until `persistence_timeout`. A configurable retry on RPC steps is a
  pending GizClaw request.
- Murder Mystery's previously free-form investigation turns are now fixed
  scripted sentences (the `REQUESTS` list inside
  `workflows/murder-mystery/test.yaml`) so the route stays
  deterministic and index-stable.
- Realtime (Doubao) and AST translation scenarios are single-client audio runs:
  they keep every keyword, rune, script, latency, and audio-present gate but no
  longer carry the external LLM judge dimensions. Script checks (`han`,
  `latin`, `japanese`, `korean`) are presence patterns (`\p{Han}` …) rather than
  the retired runner's letter-ratio thresholds.
- `h106/` targets are not part of this catalog and are not provisioned by
  `APPLY=1 make test-e2e`; `RAID=all` skips the directory, and running it with
  `RAID=h106` requires a deployment whose `testing` profile exposes those
  Workflows in the `assistants` collection.

## Running

```sh
# 1. Point the runner at a deployment: the Peer access point and the value of
#    the RegistrationToken it bootstraps with.
export GIZCLAW_TEST_ENDPOINT=<host:port>
export GIZCLAW_TEST_REGISTRATION_TOKEN=<testing-runtime token>

# 2. Smoke: one raid, serial. APPLY=1 provisions the testing closure first
#    (Admin authority; GIZCLAW_CONTEXT selects the context).
APPLY=1 GIZCLAW_CONTEXT=e2e-server-volc-bj-01 \
  GIZCLAW_TEST_ENDPOINT=edge-bj-01.e2e.gizclaw.com:9821 \
  make test-e2e RAID=story-aesop PARALLEL=3

# 3. Full catalog wave through the global worker pool.
make test-e2e PARALLEL=8
```

`make test-e2e` validates the selected scenarios offline first, then writes a
redacted JSON report under `tests/giztest/reports/` (ignored by git) unless
`REPORT=<path>` is given. No endpoint or token is baked into a script or a
scenario: every document declares them as Giztest input variables
(`env: GIZCLAW_TEST_ENDPOINT`, `env: GIZCLAW_TEST_REGISTRATION_TOKEN`, the
latter `secret: true` so reports redact it), so the same checkout drives dev,
e2e, or a local stack from the environment alone. The `testing-runtime` token in
`registration-tokens/testing.yaml` is a committed Dev/E2E-only value, not a
production credential.

## Provenance

The corpus and the relay Testers were produced once, mechanically, from the
the retired runner's plans, suites, and Tool-protocol Testers; the generator was
a migration aid and is not part of the repository. The generated files are now
the source of truth: edit a `.giztest.yaml` or a Tester directly and re-run
`make test-unit-resources`. Each route's contracts stay readable in
`workflows/<raid>/README.md` and in the Tester's own `CONTRACTS` list.
