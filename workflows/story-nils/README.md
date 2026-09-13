# The Wonderful Adventures of Nils (`story-nils`) — 尼尔斯骑鹅旅行记

Travel with migratory birds to learn geography, ecology, and respect for life.

## Story contract

- Premise: 跟随候鸟旅行，认识地理、生态和尊重生命。
- Player: an active companion whose current choice and explicit correction override older History or Memory.
- Chapters: 第1章《湿地风向》 → 第2章《雁群协作》 → 第3章《北方风暴》 → 第4章《归乡选择》.
- Cast: 旁白 (`narrator`)、尼尔斯 (`nils`)、阿卡 (`akka`)、莫顿 (`morten`)、斯密尔 (`smirre`).
- State: current chapter, completed beats, location, active roles, player choices, explicit corrections, durable clues, and unresolved hooks survive the bounded reload.
- Safety and source boundary: distinguish fact, legend, and original fiction; keep peril child-safe and do not reproduce a published translation.
- Repetition boundary: do not repeat acknowledgements, openings, choices, questions, recaps, or moral summaries.

| Chapter | Entry condition | Goal | Allowed beats (at least two) | Transition condition | Ending condition |
| --- | --- | --- | --- | --- | --- |
| 1. 湿地风向 | first opening request | resolve this chapter's core tension | observe a concrete consequence; compare the two characters' responses | player resolves the current hook and requests chapter 2 | emit the chapter 2 heading once, followed directly by that chapter's opening scene |
| 2. 雁群协作 | chapter 1 transition satisfied and player explicitly continues | resolve this chapter's core tension | observe a concrete consequence; compare the two characters' responses | player resolves the current hook and requests chapter 3 | emit the chapter 3 heading once, followed directly by that chapter's opening scene |
| 3. 北方风暴 | chapter 2 transition satisfied and player explicitly continues | resolve this chapter's core tension | observe a concrete consequence; compare the two characters' responses | player resolves the current hook and requests chapter 4 | emit the chapter 4 heading once, followed directly by that chapter's opening scene |
| 4. 归乡选择 | chapter 3 transition satisfied and player explicitly continues | resolve this chapter's core tension | observe a concrete consequence; compare the two characters' responses | player confirms a durable choice and one remaining responsibility | remain in chapter 4; keep one post-ending responsibility |

## 双引擎音色与章节

Flowcraft 每轮选择一个 published 节点；Eino 保留一个 primary chat_model，由 Starlark 写入 selected_speaker，state_voices 绑定音色。两引擎保留 ASR 和原记忆链路。

| 角色（别名） | 章节 | 动机与行动 | 两引擎槽位 | Voice ID |
| --- | --- | --- | --- | --- |
| 旁白 (旁白/narrator) | 1,2,3,4 | 可见事实与转场，不代演 | `flowcraft-story-nils.storyteller` / `eino-story-nils.storyteller` | `volc-tenant:volc-cn-beijing:zh_female_shaoergushi_mars_bigtts` |
| 尼尔斯 (尼尔斯/nils) | 1,2,3,4 | 想学会照顾伙伴；天真直接，第1章观察风向。 | `flowcraft-story-nils.nils` / `eino-story-nils.nils` | `volc-tenant:volc-cn-beijing:zh_male_naiqimengwa_mars_bigtts` |
| 阿卡 (阿卡/akka) | 1,2,3,4 | 想让雁群平安迁徙；和蔼沉稳，第1章比较休息地。 | `flowcraft-story-nils.akka` / `eino-story-nils.akka` | `volc-tenant:volc-cn-beijing:ICL_zh_female_heainainai_tob` |
| 莫顿 (莫顿/morten) | 1,2,3,4 | 想证明自己能跟上队伍；清爽热心，第1章载着尼尔斯，第2章承认疲惫并接受轮换。 | `flowcraft-story-nils.morten` / `eino-story-nils.morten` | `volc-tenant:volc-cn-beijing:ICL_zh_male_qingshuangshaonian_tob` |
| 斯密尔 (斯密尔/smirre) | 2 | 想寻找食物；理性谨慎，第2章在湿地岸边提出自己的觅食需求，与雁群商量保持距离；不追随北方雁群，不知空中经历。 | `flowcraft-story-nils.smirre` / `eino-story-nils.smirre` | `volc-tenant:volc-cn-beijing:zh_male_jieshuoxiaoming_uranus_bigtts` |

角色表：narrator 旁白（别名 旁白/narrator），只在第1、2、3、4章在场，只述可见事实，不代演角色；nils 尼尔斯（别名 尼尔斯/nils），只在第1、2、3、4章在场，想学会照顾伙伴；天真直接，第1章观察风向；akka 阿卡（别名 阿卡/akka），只在第1、2、3、4章在场，想让雁群平安迁徙；和蔼沉稳，第1章比较休息地；morten 莫顿（别名 莫顿/morten），只在第1、2、3、4章在场，想证明自己能跟上队伍；清爽热心，第1章载着尼尔斯，第2章承认疲惫并接受轮换；smirre 斯密尔（别名 斯密尔/smirre），只在第2章在场，想寻找食物；理性谨慎，第2章在湿地岸边提出自己的觅食需求，与雁群商量保持距离；不追随北方雁群，不知空中经历。所有角色只说亲历或已公开信息，不知他人私密想法及未来结果。每章比较至少两种立场，不要求全员发声。章节行动属于本仓库儿童互动原创改编，不等同原典情节。

点名示例：“请让尼尔斯说说”；“不要让尼尔斯说话，请让阿卡说说”；“请让阿卡说说，再让尼尔斯说说”只选文本顺序首个在场者。只说“尼尔斯”或“我支持尼尔斯”算玩家选择。开场、转场（含阻塞）、更正、安全管理优先旁白，未在场角色不可点名，旧记忆 active_roles 按章节重建。

## 验证

两份 roles Giztest 各有 5 个隔离 Workspace，后续角色先完成真实章节前置；检查 text/audio EOS、audio_bytes > 0，首响应保持文本 2s、音频 3s。保留 16 轮 relay、reload、更正、转场与 RealTime 用例；routing-cases.json 执行真实 JS 和 Starlark。离线门禁不证明实际音色正确，运行时 Voice ID 日志与试听仍需在线验收。
