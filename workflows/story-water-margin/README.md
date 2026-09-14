# Heroes of the Water Margin (`story-water-margin`) — 水浒群英

Use Water Margin characters to discuss courage, rules, friendship, and responsibility.

## Story contract

- Premise: 通过水浒人物故事讨论勇气、规则、友情与责任。
- Player: an active companion whose current choice and explicit correction override older History or Memory.
- Chapters: 第1章《朋友受屈》 → 第2章《冲动与规则》 → 第3章《证据转折》 → 第4章《担当收束》.
- Cast: 旁白 (`narrator`), 林冲 (`lin-chong`), 鲁智深 (`lu-zhishen`), 武松 (`wu-song`), 宋江 (`song-jiang`).
- State: current chapter, completed beats, location, active roles, player choices, explicit corrections, durable clues, and unresolved hooks survive the bounded reload.
- Safety and source boundary: distinguish fact, legend, and original fiction; keep peril child-safe and do not reproduce a published translation.
- Repetition boundary: do not repeat acknowledgements, openings, choices, questions, recaps, or moral summaries.

| Chapter | Entry condition | Goal | Allowed beats (at least two) | Transition condition | Ending condition |
| --- | --- | --- | --- | --- | --- |
| 1. 朋友受屈 | first opening request | resolve this chapter's core tension | observe a concrete consequence; compare at least two characters' responses | player resolves the current hook and requests chapter 2 | emit the chapter 2 heading once, followed directly by that chapter's opening scene |
| 2. 冲动与规则 | chapter 1 transition satisfied and player explicitly continues | resolve this chapter's core tension | observe a concrete consequence; compare at least two characters' responses | player resolves the current hook and requests chapter 3 | emit the chapter 3 heading once, followed directly by that chapter's opening scene |
| 3. 证据转折 | chapter 2 transition satisfied and player explicitly continues | resolve this chapter's core tension | observe a concrete consequence; compare at least two characters' responses | player resolves the current hook and requests chapter 4 | emit the chapter 4 heading once, followed directly by that chapter's opening scene |
| 4. 担当收束 | chapter 3 transition satisfied and player explicitly continues | resolve this chapter's core tension | observe a concrete consequence; compare at least two characters' responses | player confirms a durable choice and one remaining responsibility | remain in chapter 4; keep one post-ending responsibility |

## Implementations and Voice roles

两引擎每轮使用一个讲述 LLM，按 `speaker_voices` 连续切换段落音色，保留 ASR 和既有音色绑定。

Voice 由 runtime profile 绑定。

| 角色 / 别名 | 出场章 | 动机与具体行动 | 音色槽位（两引擎） | Voice aliases |
| --- | --- | --- | --- | --- |
| 旁白 / 旁白, narrator | 1,2,3,4 | 只述可见事实、管理和转场，不代演 | `flowcraft-story-water-margin.storyteller` / `eino-story-water-margin.storyteller` | `flowcraft-story-water-margin.storyteller` / `eino-story-water-margin.storyteller` |
| 林冲 / 林冲, 林教头, lin-chong | 1,2,3,4 | 想讲清是非并保护无辜；清晰克制，第1章核对求助经过，第4章承担守约责任 | `flowcraft-story-water-margin.lin-chong` / `eino-story-water-margin.lin-chong` | `flowcraft-story-water-margin.lin-chong` / `eino-story-water-margin.lin-chong` |
| 鲁智深 / 鲁智深, 鲁提辖, lu-zhishen | 1,2,3,4 | 想立即帮助弱者；憨厚直率，第1章提议先安置求助者，第3章劝阻冲动 | `flowcraft-story-water-margin.lu-zhishen` / `eino-story-water-margin.lu-zhishen` | `flowcraft-story-water-margin.lu-zhishen` / `eino-story-water-margin.lu-zhishen` |
| 武松 / 武松, wu-song | 2,3 | 想辨清事实再行动；清爽坚定，第2章沿路核对目击线索，第3章提议先护送受困者再求助，之后外出护送 | `flowcraft-story-water-margin.wu-song` / `eino-story-water-margin.wu-song` | `flowcraft-story-water-margin.wu-song` / `eino-story-water-margin.wu-song` |
| 宋江 / 宋江, 宋公明, song-jiang | 3,4 | 想协调伙伴承担责任；沉稳审慎，第3章比较各方公开说法并安排互助，第4章提出守信与不伤及无辜的约定 | `flowcraft-story-water-margin.song-jiang` / `eino-story-water-margin.song-jiang` | `flowcraft-story-water-margin.song-jiang` / `eino-story-water-margin.song-jiang` |

