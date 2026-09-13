# Aesop's Fables (`story-aesop`) — 伊索寓言

Discover consequences and lessons through short interactive animal fables.

## Story contract

- Premise: 通过简短动物寓言发现选择带来的结果与启发。
- Player: an active companion whose current choice and explicit correction override older History or Memory.
- Chapters: 第1章《种子的选择》 → 第2章《等待与分歧》 → 第3章《合作照料》 → 第4章《双重启发》.
- Cast: narrator (visible facts and transitions), 乌龟 (`tortoise`), 小鸟 (`bird`), 兔子 (`rabbit`), 狐狸 (`fox`). The seed-care plot is an original adaptation; characters only know witnessed or publicly revealed information.
- State: current chapter, completed beats, location, active roles, player choices, explicit corrections, durable clues, and unresolved hooks survive the bounded reload.
- Safety and source boundary: distinguish fact, legend, and original fiction; keep peril child-safe and do not reproduce a published translation.
- Repetition boundary: do not repeat acknowledgements, openings, choices, questions, recaps, or moral summaries.

| Chapter | Entry condition | Goal | Allowed beats (at least two) | Transition condition | Ending condition |
| --- | --- | --- | --- | --- | --- |
| 1. 种子的选择 | first opening request | resolve this chapter's core tension | observe a concrete consequence; compare the two characters' responses | player resolves the current hook and requests chapter 2 | emit the chapter 2 heading once, followed directly by that chapter's opening scene |
| 2. 等待与分歧 | chapter 1 transition satisfied and player explicitly continues | resolve this chapter's core tension | observe a concrete consequence; compare the two characters' responses | player resolves the current hook and requests chapter 3 | emit the chapter 3 heading once, followed directly by that chapter's opening scene |
| 3. 合作照料 | chapter 2 transition satisfied and player explicitly continues | resolve this chapter's core tension | observe a concrete consequence; compare the two characters' responses | player resolves the current hook and requests chapter 4 | emit the chapter 4 heading once, followed directly by that chapter's opening scene |
| 4. 双重启发 | chapter 3 transition satisfied and player explicitly continues | resolve this chapter's core tension | observe a concrete consequence; compare the two characters' responses | player confirms a durable choice and one remaining responsibility | remain in chapter 4; keep one post-ending responsibility |

## Implementations and Voice roles

| Workflow | Engine | Output | Voice roles |
| --- | --- | --- | --- |
| `flowcraft-story-aesop` | Flowcraft | text + TTS | `storyteller`, `tortoise`, `bird`, `rabbit`, `fox` mapped to five distinct Voice resources |
| `eino-story-aesop` | Eino | text + TTS | the same five roles, selected through `state_voices` on one primary output |

Flowcraft selects exactly one published node per external response. Eino runs `select-speaker` before the prompt and its single primary `narrator-model`; the selected identity and Voice share `selected_speaker`. Opening, transitions (including blocked transitions), corrections and safety management select narrator first. Otherwise select the first explicitly requested available character in text order; negated requests do not select a character. Unmatched requests use narrator. An option-only name such as “小鸟” remains a player choice, narrated by narrator.

## Cast and bindings

Both `runtime-profiles/default.yaml` and `testing.yaml` bind these exact IDs under `spec.resources.voices`. Flowcraft `node_voices` maps `speak-narrator` to `.storyteller` and each character node to its own role slot. Eino maps state values to `eino-story-aesop.*` aliases and defaults to `.storyteller`.

