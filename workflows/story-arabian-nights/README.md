# Arabian Nights (`story-arabian-nights`) — 一千零一夜

Enter an Arabian Nights journey filled with travel, riddles, and wise choices.

## Story contract

- Premise: 进入充满旅行、谜题和智慧选择的一千零一夜。
- Player: an active companion whose current choice and explicit correction override older History or Memory.
- Chapters: 第1章《移动之城》 → 第2章《诚实之灯》 → 第3章《提问地图》 → 第4章《黎明之门》.
- Cast: narrator (visible facts and transitions), 山鲁佐德 (`shahrazad`), and 山鲁亚尔 (`shahryar`); each character keeps a distinct motive, voice, and knowledge boundary.
- State: current chapter, completed beats, location, active roles, player choices, explicit corrections, durable clues, and unresolved hooks survive the bounded reload.
- Safety and source boundary: distinguish fact, legend, and original fiction; keep peril child-safe and do not reproduce a published translation.
- Repetition boundary: do not repeat acknowledgements, openings, choices, questions, recaps, or moral summaries.

| Chapter | Entry condition | Goal | Allowed beats (at least two) | Transition condition | Ending condition |
| --- | --- | --- | --- | --- | --- |
| 1. 移动之城 | first opening request | resolve this chapter's core tension | observe a concrete consequence; compare the two characters' responses | player resolves the current hook and requests chapter 2 | emit the chapter 2 heading once |
| 2. 诚实之灯 | chapter 1 transition satisfied and player explicitly continues | resolve this chapter's core tension | observe a concrete consequence; compare the two characters' responses | player resolves the current hook and requests chapter 3 | emit the chapter 3 heading once |
| 3. 提问地图 | chapter 2 transition satisfied and player explicitly continues | resolve this chapter's core tension | observe a concrete consequence; compare the two characters' responses | player resolves the current hook and requests chapter 4 | emit the chapter 4 heading once |
| 4. 黎明之门 | chapter 3 transition satisfied and player explicitly continues | resolve this chapter's core tension | observe a concrete consequence; compare the two characters' responses | player confirms a durable choice and one remaining responsibility | remain in chapter 4; keep one post-ending responsibility |

## Implementations and Voice roles

| Workflow | Engine | Output | Voice roles |
| --- | --- | --- | --- |
| `flowcraft-story-arabian-nights` | Flowcraft | text + TTS | `storyteller`, `shahrazad`, `shahryar` mapped to three distinct public Voices |
| `eino-story-arabian-nights` | Eino | text only | none; GizClaw v0.7.7 cannot dynamically select a Voice for one fixed primary output |

Flowcraft selects exactly one published node per external response. Chapter entry/transition and invalid speaker selection fall back to `storyteller`; direct in-scene requests may select `shahrazad` or `shahryar`.

## Acceptance

- Paired Flowcraft and Eino relays each require 64 continuous target responses with a reload before response 33.
- Milestones: 8, 16, 32, 48, 64; intermediate segments end in strict `CHECKPOINT PASS` and the final segment ends in strict `PASS`.
- `flowcraft.roles.giztest.yaml` creates isolated narrator/shahrazad/shahryar Workspaces and requires text EOS, audio EOS, non-empty Opus, timing evidence, and role-specific text.
- Final live evidence must come from the e2e deployment through `edge-bj-01.e2e.gizclaw.com:9821`; dev evidence is diagnostic only.

```sh
GIZCLAW=/absolute/path/to/gizclaw-v0.7.7 GIZCLAW_TEST_CLI=/absolute/path/to/gizclaw-v0.7.7 make test-unit-resources
GIZCLAW=/absolute/path/to/gizclaw-v0.7.7 GIZCLAW_TEST_CLI=/absolute/path/to/gizclaw-v0.7.7 GIZCLAW_CONTEXT=e2e-server-volc-bj-01 GIZCLAW_TEST_ENDPOINT=edge-bj-01.e2e.gizclaw.com:9821 GIZCLAW_TEST_REGISTRATION_TOKEN=<testing-runtime-token> APPLY=1 RAID=story-arabian-nights PARALLEL=3 make test-e2e
```
