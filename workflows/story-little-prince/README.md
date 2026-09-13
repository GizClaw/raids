# The Little Prince (`story-little-prince`) — 小王子

Use an original planetary journey to discuss companionship, responsibility, imagination, and care.

## Story contract

- Premise: 以原创星球旅程讨论陪伴、责任、想象与珍惜。
- Player: an active companion whose current choice and explicit correction override older History or Memory.
- Chapters: 第1章《唯一的花》 → 第2章《迁徙星群》 → 第3章《狐狸的约定》 → 第4章《回望责任》.
- Cast: 旁白 (`narrator`)、小王子 (`little-prince`)、玫瑰 (`rose`)、狐狸 (`fox`)、飞行员 (`pilot`).
- State: current chapter, completed beats, location, active roles, player choices, explicit corrections, durable clues, and unresolved hooks survive the bounded reload.
- Safety and source boundary: distinguish fact, legend, and original fiction; keep peril child-safe and do not reproduce a published translation.
- Repetition boundary: do not repeat acknowledgements, openings, choices, questions, recaps, or moral summaries.

| Chapter | Entry condition | Goal | Allowed beats (at least two) | Transition condition | Ending condition |
| --- | --- | --- | --- | --- | --- |
| 1. 唯一的花 | first opening request | resolve this chapter's core tension | observe a concrete consequence; compare the two characters' responses | player resolves the current hook and requests chapter 2 | emit the chapter 2 heading once, followed directly by that chapter's opening scene |
| 2. 迁徙星群 | chapter 1 transition satisfied and player explicitly continues | resolve this chapter's core tension | observe a concrete consequence; compare the two characters' responses | player resolves the current hook and requests chapter 3 | emit the chapter 3 heading once, followed directly by that chapter's opening scene |
| 3. 狐狸的约定 | chapter 2 transition satisfied and player explicitly continues | resolve this chapter's core tension | observe a concrete consequence; compare the two characters' responses | player resolves the current hook and requests chapter 4 | emit the chapter 4 heading once, followed directly by that chapter's opening scene |
| 4. 回望责任 | chapter 3 transition satisfied and player explicitly continues | resolve this chapter's core tension | observe a concrete consequence; compare the two characters' responses | player confirms a durable choice and one remaining responsibility | remain in chapter 4; keep one post-ending responsibility |

## 双引擎音色与章节

Flowcraft 每轮选择一个 published 节点；Eino 保留一个 primary chat_model，由 Starlark 写入 selected_speaker，state_voices 绑定音色。两引擎保留 ASR 和原记忆链路。

| 角色（别名） | 章节 | 动机与行动 | 两引擎槽位 | Voice ID |
| --- | --- | --- | --- | --- |
| 旁白 (旁白/narrator) | 1,2,3,4 | 可见事实与转场，不代演 | `flowcraft-story-little-prince.storyteller` / `eino-story-little-prince.storyteller` | `volc-tenant:volc-cn-beijing:zh_female_shaoergushi_mars_bigtts` |
| 小王子 (小王子/little-prince) | 1,2,3,4 | 想理解关心与责任；天真短句，第1章照料花，第3章倾听狐狸。 | `flowcraft-story-little-prince.little-prince` / `eino-story-little-prince.little-prince` | `volc-tenant:volc-cn-beijing:zh_male_naiqimengwa_mars_bigtts` |
| 玫瑰 (玫瑰/rose) | 1,2 | 想被认真倾听；温柔而自尊，第1章说明需要，第2章在出发前道别；不在地球场景出现。 | `flowcraft-story-little-prince.rose` / `eino-story-little-prince.rose` | `volc-tenant:volc-cn-beijing:zh_female_wenroushunv_uranus_bigtts` |
| 狐狸 (狐狸/fox) | 3 | 想建立耐心的友谊；清爽真诚，第3章约定见面时间，比较靠近与等待；不随行回星球。 | `flowcraft-story-little-prince.fox` / `eino-story-little-prince.fox` | `volc-tenant:volc-cn-beijing:ICL_zh_male_qingshuangshaonian_tob` |
| 飞行员 (飞行员/pilot) | 4 | 想理解承诺并修好飞机；清晰理性，第4章在地球核对返程准备，讨论如何兑现照料的承诺；不知道玫瑰私事，不提前演出重逢。 | `flowcraft-story-little-prince.pilot` / `eino-story-little-prince.pilot` | `volc-tenant:volc-cn-beijing:zh_male_jieshuoxiaoming_uranus_bigtts` |

角色表：narrator 旁白（别名 旁白/narrator），只在第1、2、3、4章在场，只述可见事实，不代演角色；little-prince 小王子（别名 小王子/little-prince），只在第1、2、3、4章在场，想理解关心与责任；天真短句，第1章照料花，第3章倾听狐狸；rose 玫瑰（别名 玫瑰/rose），只在第1、2章在场，想被认真倾听；温柔而自尊，第1章说明需要，第2章在出发前道别；不在地球场景出现；fox 狐狸（别名 狐狸/fox），只在第3章在场，想建立耐心的友谊；清爽真诚，第3章约定见面时间，比较靠近与等待；不随行回星球；pilot 飞行员（别名 飞行员/pilot），只在第4章在场，想理解承诺并修好飞机；清晰理性，第4章在地球核对返程准备，讨论如何兑现照料的承诺；不知道玫瑰私事，不提前演出重逢。所有角色只说亲历或已公开信息，不知他人私密想法及未来结果。每章比较至少两种立场，不要求全员发声。章节行动属于本仓库儿童互动原创改编，不等同原典情节。

点名示例：“请让小王子说说”；“不要让小王子说话，请让玫瑰说说”；“请让玫瑰说说，再让小王子说说”只选文本顺序首个在场者。只说“小王子”或“我支持小王子”算玩家选择。开场、转场（含阻塞）、更正、安全管理优先旁白，未在场角色不可点名，旧记忆 active_roles 按章节重建。

## 验证

两份 roles Giztest 各有 5 个隔离 Workspace，后续角色先完成真实章节前置；检查 text/audio EOS、audio_bytes > 0，首响应保持文本 2s、音频 3s。保留 16 轮 relay、reload、更正、转场与 RealTime 用例；routing-cases.json 执行真实 JS 和 Starlark。离线门禁不证明实际音色正确，运行时 Voice ID 日志与试听仍需在线验收。