角色表：narrator 旁白，只叙述可见事实和公开信息、不代演角色；lin-chong 林冲（别名 林冲/林教头/lin-chong），第1至4章在场，想讲清是非并保护无辜；清晰克制，第1章核对求助经过，第4章承担守约责任；lu-zhishen 鲁智深（别名 鲁智深/鲁提辖/lu-zhishen），第1至4章在场，想立即帮助弱者；憨厚直率，第1章提议先安置求助者，第3章劝阻冲动；wu-song 武松（别名 武松/wu-song），第2至3章在场，想辨清事实再行动；清爽坚定，第2章沿路核对目击线索，第3章提议先护送受困者再求助，之后外出护送；song-jiang 宋江（别名 宋江/宋公明/song-jiang），第3至4章在场，想协调伙伴承担责任；沉稳审慎，第3章比较各方公开说法并安排互助，第4章提出守信与不伤及无辜的约定。以上四章互动行动为本仓库基于经典的原创改编，并非原典逐字情节；历史、传说与改编须区分。所有角色只知亲历或已公开信息，不知他人私密想法及未来结果；每章比较至少两种立场，无需全员轮番发言。离场者只能由旁白说明去向，不跨地点代言。


点名示例：“请让林冲说说”；否定示例：“不要让林冲说话，请让鲁智深说说”；多人示例：“请让鲁智深说说，再让林冲说说”只选前者；“林冲”或“我支持林冲”算选项。未出场或已离场人物不会发声。

## Acceptance

- Paired Flowcraft and Eino relays each require 16 continuous target responses with a reload before response 9.
- Milestones: 8, 16; intermediate segments end in strict `CHECKPOINT PASS` and the final segment ends in strict `PASS`.
- `flowcraft.transitions.giztest.yaml` and `eino.transitions.giztest.yaml` prove an opening that names the setting, current characters and later arrivals, and how to play; ordinary progress; a negated choice that stays in chapter 1; an option-only answer that is told to say “进入下一章”; a “进入下一章” request whose chapter 2 heading is followed by story text in the same reply; and same-chapter continuation without a repeated heading.
- Final live evidence must come from the e2e deployment through `edge-bj-01.e2e.gizclaw.com:9821`; dev evidence is diagnostic only.

```sh
GIZCLAW=/absolute/path/to/gizclaw-with-state-voices GIZCLAW_TEST_CLI=/absolute/path/to/gizclaw-with-state-voices make test-unit-resources
GIZCLAW=/absolute/path/to/gizclaw-with-state-voices GIZCLAW_TEST_CLI=/absolute/path/to/gizclaw-with-state-voices GIZCLAW_CONTEXT=e2e-server-volc-bj-01 GIZCLAW_TEST_ENDPOINT=edge-bj-01.e2e.gizclaw.com:9821 GIZCLAW_TEST_REGISTRATION_TOKEN=<testing-runtime-token> APPLY=1 RAID=story-water-margin PARALLEL=3 make test-e2e
```

`routing-cases.json` 离线执行真实 JS / Starlark，覆盖点名、否定、顺序、章节出场、只报名字、管理优先、旧状态恢复与转场。离线门禁不等于在线音色验收；实际选中 Voice 仍需运行日志与试听确认。

## 连续多角色讲述契约

普通回合（含开场、转场、选择结果）约 300–600 字、1–2 分钟语音，旁白与 2–4 个当前在场角色交替讲述；当前场景只有一位角色时不为凑数增员。每段恰好以一个配置中的 `【旁白】` 或 `【角色中文名】` 开头，标记后直接正文，禁止其他全角方括号标记。AudioDock 剥离标记并串行播放、预取下一段；孩子随时插话后承接新输入。

结尾由旁白给 2–3 个具体选项；选择完成逐字结尾、第四章/终局、安全、仅确认/更正/回忆等已有约束优先，不额外加问题；限定范围和安全回复可短于 300 字。章节、场景、知情边界与旧记忆恢复保持上文契约。音色槽位和 RuntimeProfile 绑定不变，中文标记名与上表角色对应。

Smoke 用连续开场、续讲及 realtime 检查完整 EOS、单流不叠音、零欠载、无残留标记和正文长度，first_response 保持 2s/3s。Quality 保留章节守门、选择结尾、安全逐字用语及原有更正/恢复场景；不再逐角色点名。Soak 保留 16 响应、relay 和 reload 结构，普通段落检查 300–600 字（特殊回复例外）。`routing-cases.json` 执行两引擎控制源码，验证状态与内容约束；已删除无意义的单人选声断言。离线通过不代表真实音色与音频时序已验收，需 GizClaw v0.18.12 部署后 E2E 和试听。
