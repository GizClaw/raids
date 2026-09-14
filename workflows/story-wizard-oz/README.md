# The Wizard of Oz (`story-wizard-oz`) — 绿野仙踪

Discover courage, wisdom, kindness, and friendship on a journey through Oz.

## Story contract

- Premise: 在奥兹旅途中发现勇气、智慧、善意与伙伴关系。
- Player: an active companion whose current choice and explicit correction override older History or Memory.
- Chapters: 第1章《黄砖岔路》 → 第2章《勇气考验》 → 第3章《智慧迷城》 → 第4章《伙伴归途》.
- Cast: 旁白 (`narrator`), 多萝西 (`dorothy`), 稻草人 (`scarecrow`), 铁皮人 (`tin-man`), 狮子 (`lion`), 格琳达 (`glinda`).
- State: current chapter, completed beats, location, active roles, player choices, explicit corrections, durable clues, and unresolved hooks survive the bounded reload.
- Safety and source boundary: distinguish fact, legend, and original fiction; keep peril child-safe and do not reproduce a published translation.
- Repetition boundary: do not repeat acknowledgements, openings, choices, questions, recaps, or moral summaries.
- Language restart: both implementations preserve the explicit English restart path with `Chapter 1: The Yellow Brick Fork` and the established three-way yellow-brick-road opening.

| Chapter | Entry condition | Goal | Allowed beats (at least two) | Transition condition | Ending condition |
| --- | --- | --- | --- | --- | --- |
| 1. 黄砖岔路 | first opening request | resolve this chapter's core tension | observe a concrete consequence; compare at least two characters' responses | player resolves the current hook and requests chapter 2 | emit the chapter 2 heading once, followed directly by that chapter's opening scene |
| 2. 勇气考验 | chapter 1 transition satisfied and player explicitly continues | resolve this chapter's core tension | observe a concrete consequence; compare at least two characters' responses | player resolves the current hook and requests chapter 3 | emit the chapter 3 heading once, followed directly by that chapter's opening scene |
| 3. 智慧迷城 | chapter 2 transition satisfied and player explicitly continues | resolve this chapter's core tension | observe a concrete consequence; compare at least two characters' responses | player resolves the current hook and requests chapter 4 | emit the chapter 4 heading once, followed directly by that chapter's opening scene |
| 4. 伙伴归途 | chapter 3 transition satisfied and player explicitly continues | resolve this chapter's core tension | observe a concrete consequence; compare at least two characters' responses | player confirms a durable choice and one remaining responsibility | remain in chapter 4; keep one post-ending responsibility |

## Implementations and Voice roles

两引擎每轮使用一个讲述 LLM，按 `speaker_voices` 连续切换段落音色，保留 ASR 和既有音色绑定。

Voice 由 runtime profile 绑定。

| 角色 / 别名 | 出场章 | 动机与具体行动 | 音色槽位（两引擎） | Voice aliases |
| --- | --- | --- | --- | --- |
| 旁白 / 旁白, narrator | 1,2,3,4 | 只述可见事实、管理和转场，不代演 | `flowcraft-story-wizard-oz.storyteller` / `eino-story-wizard-oz.storyteller` | `flowcraft-story-wizard-oz.storyteller` / `eino-story-wizard-oz.storyteller` |
| 多萝西 / 多萝西, dorothy | 1,2,3,4 | 想回家也不丢下伙伴；活泼坚定，第1章选择黄砖路，第4章珍惜共同经历 | `flowcraft-story-wizard-oz.dorothy` / `eino-story-wizard-oz.dorothy` | `flowcraft-story-wizard-oz.dorothy` / `eino-story-wizard-oz.dorothy` |
| 稻草人 / 稻草人, scarecrow | 1,2,3,4 | 想证明自己会思考；清晰好奇，第1章比较岔路，第3章拆解迷城谜题 | `flowcraft-story-wizard-oz.scarecrow` / `eino-story-wizard-oz.scarecrow` | `flowcraft-story-wizard-oz.scarecrow` / `eino-story-wizard-oz.scarecrow` |
| 铁皮人 / 铁皮人, 铁樵夫, tin man, tin-man | 2,3,4 | 想表现善意；清爽温和，第2章帮助伙伴越过障碍，第3章优先照顾落后者，第4章认识自己的关心 | `flowcraft-story-wizard-oz.tin-man` / `eino-story-wizard-oz.tin-man` | `flowcraft-story-wizard-oz.tin` / `eino-story-wizard-oz.tin` |
| 狮子 / 狮子, 胆小狮, lion | 2,3,4 | 想在害怕时也帮助朋友；憨厚诚实，第2章陪伴伙伴面对考验，第3章守住退路，第4章承认勇气不是不害怕 | `flowcraft-story-wizard-oz.lion` / `eino-story-wizard-oz.lion` | `flowcraft-story-wizard-oz.lion` / `eino-story-wizard-oz.lion` |
| 格琳达 / 格琳达, 善女巫, glinda | 4 | 想帮助伙伴看见自己的能力；温柔稳重，第4章听取旅程后解释归途线索，不预知玩家未公开的经历 | `flowcraft-story-wizard-oz.glinda` / `eino-story-wizard-oz.glinda` | `flowcraft-story-wizard-oz.glinda` / `eino-story-wizard-oz.glinda` |

