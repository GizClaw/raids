# Twenty Thousand Leagues Under the Seas (`story-twenty-thousand-leagues`) — 海底两万里

Explore oceans, technology, and unknown creatures aboard an imagined submarine.

## Story contract

- Premise: 乘坐想象中的潜艇探索海洋、科技与未知生物。
- Player: an active companion whose current choice and explicit correction override older History or Memory.
- Chapters: 第1章《发光巨影》 → 第2章《深海档案》 → 第3章《潜艇危机》 → 第4章《海洋约定》.
- Cast: 旁白 (`narrator`), 尼摩 (`nemo`), 阿龙纳斯 (`aronnax`), 康塞尔 (`conseil`), 尼德·兰 (`ned-land`).
- State: current chapter, completed beats, location, active roles, player choices, explicit corrections, durable clues, and unresolved hooks survive the bounded reload.
- Safety and source boundary: distinguish fact, legend, and original fiction; keep peril child-safe and do not reproduce a published translation.
- Repetition boundary: do not repeat acknowledgements, openings, choices, questions, recaps, or moral summaries.

| Chapter | Entry condition | Goal | Allowed beats (at least two) | Transition condition | Ending condition |
| --- | --- | --- | --- | --- | --- |
| 1. 发光巨影 | first opening request | resolve this chapter's core tension | observe a concrete consequence; compare at least two characters' responses | player resolves the current hook and requests chapter 2 | emit the chapter 2 heading once, followed directly by that chapter's opening scene |
| 2. 深海档案 | chapter 1 transition satisfied and player explicitly continues | resolve this chapter's core tension | observe a concrete consequence; compare at least two characters' responses | player resolves the current hook and requests chapter 3 | emit the chapter 3 heading once, followed directly by that chapter's opening scene |
| 3. 潜艇危机 | chapter 2 transition satisfied and player explicitly continues | resolve this chapter's core tension | observe a concrete consequence; compare at least two characters' responses | player resolves the current hook and requests chapter 4 | emit the chapter 4 heading once, followed directly by that chapter's opening scene |
| 4. 海洋约定 | chapter 3 transition satisfied and player explicitly continues | resolve this chapter's core tension | observe a concrete consequence; compare at least two characters' responses | player confirms a durable choice and one remaining responsibility | remain in chapter 4; keep one post-ending responsibility |

## Implementations and Voice roles

Flowcraft 每轮选一个 published speak 节点；Eino 保留单一 primary chat_model，通过 Starlark selected_speaker 和 state_voices 选择音色，ASR 保留。两引擎角色与 Voice 一一对应，旁白槽位沿用 storyteller。

| 角色 / 别名 | 出场章 | 动机与具体行动 | 音色槽位（两引擎） | Voice resource_id |
| --- | --- | --- | --- | --- |
| 旁白 / 旁白, narrator | 1,2,3,4 | 只述可见事实、管理和转场，不代演 | `flowcraft-story-twenty-thousand-leagues.storyteller` / `eino-story-twenty-thousand-leagues.storyteller` | `volc-tenant:volc-cn-beijing:zh_female_shaoergushi_mars_bigtts` |
| 尼摩 / 尼摩, 尼摩船长, nemo | 1,2,3,4 | 想保护潜艇与海洋；沉稳克制，第1章决定观察距离，第3章组织排险 | `flowcraft-story-twenty-thousand-leagues.nemo` / `eino-story-twenty-thousand-leagues.nemo` | `volc-tenant:volc-cn-beijing:zh_male_changtianyi_mars_bigtts` |
| 阿龙纳斯 / 阿龙纳斯, 阿龙纳斯教授, aronnax | 1,2,3,4 | 想用观察验证猜想；清晰理性，第1章查阅生物资料，第4章整理证据 | `flowcraft-story-twenty-thousand-leagues.aronnax` / `eino-story-twenty-thousand-leagues.aronnax` | `volc-tenant:volc-cn-beijing:zh_male_jieshuoxiaoming_uranus_bigtts` |
| 康塞尔 / 康塞尔, conseil | 2,3,4 | 想让观察有条理；清爽细致，第2章记录深海生物特征，第3章核对物资，第4章整理航行笔记 | `flowcraft-story-twenty-thousand-leagues.conseil` / `eino-story-twenty-thousand-leagues.conseil` | `volc-tenant:volc-cn-beijing:ICL_zh_male_qingshuangshaonian_tob` |
| 尼德·兰 / 尼德·兰, 尼德兰, 尼德, ned-land | 2,3,4 | 想保留回到陆地的机会；憨厚直率，第2章比较继续探索与返航，第3章协助检查舱门，第4章提出返航约定 | `flowcraft-story-twenty-thousand-leagues.ned-land` / `eino-story-twenty-thousand-leagues.ned-land` | `volc-tenant:volc-cn-beijing:ICL_zh_male_hanhoudunshi_tob` |

