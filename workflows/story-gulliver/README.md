# Gulliver's Travels (`story-gulliver`) — 格列弗游记

Learn perspective-taking through worlds with different scales and social rules.

## Workspace safety fence

Every player-facing system prompt starts with the Workspace fence, then a
blank line and the scenario instructions: Flowcraft uses `${board.safety_fence}`;
Eino binds `input.safety_fence` and renders `{safety_fence}` with `f_string`.
This covers all narrator/character paths, prompt branches, and available variants.
At `off`, only two leading newlines remain. Internal routing/memory nodes and
Tester Workflows do not receive the variable. See the root
[contract and GizClaw compatibility requirement](../../README.md#workspace-safety-fence).

## Story contract

- Premise: 从不同尺度和社会规则中学习换位思考。
- Player: an active companion whose current choice and explicit correction override older History or Memory.
- Chapters: 第1章《微小之城》 → 第2章《礼节冲突》 → 第3章《尺度反转》 → 第4章《平等约定》.
- Cast: narrator (visible facts and transitions), 格列佛 (`gulliver`), and 当地向导 (`local-guide`); each character keeps a distinct motive, voice, and knowledge boundary.
- State: current chapter, completed beats, location, active roles, player choices, explicit corrections, durable clues, and unresolved hooks survive the bounded reload.
- Safety and source boundary: distinguish fact, legend, and original fiction; keep peril child-safe and do not reproduce a published translation.
- Repetition boundary: do not repeat acknowledgements, openings, choices, questions, recaps, or moral summaries.

| Chapter | Entry condition | Goal | Allowed beats (at least two) | Transition condition | Ending condition |
| --- | --- | --- | --- | --- | --- |
| 1. 微小之城 | first opening request | resolve this chapter's core tension | observe a concrete consequence; compare the two characters' responses | player resolves the current hook and requests chapter 2 | emit the chapter 2 heading once, followed directly by that chapter's opening scene |
| 2. 礼节冲突 | chapter 1 transition satisfied and player explicitly continues | resolve this chapter's core tension | observe a concrete consequence; compare the two characters' responses | player resolves the current hook and requests chapter 3 | emit the chapter 3 heading once, followed directly by that chapter's opening scene |
| 3. 尺度反转 | chapter 2 transition satisfied and player explicitly continues | resolve this chapter's core tension | observe a concrete consequence; compare the two characters' responses | player resolves the current hook and requests chapter 4 | emit the chapter 4 heading once, followed directly by that chapter's opening scene |
| 4. 平等约定 | chapter 3 transition satisfied and player explicitly continues | resolve this chapter's core tension | observe a concrete consequence; compare the two characters' responses | player confirms a durable choice and one remaining responsibility | remain in chapter 4; keep one post-ending responsibility |

## Implementations and Voice roles

| Workflow | Engine | Output | Voice roles |
| --- | --- | --- | --- |
| `flowcraft-story-gulliver` | Flowcraft | text + TTS | `storyteller`, `gulliver`, `local-guide` mapped to three distinct public Voices |
| `eino-story-gulliver` | Eino | text + audio | `eino-story-gulliver.storyteller` (single default Voice) |

Flowcraft selects exactly one published node per external response. Chapter entry/transition and invalid speaker selection fall back to `storyteller`; direct in-scene requests may select `gulliver` or `local-guide`.

## Acceptance

- Paired Flowcraft and Eino relays each require 16 continuous target responses with a reload before response 9.
- Milestones: 8, 16; intermediate segments end in strict `CHECKPOINT PASS` and the final segment ends in strict `PASS`.
- `flowcraft.roles.giztest.yaml` creates isolated narrator/gulliver/local-guide Workspaces and requires text EOS, audio EOS, non-empty Opus, timing evidence, and direct, speaker-label-free role text.
- `flowcraft.transitions.giztest.yaml` and `eino.transitions.giztest.yaml` prove an opening that names the setting, both characters, and how to play; ordinary progress; a negated choice that stays in chapter 1; an option-only answer that is told to say “进入下一章”; a “进入下一章” request whose chapter 2 heading is followed by story text in the same reply; and same-chapter continuation without a repeated heading.
- Final live evidence must come from the e2e deployment through `edge-bj-01.e2e.gizclaw.com:9821`; dev evidence is diagnostic only.

```sh
GIZCLAW=/absolute/path/to/gizclaw-with-safety-fence GIZCLAW_TEST_CLI=/absolute/path/to/gizclaw-with-safety-fence make test-unit-resources
GIZCLAW=/absolute/path/to/gizclaw-with-safety-fence GIZCLAW_TEST_CLI=/absolute/path/to/gizclaw-with-safety-fence GIZCLAW_CONTEXT=e2e-server-volc-bj-01 GIZCLAW_TEST_ENDPOINT=edge-bj-01.e2e.gizclaw.com:9821 GIZCLAW_TEST_REGISTRATION_TOKEN=<testing-runtime-token> APPLY=1 RAID=story-gulliver PARALLEL=3 make test-e2e
```

## Multi-role implementations

Continuous multi-character narration is available separately; original implementations remain unchanged.

- `eino.multi-role.yaml`: `eino-story-gulliver-multi-role`; Voice aliases: `eino-story-gulliver-mr.storyteller`, `eino-story-gulliver-mr.gulliver`, `eino-story-gulliver-mr.local-guide`, `eino-story-gulliver-mr.king`, `eino-story-gulliver-mr.glumdalclitch`.
- `flowcraft.multi-role.yaml`: `flowcraft-story-gulliver-multi-role`; Voice aliases: `flowcraft-story-gulliver-mr.storyteller`, `flowcraft-story-gulliver-mr.gulliver`, `flowcraft-story-gulliver-mr.local-guide`, `flowcraft-story-gulliver-mr.king`, `flowcraft-story-gulliver-mr.glumdalclitch`.