角色表：narrator 旁白，只叙述可见事实和公开信息、不代演角色；dorothy 多萝西（别名 多萝西/dorothy），第1至4章在场，想回家也不丢下伙伴；活泼坚定，第1章选择黄砖路，第4章珍惜共同经历；scarecrow 稻草人（别名 稻草人/scarecrow），第1至4章在场，想证明自己会思考；清晰好奇，第1章比较岔路，第3章拆解迷城谜题；tin-man 铁皮人（别名 铁皮人/铁樵夫/tin man/tin-man），第2至4章在场，想表现善意；清爽温和，第2章帮助伙伴越过障碍，第3章优先照顾落后者，第4章认识自己的关心；lion 狮子（别名 狮子/胆小狮/lion），第2至4章在场，想在害怕时也帮助朋友；憨厚诚实，第2章陪伴伙伴面对考验，第3章守住退路，第4章承认勇气不是不害怕；glinda 格琳达（别名 格琳达/善女巫/glinda），第4至4章在场，想帮助伙伴看见自己的能力；温柔稳重，第4章听取旅程后解释归途线索，不预知玩家未公开的经历。以上四章互动行动为本仓库基于经典的原创改编，并非原典逐字情节；历史、传说与改编须区分。所有角色只知亲历或已公开信息，不知他人私密想法及未来结果；每章比较至少两种立场，无需全员轮番发言。离场者只能由旁白说明去向，不跨地点代言。


点名示例：“请让多萝西说说”；否定示例：“不要让多萝西说话，请让稻草人说说”；多人示例：“请让稻草人说说，再让多萝西说说”只选前者；“多萝西”或“我支持多萝西”算选项。未出场或已离场人物不会发声。

## Acceptance

- Paired Flowcraft and Eino relays each require 16 continuous target responses with a reload before response 9.
- Milestones: 8, 16; intermediate segments end in strict `CHECKPOINT PASS` and the final segment ends in strict `PASS`.
- `flowcraft.transitions.giztest.yaml` and `eino.transitions.giztest.yaml` prove an opening that names the setting, current characters and later arrivals, and how to play; ordinary progress; a negated choice that stays in chapter 1; an option-only answer that is told to say “进入下一章”; a “进入下一章” request whose chapter 2 heading is followed by story text in the same reply; and same-chapter continuation without a repeated heading.
- `english-restart.giztest.yaml` checks Flowcraft text/audio directly; `english-restart.eino.giztest.yaml` checks English restart, named-character continuation, negated English selection, and English reconnect recall through the stable relay transport.
- Final live evidence must come from the e2e deployment through `edge-bj-01.e2e.gizclaw.com:9821`; dev evidence is diagnostic only.

```sh
GIZCLAW=/absolute/path/to/gizclaw-with-state-voices GIZCLAW_TEST_CLI=/absolute/path/to/gizclaw-with-state-voices make test-unit-resources
GIZCLAW=/absolute/path/to/gizclaw-with-state-voices GIZCLAW_TEST_CLI=/absolute/path/to/gizclaw-with-state-voices GIZCLAW_CONTEXT=e2e-server-volc-bj-01 GIZCLAW_TEST_ENDPOINT=edge-bj-01.e2e.gizclaw.com:9821 GIZCLAW_TEST_REGISTRATION_TOKEN=<testing-runtime-token> APPLY=1 RAID=story-wizard-oz PARALLEL=3 make test-e2e
```

`routing-cases.json` 离线执行真实 JS / Starlark，覆盖点名、否定、顺序、章节出场、只报名字、管理优先、旧状态恢复与转场。离线门禁不等于在线音色验收；实际选中 Voice 仍需运行日志与试听确认。

## 连续多角色讲述契约

普通回合（含开场、转场、选择结果）约 300–600 字、1–2 分钟语音，旁白与 2–4 个当前在场角色交替讲述；当前场景只有一位角色时不为凑数增员。每段恰好以一个配置中的 `【旁白】` 或 `【角色中文名】` 开头，标记后直接正文，禁止其他全角方括号标记。AudioDock 剥离标记并串行播放、预取下一段；孩子随时插话后承接新输入。

结尾由旁白给 2–3 个具体选项；选择完成逐字结尾、第四章/终局、安全、仅确认/更正/回忆等已有约束优先，不额外加问题；限定范围和安全回复可短于 300 字。章节、场景、知情边界与旧记忆恢复保持上文契约。音色槽位和 RuntimeProfile 绑定不变，中文标记名与上表角色对应。

Smoke 用连续开场、续讲及 realtime 检查完整 EOS、单流不叠音、零欠载、无残留标记和正文长度，first_response 保持 2s/3s。Quality 保留章节守门、选择结尾、安全逐字用语及原有更正/恢复场景；不再逐角色点名。Soak 保留 16 响应、relay 和 reload 结构，普通段落检查 300–600 字（特殊回复例外）。`routing-cases.json` 执行两引擎控制源码，验证状态与内容约束；已删除无意义的单人选声断言。离线通过不代表真实音色与音频时序已验收，需 GizClaw v0.18.12 部署后 E2E 和试听。