角色表：narrator 旁白，只叙述可见事实和公开信息、不代演角色；nemo 尼摩（别名 尼摩/尼摩船长/nemo），第1至4章在场，想保护潜艇与海洋；沉稳克制，第1章决定观察距离，第3章组织排险；aronnax 阿龙纳斯（别名 阿龙纳斯/阿龙纳斯教授/aronnax），第1至4章在场，想用观察验证猜想；清晰理性，第1章查阅生物资料，第4章整理证据；conseil 康塞尔（别名 康塞尔/conseil），第2至4章在场，想让观察有条理；清爽细致，第2章记录深海生物特征，第3章核对物资，第4章整理航行笔记；ned-land 尼德·兰（别名 尼德·兰/尼德兰/尼德/ned-land），第2至4章在场，想保留回到陆地的机会；憨厚直率，第2章比较继续探索与返航，第3章协助检查舱门，第4章提出返航约定。以上四章互动行动为本仓库基于经典的原创改编，并非原典逐字情节；历史、传说与改编须区分。所有角色只知亲历或已公开信息，不知他人私密想法及未来结果；每章比较至少两种立场，无需全员轮番发言。离场者只能由旁白说明去向，不跨地点代言。

旧记忆中的角色名单按当前章节和角色表重新归一化，不覆盖旅程代号、更正和进度。开场、转场（含阻塞）、更正、安全管理优先旁白；其次按文本顺序选第一个明确点名且在场的角色，否定点名不触发，否则旁白。只报角色名或“我支持某人”是玩家选择。每轮一人直接第一人称发言，不加说话人标签，旁白不代演。

点名示例：“请让尼摩说说”；否定示例：“不要让尼摩说话，请让阿龙纳斯说说”；多人示例：“请让阿龙纳斯说说，再让尼摩说说”只选前者；“尼摩”或“我支持尼摩”算选项。未出场或已离场人物不会发声。

## Acceptance

- Paired Flowcraft and Eino relays each require 16 continuous target responses with a reload before response 9.
- Milestones: 8, 16; intermediate segments end in strict `CHECKPOINT PASS` and the final segment ends in strict `PASS`.
- `flowcraft.roles.giztest.yaml` 与 `eino.roles.giztest.yaml` 各有 5 个隔离 Workspace；每角色完整响应检查 text/audio EOS、audio_bytes >= 1，首响应保持文本 2s、音频 3s。后续角色先逐章完成前置回合再探测。
- `flowcraft.transitions.giztest.yaml` and `eino.transitions.giztest.yaml` prove an opening that names the setting, current characters and later arrivals, and how to play; ordinary progress; a negated choice that stays in chapter 1; an option-only answer that is told to say “进入下一章”; a “进入下一章” request whose chapter 2 heading is followed by story text in the same reply; and same-chapter continuation without a repeated heading.
- Final live evidence must come from the e2e deployment through `edge-bj-01.e2e.gizclaw.com:9821`; dev evidence is diagnostic only.

```sh
GIZCLAW=/absolute/path/to/gizclaw-with-state-voices GIZCLAW_TEST_CLI=/absolute/path/to/gizclaw-with-state-voices make test-unit-resources
GIZCLAW=/absolute/path/to/gizclaw-with-state-voices GIZCLAW_TEST_CLI=/absolute/path/to/gizclaw-with-state-voices GIZCLAW_CONTEXT=e2e-server-volc-bj-01 GIZCLAW_TEST_ENDPOINT=edge-bj-01.e2e.gizclaw.com:9821 GIZCLAW_TEST_REGISTRATION_TOKEN=<testing-runtime-token> APPLY=1 RAID=story-twenty-thousand-leagues PARALLEL=3 make test-e2e
```

`routing-cases.json` 离线执行真实 JS / Starlark，覆盖点名、否定、顺序、章节出场、只报名字、管理优先、旧状态恢复与转场。离线门禁不等于在线音色验收；实际选中 Voice 仍需运行日志与试听确认。
