# Aesop's Fables (`story-aesop`) — 伊索寓言

Discover consequences and lessons through short interactive animal fables.

## Story contract

- Premise: 通过简短动物寓言发现选择带来的结果与启发。
- Player: an active companion whose current choice and explicit correction override older History or Memory.
- Chapters: 第1章《种子的选择》 → 第2章《等待与分歧》 → 第3章《合作照料》 → 第4章《双重启发》.
- Cast: narrator (visible facts and transitions), 乌龟 (`tortoise`), and 小鸟 (`bird`); each character keeps a distinct motive, voice, and knowledge boundary.
- State: current chapter, completed beats, location, active roles, player choices, explicit corrections, durable clues, and unresolved hooks survive the bounded reload.
- Safety and source boundary: distinguish fact, legend, and original fiction; keep peril child-safe and do not reproduce a published translation.
- Repetition boundary: do not repeat acknowledgements, openings, choices, questions, recaps, or moral summaries.

| Chapter | Entry condition | Goal | Allowed beats (at least two) | Transition condition | Ending condition |
| --- | --- | --- | --- | --- | --- |
| 1. 种子的选择 | first opening request | resolve this chapter's core tension | observe a concrete consequence; compare the two characters' responses | player resolves the current hook and requests chapter 2 | emit the chapter 2 heading once |
| 2. 等待与分歧 | chapter 1 transition satisfied and player explicitly continues | resolve this chapter's core tension | observe a concrete consequence; compare the two characters' responses | player resolves the current hook and requests chapter 3 | emit the chapter 3 heading once |
| 3. 合作照料 | chapter 2 transition satisfied and player explicitly continues | resolve this chapter's core tension | observe a concrete consequence; compare the two characters' responses | player resolves the current hook and requests chapter 4 | emit the chapter 4 heading once |
| 4. 双重启发 | chapter 3 transition satisfied and player explicitly continues | resolve this chapter's core tension | observe a concrete consequence; compare the two characters' responses | player confirms a durable choice and one remaining responsibility | remain in chapter 4; keep one post-ending responsibility |

## Implementations and Voice roles

| Workflow | Engine | Output | Voice roles |
| --- | --- | --- | --- |
| `flowcraft-story-aesop` | Flowcraft | text + TTS | `storyteller`, `tortoise`, `bird` mapped to three distinct public Voices |
| `eino-story-aesop` | Eino | text only | none; GizClaw v0.7.7 cannot dynamically select a Voice for one fixed primary output |

Flowcraft selects exactly one published node per external response. Chapter entry/transition and invalid speaker selection fall back to `storyteller`; direct in-scene requests may select `tortoise` or `bird`.

## Acceptance

- Paired Flowcraft and Eino relays each require 16 continuous target responses with a reload before response 9.
- Milestones: 8, 16; intermediate segments end in strict `CHECKPOINT PASS` and the final segment ends in strict `PASS`.
- `flowcraft.roles.giztest.yaml` creates isolated narrator/tortoise/bird Workspaces and requires text EOS, audio EOS, non-empty Opus, timing evidence, and direct, speaker-label-free role text.
- `flowcraft.transitions.giztest.yaml` proves ordinary progress, a negated choice that stays in chapter 1, an option-only answer that later enters chapter 2 without a magic completion phrase, and same-chapter continuation without a false transition block.
- Final live evidence must come from the e2e deployment through `edge-bj-01.e2e.gizclaw.com:9821`; dev evidence is diagnostic only.

```sh
GIZCLAW=/absolute/path/to/gizclaw-v0.7.7 GIZCLAW_TEST_CLI=/absolute/path/to/gizclaw-v0.7.7 make test-unit-resources
GIZCLAW=/absolute/path/to/gizclaw-v0.7.7 GIZCLAW_TEST_CLI=/absolute/path/to/gizclaw-v0.7.7 GIZCLAW_CONTEXT=e2e-server-volc-bj-01 GIZCLAW_TEST_ENDPOINT=edge-bj-01.e2e.gizclaw.com:9821 GIZCLAW_TEST_REGISTRATION_TOKEN=<testing-runtime-token> APPLY=1 RAID=story-aesop PARALLEL=3 make test-e2e
```
