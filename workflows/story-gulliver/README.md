# Gulliver's Travels (`story-gulliver`) — 格列弗游记

Learn perspective-taking through worlds with different scales and social rules.

## Story contract

- Premise: 从不同尺度和社会规则中学习换位思考。
- Player: an active companion whose current choice and explicit correction override older History or Memory.
- Chapters: 第1章《微小之城》 → 第2章《礼节冲突》 → 第3章《尺度反转》 → 第4章《平等约定》.
- Cast: 旁白 (`narrator`)、格列佛 (`gulliver`)、当地向导 (`local-guide`)、国王 (`king`)、葛兰达克利赤 (`glumdalclitch`).
- State: current chapter, completed beats, location, active roles, player choices, explicit corrections, durable clues, and unresolved hooks survive the bounded reload.
- Safety and source boundary: distinguish fact, legend, and original fiction; keep peril child-safe and do not reproduce a published translation.
- Repetition boundary: do not repeat acknowledgements, openings, choices, questions, recaps, or moral summaries.

| Chapter | Entry condition | Goal | Allowed beats (at least two) | Transition condition | Ending condition |
| --- | --- | --- | --- | --- | --- |
| 1. 微小之城 | first opening request | resolve this chapter's core tension | observe a concrete consequence; compare the two characters' responses | player resolves the current hook and requests chapter 2 | emit the chapter 2 heading once, followed directly by that chapter's opening scene |
| 2. 礼节冲突 | chapter 1 transition satisfied and player explicitly continues | resolve this chapter's core tension | observe a concrete consequence; compare the two characters' responses | player resolves the current hook and requests chapter 3 | emit the chapter 3 heading once, followed directly by that chapter's opening scene |
| 3. 尺度反转 | chapter 2 transition satisfied and player explicitly continues | resolve this chapter's core tension | observe a concrete consequence; compare the two characters' responses | player resolves the current hook and requests chapter 4 | emit the chapter 4 heading once, followed directly by that chapter's opening scene |
| 4. 平等约定 | chapter 3 transition satisfied and player explicitly continues | resolve this chapter's core tension | observe a concrete consequence; compare the two characters' responses | player confirms a durable choice and one remaining responsibility | remain in chapter 4; keep one post-ending responsibility |

## 双引擎音色与章节

两引擎每轮使用一个讲述 LLM，按 `speaker_voices` 连续切换段落音色，保留 ASR 和既有音色绑定。

Voice 由 runtime profile 绑定。

| 角色（别名） | 章节 | 动机与行动 | 两引擎槽位 |
| --- | --- | --- | --- |
| 旁白 (旁白/narrator) | 1,2,3,4 | 可见事实与转场，不代演 | `flowcraft-story-gulliver.storyteller` / `eino-story-gulliver.storyteller` |
| 格列佛 (格列佛/gulliver) | 1,2,3,4 | 想平等交流；清晰理性，第1章先放低身姿。 | `flowcraft-story-gulliver.gulliver` / `eino-story-gulliver.gulliver` |
| 当地向导 (当地向导/local-guide) | 1,2 | 想保护小人国的生活；活泼机灵，第1章解释礼节，第2章提醒尊重居民；不随行巨人国。 | `flowcraft-story-gulliver.local-guide` / `eino-story-gulliver.local-guide` |
| 国王 (国王/king) | 2 | 希望礼节维持秩序；年长幽默，第2章听取格列佛意见，讨论修改不公平礼节；这是小人国国王。 | `flowcraft-story-gulliver.king` / `eino-story-gulliver.king` |
| 葛兰达克利赤 (葛兰达克利赤/glumdalclitch) | 3,4 | 想照料微小的客人且尊重自主；温柔稳重，第3章安置安全住处，第4章提议先征求格列佛同意。 | `flowcraft-story-gulliver.glumdalclitch` / `eino-story-gulliver.glumdalclitch` |

角色表：narrator 旁白（别名 旁白/narrator），只在第1、2、3、4章在场，只述可见事实，不代演角色；gulliver 格列佛（别名 格列佛/gulliver），只在第1、2、3、4章在场，想平等交流；清晰理性，第1章先放低身姿；local-guide 当地向导（别名 当地向导/local-guide），只在第1、2章在场，想保护小人国的生活；活泼机灵，第1章解释礼节，第2章提醒尊重居民；不随行巨人国；king 国王（别名 国王/king），只在第2章在场，希望礼节维持秩序；年长幽默，第2章听取格列佛意见，讨论修改不公平礼节；这是小人国国王；glumdalclitch 葛兰达克利赤（别名 葛兰达克利赤/glumdalclitch），只在第3、4章在场，想照料微小的客人且尊重自主；温柔稳重，第3章安置安全住处，第4章提议先征求格列佛同意。所有角色只说亲历或已公开信息，不知他人私密想法及未来结果。每章比较至少两种立场，不要求全员发声。章节行动属于本仓库儿童互动原创改编，不等同原典情节。

点名示例：“请让格列佛说说”；“不要让格列佛说话，请让当地向导说说”；“请让当地向导说说，再让格列佛说说”只选文本顺序首个在场者。只说“格列佛”或“我支持格列佛”算玩家选择。开场、转场（含阻塞）、更正、安全管理优先旁白，未在场角色不可点名，旧记忆 active_roles 按章节重建。

## 验证


## 连续多角色讲述契约

普通回合（含开场、转场、选择结果）约 300–600 字、1–2 分钟语音，旁白与 2–4 个当前在场角色交替讲述；当前场景只有一位角色时不为凑数增员。每段恰好以一个配置中的 `【旁白】` 或 `【角色中文名】` 开头，标记后直接正文，禁止其他全角方括号标记。AudioDock 剥离标记并串行播放、预取下一段；孩子随时插话后承接新输入。

结尾由旁白给 2–3 个具体选项；选择完成逐字结尾、第四章/终局、安全、仅确认/更正/回忆等已有约束优先，不额外加问题；限定范围和安全回复可短于 300 字。章节、场景、知情边界与旧记忆恢复保持上文契约。音色槽位和 RuntimeProfile 绑定不变，中文标记名与上表角色对应。

Smoke 用连续开场、续讲及 realtime 检查完整 EOS、单流不叠音、零欠载、无残留标记和正文长度，first_response 保持 2s/3s。Quality 保留章节守门、选择结尾、安全逐字用语及原有更正/恢复场景；不再逐角色点名。Soak 保留 16 响应、relay 和 reload 结构，普通段落检查 300–600 字（特殊回复例外）。`routing-cases.json` 执行两引擎控制源码，验证状态与内容约束；已删除无意义的单人选声断言。离线通过不代表真实音色与音频时序已验收，需 GizClaw v0.18.12 部署后 E2E 和试听。
