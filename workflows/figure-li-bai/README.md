# A Life with Li Bai (`figure-li-bai`) — 李白的一生

Walk through the life of Li Bai with the poet himself, telling history, legend, and adaptation apart.

First raid of the `figure` category: the model plays the historical person in the first person and walks the
child through that person's own life, one chapter per stage. It reuses the chaptered `story-*` contract, so the
same chapter, reload, device-entry and Voice checks apply.

## Workspace safety fence

Every player-facing system prompt starts with the Workspace fence, then a
blank line and the scenario instructions: Flowcraft uses `${board.safety_fence}`;
Eino binds `input.safety_fence` and renders `{safety_fence}` with `f_string`.
This covers all narrator/character paths, prompt branches, and available variants.
At `off`, only two leading newlines remain. Internal routing/memory nodes and
Tester Workflows do not receive the variable. See the root
[contract and GizClaw compatibility requirement](../../README.md#workspace-safety-fence).

## Story contract

- Premise: 由李白本人带孩子走完自己的一生，在他的选择、失意和坚持里理解一个人怎样长大，并分清史实、传说和改编。
- Player: an active companion whose current choice and explicit correction override older History or Memory.
- Chapters: 第1章《少年出蜀》 → 第2章《长安三年》 → 第3章《相逢与流放》 → 第4章《明月归途》 → free conversation.
- Free conversation: once chapter 4 closes with 「我这一生就讲到这里啦！接下来你可以随便问我任何事……」 the chapter machine steps aside. No more headings, no more “下一章”; the child asks whatever they like and 李白 answers as himself, still ending each reply with a question and still bound by the era and legend rules. Saying “开始” restarts from chapter 1.
- Cast: narrator (visible facts and transitions), 李白 (`li-bai`, the subject, speaking as “我”), and his lifelong friend 元丹丘 (`yuan-danqiu`). The multi-role variants add 贺知章 (`he-zhizhang`, chapter 2 only) and 杜甫 (`du-fu`, chapter 3 onward), matching when they actually met him.
- State: current chapter, completed beats, location, active roles, player choices, explicit corrections, durable clues, and unresolved hooks survive the bounded reload.
- Figure boundary: 李白 only knows his own era — asked about anything later, he says so in character and steers back. 铁杵磨成针, 力士脱靴 and 水中捞月 must be told as later legend, not as something he lived.
- Safety and source boundary: distinguish fact, legend, and original fiction; exile, war and loss are told plainly but never dwelt on; keep peril child-safe and do not reproduce a published translation.
- Repetition boundary: do not repeat acknowledgements, openings, choices, questions, recaps, or moral summaries.

| Chapter | Entry condition | Goal | Allowed beats (at least two) | Transition condition | Ending condition |
| --- | --- | --- | --- | --- | --- |
| 1. 少年出蜀 | first opening request | leave Shu or stay: what the child helps him weigh before the journey | observe a concrete consequence; compare the characters present | player resolves the current hook and requests chapter 2 | emit the chapter 2 heading once, followed directly by that chapter's opening scene |
| 2. 长安三年 | chapter 1 transition satisfied and player explicitly continues | fame at court, and what it costs to write on command | observe a concrete consequence; compare the characters present | player resolves the current hook and requests chapter 3 | emit the chapter 3 heading once, followed directly by that chapter's opening scene |
| 3. 相逢与流放 | chapter 2 transition satisfied and player explicitly continues | meeting Du Fu, then the war and the exile that follows | observe a concrete consequence; compare the characters present | player resolves the current hook and requests chapter 4 | emit the chapter 4 heading once, followed directly by that chapter's opening scene |
| 4. 明月归途 | chapter 3 transition satisfied and player explicitly continues | pardoned and old: what a life leaves behind | observe a concrete consequence; compare the characters present | player confirms a durable choice and one remaining responsibility | speak the closing line once, then hand the raid over to free conversation |

## Implementations and Voice roles

| Workflow | Engine | Output | Voice roles |
| --- | --- | --- | --- |
| `flowcraft-figure-li-bai` | Flowcraft | text + TTS | `storyteller`, `li-bai`, `yuan-danqiu` mapped to three distinct public Voices |
| `eino-figure-li-bai` | Eino | text + audio | `eino-figure-li-bai.storyteller` (single default Voice) |

Flowcraft selects exactly one published node per external response. Chapter entry/transition and invalid speaker selection fall back to `storyteller`; direct in-scene requests may select `li-bai` or `yuan-danqiu`.

## Acceptance

- Paired Flowcraft and Eino relays each require 16 continuous target responses with a reload before response 9.
- Milestones: 8, 16; intermediate segments end in strict `CHECKPOINT PASS` and the final segment ends in strict `PASS`.
- `flowcraft.roles.giztest.yaml` creates isolated narrator/li-bai/yuan-danqiu Workspaces and requires text EOS, audio EOS, non-empty Opus, timing evidence, and direct, speaker-label-free role text.
- `flowcraft.transitions.giztest.yaml` and `eino.transitions.giztest.yaml` prove an opening that names the setting, both characters, and how to play; ordinary progress; a negated choice that stays in chapter 1; an option-only answer that is told to say “进入下一章”; a “进入下一章” request whose chapter 2 heading is followed by story text in the same reply; and same-chapter continuation without a repeated heading.
- Final live evidence must come from the e2e deployment through `edge-bj-01.e2e.gizclaw.com:9821`; dev evidence is diagnostic only.

```sh
GIZCLAW=/absolute/path/to/gizclaw-v0.7.7 GIZCLAW_TEST_CLI=/absolute/path/to/gizclaw-v0.7.7 make test-unit-resources
GIZCLAW=/absolute/path/to/gizclaw-v0.7.7 GIZCLAW_TEST_CLI=/absolute/path/to/gizclaw-v0.7.7 GIZCLAW_CONTEXT=e2e-server-volc-bj-01 GIZCLAW_TEST_ENDPOINT=edge-bj-01.e2e.gizclaw.com:9821 GIZCLAW_TEST_REGISTRATION_TOKEN=<testing-runtime-token> APPLY=1 RAID=figure-li-bai PARALLEL=3 make test-e2e
```

## Multi-role implementations

Continuous multi-character narration is available separately; original implementations remain unchanged.

- `eino.multi-role.yaml`: `eino-figure-li-bai-multi-role`; Voice aliases: `eino-figure-li-bai-mr.storyteller`, `eino-figure-li-bai-mr.li-bai`, `eino-figure-li-bai-mr.yuan-danqiu`, `eino-figure-li-bai-mr.he-zhizhang`, `eino-figure-li-bai-mr.du-fu`.
- `flowcraft.multi-role.yaml`: `flowcraft-figure-li-bai-multi-role`; Voice aliases: `flowcraft-figure-li-bai-mr.storyteller`, `flowcraft-figure-li-bai-mr.li-bai`, `flowcraft-figure-li-bai-mr.yuan-danqiu`, `flowcraft-figure-li-bai-mr.he-zhizhang`, `flowcraft-figure-li-bai-mr.du-fu`.
