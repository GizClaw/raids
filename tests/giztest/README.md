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
#921, #923). `make test-unit-resources` validates the corpus offline.

## Layout

One directory per scenario (raid), mirroring `workflows/<raid>/`, with one
`.giztest.yaml` per engine implementation or per single-client case:

```text
tests/giztest/<raid>/<engine>.giztest.yaml            # relay: candidate <engine> vs. workflows/<raid>/test.yaml
tests/giztest/<raid>/<engine>.<case>.giztest.yaml     # extra scenarios for the same implementation
tests/giztest/ast-translate/<pair>.<case>.giztest.yaml
tests/giztest/doubao-realtime/conversation.<case>.giztest.yaml
tests/giztest/h106/…                                  # targets outside this catalog
```

| Group | Files | Topology |
| --- | --- | --- |
| 30 story/adventure raids × `flowcraft` + `eino` | 60 | `workspace_relay` against the raid's `<raid>-test` Tester |
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
Tester), selects both, and runs one `workspace_relay` step with
`first_client: tester`. The Tester receives the brief, emits the first scripted
player message, and the runner forwards every assistant text fragment as the
other side's user input until `max_turns = 2N + 1` completed responses (N
candidate replies, N scripted player turns, one verdict).

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

- Eino History is capped at 50 messages. Only Murder Mystery (26 responses)
  crosses it: the turn index still resolves through scripted-message matching,
  but the final audit and judge prompt see the latest 25 rounds only.
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
APPLY=1 GIZCLAW_CONTEXT=dev make test-e2e RAID=story-aesop

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
