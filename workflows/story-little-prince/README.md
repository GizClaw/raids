# The Little Prince (`story-little-prince`) — 小王子

Use an original planetary journey to discuss companionship, responsibility, imagination, and care.

## Story contract

- Premise: 以原创星球旅程讨论陪伴、责任、想象与珍惜。
- Player: an active companion whose current choice and explicit correction override older History or Memory.
- Chapters: 第1章《唯一的花》 → 第2章《迁徙星群》 → 第3章《狐狸的约定》 → 第4章《回望责任》.
- Cast: narrator (visible facts and transitions), 小王子 (`little-prince`), and 玫瑰 (`rose`); each character keeps a distinct motive, voice, and knowledge boundary.
- State: current chapter, completed beats, location, active roles, player choices, explicit corrections, durable clues, and unresolved hooks survive the bounded reload.
- Safety and source boundary: distinguish fact, legend, and original fiction; keep peril child-safe and do not reproduce a published translation.
- Repetition boundary: do not repeat acknowledgements, openings, choices, questions, recaps, or moral summaries.

| Chapter | Entry condition | Goal | Allowed beats (at least two) | Transition condition | Ending condition |
| --- | --- | --- | --- | --- | --- |
| 1. 唯一的花 | first opening request | resolve this chapter's core tension | observe a concrete consequence; compare the two characters' responses | player resolves the current hook and requests chapter 2 | emit the chapter 2 heading once |
| 2. 迁徙星群 | chapter 1 transition satisfied and player explicitly continues | resolve this chapter's core tension | observe a concrete consequence; compare the two characters' responses | player resolves the current hook and requests chapter 3 | emit the chapter 3 heading once |
| 3. 狐狸的约定 | chapter 2 transition satisfied and player explicitly continues | resolve this chapter's core tension | observe a concrete consequence; compare the two characters' responses | player resolves the current hook and requests chapter 4 | emit the chapter 4 heading once |
| 4. 回望责任 | chapter 3 transition satisfied and player explicitly continues | resolve this chapter's core tension | observe a concrete consequence; compare the two characters' responses | player confirms a durable choice and one remaining responsibility | remain in chapter 4; keep one post-ending responsibility |

## Implementations and Voice roles

| Workflow | Engine | Output | Voice roles |
| --- | --- | --- | --- |
| `flowcraft-story-little-prince` | Flowcraft | text + TTS | `storyteller`, `little-prince`, `rose` mapped to three distinct public Voices |
| `eino-story-little-prince` | Eino | text only | none; GizClaw v0.7.7 cannot dynamically select a Voice for one fixed primary output |

Flowcraft selects exactly one published node per external response. Chapter entry/transition and invalid speaker selection fall back to `storyteller`; direct in-scene requests may select `little-prince` or `rose`.

## Acceptance

- Paired Flowcraft and Eino relays each require 16 continuous target responses with a reload before response 9.
- Milestones: 8, 16; intermediate segments end in strict `CHECKPOINT PASS` and the final segment ends in strict `PASS`.
- `flowcraft.roles.giztest.yaml` creates isolated narrator/little-prince/rose Workspaces and requires text EOS, audio EOS, non-empty Opus, timing evidence, and direct, speaker-label-free role text.
- Final live evidence must come from the e2e deployment through `edge-bj-01.e2e.gizclaw.com:9821`; dev evidence is diagnostic only.

```sh
GIZCLAW=/absolute/path/to/gizclaw-v0.7.7 GIZCLAW_TEST_CLI=/absolute/path/to/gizclaw-v0.7.7 make test-unit-resources
GIZCLAW=/absolute/path/to/gizclaw-v0.7.7 GIZCLAW_TEST_CLI=/absolute/path/to/gizclaw-v0.7.7 GIZCLAW_CONTEXT=e2e-server-volc-bj-01 GIZCLAW_TEST_ENDPOINT=edge-bj-01.e2e.gizclaw.com:9821 GIZCLAW_TEST_REGISTRATION_TOKEN=<testing-runtime-token> APPLY=1 RAID=story-little-prince PARALLEL=3 make test-e2e
```
