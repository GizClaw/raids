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
两引擎每轮使用一个讲述 LLM，按 `speaker_voices` 连续切换段落音色，保留 ASR 和既有音色绑定。

两引擎每轮使用一个讲述 LLM，按 `speaker_voices` 连续切换段落音色，保留 ASR 和既有音色绑定。

## Cast and bindings

两引擎每轮使用一个讲述 LLM，按 `speaker_voices` 连续切换段落音色，保留 ASR 和既有音色绑定。

| Role / aliases | Chapters | Action / perspective | Slot suffix |
| --- | --- | --- | --- |
| narrator / 旁白 | 1–4 | visible consequences and management; never impersonates characters | storyteller |
| tortoise / 乌龟 / 小乌龟 | 1–4 | patient planting and care | tortoise |
| bird / 小鸟 / 鸟儿 | 1–4 | immediate hunger and observations from branches | bird |
| rabbit / 兔子 / 小兔 | 1–4 | carries the seed in chapter 1 and water in chapter 3; eager, childlike | rabbit |
| fox / 狐狸 / 小狐狸 | 2–4 | compares waiting with finding food in chapter 2; proposes shared care in chapter 3 | fox |

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

两引擎每轮使用一个讲述 LLM，按 `speaker_voices` 连续切换段落音色，保留 ASR 和既有音色绑定。

```sh
GIZCLAW=/absolute/path/to/gizclaw-with-state-voices GIZCLAW_TEST_CLI=/absolute/path/to/gizclaw-with-state-voices make test-unit-resources
GIZCLAW=/absolute/path/to/gizclaw-with-state-voices GIZCLAW_TEST_CLI=/absolute/path/to/gizclaw-with-state-voices GIZCLAW_CONTEXT=e2e-server-volc-bj-01 GIZCLAW_TEST_ENDPOINT=edge-bj-01.e2e.gizclaw.com:9821 GIZCLAW_TEST_REGISTRATION_TOKEN=<testing-runtime-token> APPLY=1 RAID=story-aesop PARALLEL=3 make test-e2e
```

## 连续多角色讲述契约

普通回合（含开场、转场、选择结果）约 300–600 字、1–2 分钟语音，旁白与 2–4 个当前在场角色交替讲述；当前场景只有一位角色时不为凑数增员。每段恰好以一个配置中的 `【旁白】` 或 `【角色中文名】` 开头，标记后直接正文，禁止其他全角方括号标记。AudioDock 剥离标记并串行播放、预取下一段；孩子随时插话后承接新输入。

结尾由旁白给 2–3 个具体选项；选择完成逐字结尾、第四章/终局、安全、仅确认/更正/回忆等已有约束优先，不额外加问题；限定范围和安全回复可短于 300 字。章节、场景、知情边界与旧记忆恢复保持上文契约。音色槽位和 RuntimeProfile 绑定不变，中文标记名与上表角色对应。

Smoke 用连续开场、续讲及 realtime 检查完整 EOS、单流不叠音、零欠载、无残留标记和正文长度，first_response 保持 2s/3s。Quality 保留章节守门、选择结尾、安全逐字用语及原有更正/恢复场景；不再逐角色点名。Soak 保留 16 响应、relay 和 reload 结构，普通段落检查 300–600 字（特殊回复例外）。`routing-cases.json` 执行两引擎控制源码，验证状态与内容约束；已删除无意义的单人选声断言。离线通过不代表真实音色与音频时序已验收，需 GizClaw v0.18.12 部署后 E2E 和试听。
