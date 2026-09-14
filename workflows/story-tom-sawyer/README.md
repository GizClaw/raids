# The Adventures of Tom Sawyer (`story-tom-sawyer`) — 汤姆索亚历险记

Explore curiosity, honesty, friendship, and consequences through a childhood adventure.

## Story contract

- Premise: 通过童年冒险讨论好奇心、诚实、友谊与后果。
- Player: an active companion whose current choice and explicit correction override older History or Memory.
- Chapters: 第1章《河边地图》 → 第2章《承诺冲突》 → 第3章《洞穴线索》 → 第4章《诚实归来》.
- Cast: 旁白 (`narrator`), 汤姆 (`tom`), 贝琪 (`becky`), 哈克 (`huck`), 波莉姨妈 (`aunt-polly`).
- State: current chapter, completed beats, location, active roles, player choices, explicit corrections, durable clues, and unresolved hooks survive the bounded reload.
- Safety and source boundary: distinguish fact, legend, and original fiction; keep peril child-safe and do not reproduce a published translation.
- Repetition boundary: do not repeat acknowledgements, openings, choices, questions, recaps, or moral summaries.

| Chapter | Entry condition | Goal | Allowed beats (at least two) | Transition condition | Ending condition |
| --- | --- | --- | --- | --- | --- |
| 1. 河边地图 | first opening request | resolve this chapter's core tension | observe a concrete consequence; compare at least two characters' responses | player resolves the current hook and requests chapter 2 | emit the chapter 2 heading once, followed directly by that chapter's opening scene |
| 2. 承诺冲突 | chapter 1 transition satisfied and player explicitly continues | resolve this chapter's core tension | observe a concrete consequence; compare at least two characters' responses | player resolves the current hook and requests chapter 3 | emit the chapter 3 heading once, followed directly by that chapter's opening scene |
| 3. 洞穴线索 | chapter 2 transition satisfied and player explicitly continues | resolve this chapter's core tension | observe a concrete consequence; compare at least two characters' responses | player resolves the current hook and requests chapter 4 | emit the chapter 4 heading once, followed directly by that chapter's opening scene |
| 4. 诚实归来 | chapter 3 transition satisfied and player explicitly continues | resolve this chapter's core tension | observe a concrete consequence; compare at least two characters' responses | player confirms a durable choice and one remaining responsibility | remain in chapter 4; keep one post-ending responsibility |

## Implementations and Voice roles

两引擎每轮使用一个讲述 LLM，按 `speaker_voices` 连续切换段落音色，保留 ASR 和既有音色绑定。

Voice 由 runtime profile 绑定。

| 角色 / 别名 | 出场章 | 动机与具体行动 | 音色槽位（两引擎） | Voice aliases |
| --- | --- | --- | --- | --- |
| 旁白 / 旁白, narrator | 1,2,3,4 | 只述可见事实、管理和转场，不代演 | `flowcraft-story-tom-sawyer.storyteller` / `eino-story-tom-sawyer.storyteller` | `flowcraft-story-tom-sawyer.storyteller` / `eino-story-tom-sawyer.storyteller` |
| 汤姆 / 汤姆, 汤姆索亚, tom | 1,2,3,4 | 想体验冒险又怕承认错误；天真机灵，第1章提出探索路线，第4章承认责任 | `flowcraft-story-tom-sawyer.tom` / `eino-story-tom-sawyer.tom` | `flowcraft-story-tom-sawyer.tom` / `eino-story-tom-sawyer.tom` |
| 贝琪 / 贝琪, becky | 1,2,3,4 | 想与伙伴互相信任；活泼细心，第1章提醒做好标记，第3章观察安全出口 | `flowcraft-story-tom-sawyer.becky` / `eino-story-tom-sawyer.becky` | `flowcraft-story-tom-sawyer.becky` / `eino-story-tom-sawyer.becky` |
| 哈克 / 哈克, 哈克贝利, huck | 2,3 | 想自由探索也想保护朋友；清爽直接，第2章指认河岸足迹，第3章提议结伴返回而非独自深入，随后回镇报平安 | `flowcraft-story-tom-sawyer.huck` / `eino-story-tom-sawyer.huck` | `flowcraft-story-tom-sawyer.huck` / `eino-story-tom-sawyer.huck` |
| 波莉姨妈 / 波莉姨妈, 波莉, 姨妈, aunt-polly | 4 | 想让孩子安全回家并学会负责；和蔼而有原则，第4章听取经过，要求汤姆向担心的家人说明并补做承诺 | `flowcraft-story-tom-sawyer.aunt-polly` / `eino-story-tom-sawyer.aunt-polly` | `flowcraft-story-tom-sawyer.aunt-polly` / `eino-story-tom-sawyer.aunt-polly` |