| Role / aliases | Chapters | Action / perspective | Slot suffix | Full Voice resource ID |
| --- | --- | --- | --- | --- |
| narrator / 旁白 | 1–4 | visible consequences and management; never impersonates characters | storyteller | volc-tenant:volc-cn-beijing:zh_female_shaoergushi_mars_bigtts |
| tortoise / 乌龟 / 小乌龟 | 1–4 | patient planting and care | tortoise | volc-tenant:volc-cn-beijing:ICL_zh_male_hanhoudunshi_tob |
| bird / 小鸟 / 鸟儿 | 1–4 | immediate hunger and observations from branches | bird | volc-tenant:volc-cn-beijing:ICL_zh_female_huoponvhai_tob |
| rabbit / 兔子 / 小兔 | 1–4 | carries the seed in chapter 1 and water in chapter 3; eager, childlike | rabbit | volc-tenant:volc-cn-beijing:zh_male_naiqimengwa_mars_bigtts |
| fox / 狐狸 / 小狐狸 | 2–4 | compares waiting with finding food in chapter 2; proposes shared care in chapter 3 | fox | volc-tenant:volc-cn-beijing:ICL_zh_male_qingshuangshaonian_tob |

Examples: “请让兔子说说”; after chapter 2 starts, “请让狐狸亲自回应”. “请让小鸟说说，再让乌龟说说” selects only bird. “不要让兔子说话，请让小鸟说说” selects bird. Before chapter 2 a fox request falls back to narrator.

`control-story` rebuilds `active_roles` from `roleTable` after old memory recovery and every chapter change, preserving choices, corrections and journey code. Old three-role arrays cannot overwrite the new cast. Each chapter compares at least two perspectives; it does not require every character to speak. Eino keeps the existing recall/observe/History contract. Its selector derives eligibility from delivered assistant chapter headings or recognized recalled structured state, ignoring legacy cast arrays and user requests to skip ahead. Unrecognized recalled chapter formats conservatively fall back to chapter 1.

Voice age/temperament descriptions are casting intentions based on catalog names, not listening results. Static checks do not establish tenant synthesis access or perceived voice quality. Existing Voice provider parameters remain unchanged.

## Acceptance

- Paired Flowcraft and Eino relays each require 16 continuous target responses with a reload before response 9.
- Milestones: 8, 16; intermediate segments end in strict `CHECKPOINT PASS` and the final segment ends in strict `PASS`.
- Role manifest count: **5** (including narrator); each has one full response probe and one first-response probe. The fox Workspace completes chapter 1 before probing chapter 2. Offline controller regression covers negation, text-order selection, option-only choices, management priority and legacy memory normalization.
- `flowcraft.roles.giztest.yaml` and `eino.roles.giztest.yaml` each create five isolated narrator/tortoise/bird/rabbit/fox Workspaces and requires text EOS, audio EOS, non-empty Opus, timing evidence, and direct, speaker-label-free role text.
- `flowcraft.transitions.giztest.yaml` and `eino.transitions.giztest.yaml` prove an opening that names the setting, the opening cast and the fox’s later arrival, and how to play; ordinary progress; a negated choice that stays in chapter 1; an option-only answer that is told to say “进入下一章”; a “进入下一章” request whose chapter 2 heading is followed by story text in the same reply; and same-chapter continuation without a repeated heading.
- Final live evidence must come from the e2e deployment through `edge-bj-01.e2e.gizclaw.com:9821`; dev evidence is diagnostic only.

Offline routing checks execute the YAML Starlark source using Go and locally cached dependencies (`GOPROXY=off`, `GOSUMDB=off`); set `GO` for an alternative local toolchain. Both CLI and Server must support Eino `state_voices`.

```sh
GIZCLAW=/absolute/path/to/gizclaw-with-state-voices GIZCLAW_TEST_CLI=/absolute/path/to/gizclaw-with-state-voices make test-unit-resources
GIZCLAW=/absolute/path/to/gizclaw-with-state-voices GIZCLAW_TEST_CLI=/absolute/path/to/gizclaw-with-state-voices GIZCLAW_CONTEXT=e2e-server-volc-bj-01 GIZCLAW_TEST_ENDPOINT=edge-bj-01.e2e.gizclaw.com:9821 GIZCLAW_TEST_REGISTRATION_TOKEN=<testing-runtime-token> APPLY=1 RAID=story-aesop PARALLEL=3 make test-e2e
```
