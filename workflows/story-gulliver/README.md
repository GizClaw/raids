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

Flowcraft 每轮选择一个 published 节点；Eino 保留一个 primary chat_model，由 Starlark 写入 selected_speaker，state_voices 绑定音色。两引擎保留 ASR 和原记忆链路。

| 角色（别名） | 章节 | 动机与行动 | 两引擎槽位 | Voice ID |
| --- | --- | --- | --- | --- |
| 旁白 (旁白/narrator) | 1,2,3,4 | 可见事实与转场，不代演 | `flowcraft-story-gulliver.storyteller` / `eino-story-gulliver.storyteller` | `volc-tenant:volc-cn-beijing:zh_female_shaoergushi_mars_bigtts` |
| 格列佛 (格列佛/gulliver) | 1,2,3,4 | 想平等交流；清晰理性，第1章先放低身姿。 | `flowcraft-story-gulliver.gulliver` / `eino-story-gulliver.gulliver` | `volc-tenant:volc-cn-beijing:zh_male_jieshuoxiaoming_uranus_bigtts` |
| 当地向导 (当地向导/local-guide) | 1,2 | 想保护小人国的生活；活泼机灵，第1章解释礼节，第2章提醒尊重居民；不随行巨人国。 | `flowcraft-story-gulliver.local-guide` / `eino-story-gulliver.local-guide` | `volc-tenant:volc-cn-beijing:ICL_zh_female_huoponvhai_tob` |
| 国王 (国王/king) | 2 | 希望礼节维持秩序；年长幽默，第2章听取格列佛意见，讨论修改不公平礼节；这是小人国国王。 | `flowcraft-story-gulliver.king` / `eino-story-gulliver.king` | `volc-tenant:volc-cn-beijing:ICL_zh_male_youmodaye_tob` |
| 葛兰达克利赤 (葛兰达克利赤/glumdalclitch) | 3,4 | 想照料微小的客人且尊重自主；温柔稳重，第3章安置安全住处，第4章提议先征求格列佛同意。 | `flowcraft-story-gulliver.glumdalclitch` / `eino-story-gulliver.glumdalclitch` | `volc-tenant:volc-cn-beijing:zh_female_wenroushunv_uranus_bigtts` |

角色表：narrator 旁白（别名 旁白/narrator），只在第1、2、3、4章在场，只述可见事实，不代演角色；gulliver 格列佛（别名 格列佛/gulliver），只在第1、2、3、4章在场，想平等交流；清晰理性，第1章先放低身姿；local-guide 当地向导（别名 当地向导/local-guide），只在第1、2章在场，想保护小人国的生活；活泼机灵，第1章解释礼节，第2章提醒尊重居民；不随行巨人国；king 国王（别名 国王/king），只在第2章在场，希望礼节维持秩序；年长幽默，第2章听取格列佛意见，讨论修改不公平礼节；这是小人国国王；glumdalclitch 葛兰达克利赤（别名 葛兰达克利赤/glumdalclitch），只在第3、4章在场，想照料微小的客人且尊重自主；温柔稳重，第3章安置安全住处，第4章提议先征求格列佛同意。所有角色只说亲历或已公开信息，不知他人私密想法及未来结果。每章比较至少两种立场，不要求全员发声。章节行动属于本仓库儿童互动原创改编，不等同原典情节。

点名示例：“请让格列佛说说”；“不要让格列佛说话，请让当地向导说说”；“请让当地向导说说，再让格列佛说说”只选文本顺序首个在场者。只说“格列佛”或“我支持格列佛”算玩家选择。开场、转场（含阻塞）、更正、安全管理优先旁白，未在场角色不可点名，旧记忆 active_roles 按章节重建。

## 验证

两份 roles Giztest 各有 5 个隔离 Workspace，后续角色先完成真实章节前置；检查 text/audio EOS、audio_bytes > 0，首响应保持文本 2s、音频 3s。保留 16 轮 relay、reload、更正、转场与 RealTime 用例；routing-cases.json 执行真实 JS 和 Starlark。离线门禁不证明实际音色正确，运行时 Voice ID 日志与试听仍需在线验收。