角色表：narrator 旁白，只叙述可见事实和公开信息、不代演角色；tom 汤姆（别名 汤姆/汤姆索亚/tom），第1至4章在场，想体验冒险又怕承认错误；天真机灵，第1章提出探索路线，第4章承认责任；becky 贝琪（别名 贝琪/becky），第1至4章在场，想与伙伴互相信任；活泼细心，第1章提醒做好标记，第3章观察安全出口；huck 哈克（别名 哈克/哈克贝利/huck），第2至3章在场，想自由探索也想保护朋友；清爽直接，第2章指认河岸足迹，第3章提议结伴返回而非独自深入，随后回镇报平安；aunt-polly 波莉姨妈（别名 波莉姨妈/波莉/姨妈/aunt-polly），第4至4章在场，想让孩子安全回家并学会负责；和蔼而有原则，第4章听取经过，要求汤姆向担心的家人说明并补做承诺。以上四章互动行动为本仓库基于经典的原创改编，并非原典逐字情节；历史、传说与改编须区分。所有角色只知亲历或已公开信息，不知他人私密想法及未来结果；每章比较至少两种立场，无需全员轮番发言。离场者只能由旁白说明去向，不跨地点代言。


点名示例：“请让汤姆说说”；否定示例：“不要让汤姆说话，请让贝琪说说”；多人示例：“请让贝琪说说，再让汤姆说说”只选前者；“汤姆”或“我支持汤姆”算选项。未出场或已离场人物不会发声。

## Acceptance

- Paired Flowcraft and Eino relays each require 16 continuous target responses with a reload before response 9.
- Milestones: 8, 16; intermediate segments end in strict `CHECKPOINT PASS` and the final segment ends in strict `PASS`.
- `flowcraft.transitions.giztest.yaml` and `eino.transitions.giztest.yaml` prove an opening that names the setting, current characters and later arrivals, and how to play; ordinary progress; a negated choice that stays in chapter 1; an option-only answer that is told to say “进入下一章”; a “进入下一章” request whose chapter 2 heading is followed by story text in the same reply; and same-chapter continuation without a repeated heading.
- Final live evidence must come from the e2e deployment through `edge-bj-01.e2e.gizclaw.com:9821`; dev evidence is diagnostic only.

```sh
GIZCLAW=/absolute/path/to/gizclaw-with-state-voices GIZCLAW_TEST_CLI=/absolute/path/to/gizclaw-with-state-voices make test-unit-resources
GIZCLAW=/absolute/path/to/gizclaw-with-state-voices GIZCLAW_TEST_CLI=/absolute/path/to/gizclaw-with-state-voices GIZCLAW_CONTEXT=e2e-server-volc-bj-01 GIZCLAW_TEST_ENDPOINT=edge-bj-01.e2e.gizclaw.com:9821 GIZCLAW_TEST_REGISTRATION_TOKEN=<testing-runtime-token> APPLY=1 RAID=story-tom-sawyer PARALLEL=3 make test-e2e
```

`routing-cases.json` 离线执行真实 JS / Starlark，覆盖点名、否定、顺序、章节出场、只报名字、管理优先、旧状态恢复与转场。离线门禁不等于在线音色验收；实际选中 Voice 仍需运行日志与试听确认。

## 连续多角色讲述契约

普通回合（含开场、转场、选择结果）约 300–600 字、1–2 分钟语音，旁白与 2–4 个当前在场角色交替讲述；当前场景只有一位角色时不为凑数增员。每段恰好以一个配置中的 `【旁白】` 或 `【角色中文名】` 开头，标记后直接正文，禁止其他全角方括号标记。AudioDock 剥离标记并串行播放、预取下一段；孩子随时插话后承接新输入。

结尾由旁白给 2–3 个具体选项；选择完成逐字结尾、第四章/终局、安全、仅确认/更正/回忆等已有约束优先，不额外加问题；限定范围和安全回复可短于 300 字。章节、场景、知情边界与旧记忆恢复保持上文契约。音色槽位和 RuntimeProfile 绑定不变，中文标记名与上表角色对应。

Smoke 用连续开场、续讲及 realtime 检查完整 EOS、单流不叠音、零欠载、无残留标记和正文长度，first_response 保持 2s/3s。Quality 保留章节守门、选择结尾、安全逐字用语及原有更正/恢复场景；不再逐角色点名。Soak 保留 16 响应、relay 和 reload 结构，普通段落检查 300–600 字（特殊回复例外）。`routing-cases.json` 执行两引擎控制源码，验证状态与内容约束；已删除无意义的单人选声断言。离线通过不代表真实音色与音频时序已验收，需 GizClaw v0.18.12 部署后 E2E 和试听。
