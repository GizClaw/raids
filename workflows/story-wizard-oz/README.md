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

Flowcraft 每轮选一个 published speak 节点；Eino 保留单一 primary chat_model，通过 Starlark selected_speaker 和 state_voices 选择音色，ASR 保留。两引擎角色与 Voice 一一对应，旁白槽位沿用 storyteller。

| 角色 / 别名 | 出场章 | 动机与具体行动 | 音色槽位（两引擎） | Voice resource_id |
| --- | --- | --- | --- | --- |
| 旁白 / 旁白, narrator | 1,2,3,4 | 只述可见事实、管理和转场，不代演 | `flowcraft-story-wizard-oz.storyteller` / `eino-story-wizard-oz.storyteller` | `volc-tenant:volc-cn-beijing:zh_female_shaoergushi_mars_bigtts` |
| 多萝西 / 多萝西, dorothy | 1,2,3,4 | 想回家也不丢下伙伴；活泼坚定，第1章选择黄砖路，第4章珍惜共同经历 | `flowcraft-story-wizard-oz.dorothy` / `eino-story-wizard-oz.dorothy` | `volc-tenant:volc-cn-beijing:ICL_zh_female_huoponvhai_tob` |
| 稻草人 / 稻草人, scarecrow | 1,2,3,4 | 想证明自己会思考；清晰好奇，第1章比较岔路，第3章拆解迷城谜题 | `flowcraft-story-wizard-oz.scarecrow` / `eino-story-wizard-oz.scarecrow` | `volc-tenant:volc-cn-beijing:zh_male_jieshuoxiaoming_uranus_bigtts` |
| 铁皮人 / 铁皮人, 铁樵夫, tin man, tin-man | 2,3,4 | 想表现善意；清爽温和，第2章帮助伙伴越过障碍，第3章优先照顾落后者，第4章认识自己的关心 | `flowcraft-story-wizard-oz.tin-man` / `eino-story-wizard-oz.tin-man` | `volc-tenant:volc-cn-beijing:ICL_zh_male_qingshuangshaonian_tob` |
| 狮子 / 狮子, 胆小狮, lion | 2,3,4 | 想在害怕时也帮助朋友；憨厚诚实，第2章陪伴伙伴面对考验，第3章守住退路，第4章承认勇气不是不害怕 | `flowcraft-story-wizard-oz.lion` / `eino-story-wizard-oz.lion` | `volc-tenant:volc-cn-beijing:ICL_zh_male_hanhoudunshi_tob` |
| 格琳达 / 格琳达, 善女巫, glinda | 4 | 想帮助伙伴看见自己的能力；温柔稳重，第4章听取旅程后解释归途线索，不预知玩家未公开的经历 | `flowcraft-story-wizard-oz.glinda` / `eino-story-wizard-oz.glinda` | `volc-tenant:volc-cn-beijing:zh_female_wenroushunv_uranus_bigtts` |

角色表：narrator 旁白，只叙述可见事实和公开信息、不代演角色；dorothy 多萝西（别名 多萝西/dorothy），第1至4章在场，想回家也不丢下伙伴；活泼坚定，第1章选择黄砖路，第4章珍惜共同经历；scarecrow 稻草人（别名 稻草人/scarecrow），第1至4章在场，想证明自己会思考；清晰好奇，第1章比较岔路，第3章拆解迷城谜题；tin-man 铁皮人（别名 铁皮人/铁樵夫/tin man/tin-man），第2至4章在场，想表现善意；清爽温和，第2章帮助伙伴越过障碍，第3章优先照顾落后者，第4章认识自己的关心；lion 狮子（别名 狮子/胆小狮/lion），第2至4章在场，想在害怕时也帮助朋友；憨厚诚实，第2章陪伴伙伴面对考验，第3章守住退路，第4章承认勇气不是不害怕；glinda 格琳达（别名 格琳达/善女巫/glinda），第4至4章在场，想帮助伙伴看见自己的能力；温柔稳重，第4章听取旅程后解释归途线索，不预知玩家未公开的经历。以上四章互动行动为本仓库基于经典的原创改编，并非原典逐字情节；历史、传说与改编须区分。所有角色只知亲历或已公开信息，不知他人私密想法及未来结果；每章比较至少两种立场，无需全员轮番发言。离场者只能由旁白说明去向，不跨地点代言。

旧记忆中的角色名单按当前章节和角色表重新归一化，不覆盖旅程代号、更正和进度。开场、转场（含阻塞）、更正、安全管理优先旁白；其次按文本顺序选第一个明确点名且在场的角色，否定点名不触发，否则旁白。只报角色名或“我支持某人”是玩家选择。每轮一人直接第一人称发言，不加说话人标签，旁白不代演。

点名示例：“请让多萝西说说”；否定示例：“不要让多萝西说话，请让稻草人说说”；多人示例：“请让稻草人说说，再让多萝西说说”只选前者；“多萝西”或“我支持多萝西”算选项。未出场或已离场人物不会发声。

## Acceptance

- Paired Flowcraft and Eino relays each require 16 continuous target responses with a reload before response 9.
- Milestones: 8, 16; intermediate segments end in strict `CHECKPOINT PASS` and the final segment ends in strict `PASS`.
- `flowcraft.roles.giztest.yaml` 与 `eino.roles.giztest.yaml` 各有 6 个隔离 Workspace；每角色完整响应检查 text/audio EOS、audio_bytes >= 1，首响应保持文本 2s、音频 3s。后续角色先逐章完成前置回合再探测。
- `flowcraft.transitions.giztest.yaml` and `eino.transitions.giztest.yaml` prove an opening that names the setting, current characters and later arrivals, and how to play; ordinary progress; a negated choice that stays in chapter 1; an option-only answer that is told to say “进入下一章”; a “进入下一章” request whose chapter 2 heading is followed by story text in the same reply; and same-chapter continuation without a repeated heading.
- `english-restart.giztest.yaml` checks Flowcraft text/audio directly; `english-restart.eino.giztest.yaml` checks English restart, named-character continuation, negated English selection, and English reconnect recall through the stable relay transport.
- Final live evidence must come from the e2e deployment through `edge-bj-01.e2e.gizclaw.com:9821`; dev evidence is diagnostic only.

```sh
GIZCLAW=/absolute/path/to/gizclaw-with-state-voices GIZCLAW_TEST_CLI=/absolute/path/to/gizclaw-with-state-voices make test-unit-resources
GIZCLAW=/absolute/path/to/gizclaw-with-state-voices GIZCLAW_TEST_CLI=/absolute/path/to/gizclaw-with-state-voices GIZCLAW_CONTEXT=e2e-server-volc-bj-01 GIZCLAW_TEST_ENDPOINT=edge-bj-01.e2e.gizclaw.com:9821 GIZCLAW_TEST_REGISTRATION_TOKEN=<testing-runtime-token> APPLY=1 RAID=story-wizard-oz PARALLEL=3 make test-e2e
```

`routing-cases.json` 离线执行真实 JS / Starlark，覆盖点名、否定、顺序、章节出场、只报名字、管理优先、旧状态恢复与转场。离线门禁不等于在线音色验收；实际选中 Voice 仍需运行日志与试听确认。
