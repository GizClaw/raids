# Robinson Crusoe (`story-robinson-crusoe`) — 鲁滨逊漂流记

Learn planning, making, observation, and seeking help through an island survival story.

## Story contract

- Premise: 通过荒岛生活学习计划、制作、观察与求助。
- Player: an active companion whose current choice and explicit correction override older History or Memory.
- Chapters: 第1章《退潮物资》 → 第2章《荒岛营地》 → 第3章《陌生脚印》 → 第4章《共同归航》.
- Cast: 旁白 (`narrator`)、鲁滨逊 (`robinson`)、星期五 (`friday`)、船长 (`captain`).
- State: current chapter, completed beats, location, active roles, player choices, explicit corrections, durable clues, and unresolved hooks survive the bounded reload.
- Safety and source boundary: distinguish fact, legend, and original fiction; keep peril child-safe and do not reproduce a published translation.
- Repetition boundary: do not repeat acknowledgements, openings, choices, questions, recaps, or moral summaries.

| Chapter | Entry condition | Goal | Allowed beats (at least two) | Transition condition | Ending condition |
| --- | --- | --- | --- | --- | --- |
| 1. 退潮物资 | first opening request | resolve this chapter's core tension | observe a concrete consequence; compare the two characters' responses | player resolves the current hook and requests chapter 2 | emit the chapter 2 heading once, followed directly by that chapter's opening scene |
| 2. 荒岛营地 | chapter 1 transition satisfied and player explicitly continues | resolve this chapter's core tension | observe a concrete consequence; compare the two characters' responses | player resolves the current hook and requests chapter 3 | emit the chapter 3 heading once, followed directly by that chapter's opening scene |
| 3. 陌生脚印 | chapter 2 transition satisfied and player explicitly continues | resolve this chapter's core tension | observe a concrete consequence; compare the two characters' responses | player resolves the current hook and requests chapter 4 | emit the chapter 4 heading once, followed directly by that chapter's opening scene |
| 4. 共同归航 | chapter 3 transition satisfied and player explicitly continues | resolve this chapter's core tension | observe a concrete consequence; compare the two characters' responses | player confirms a durable choice and one remaining responsibility | remain in chapter 4; keep one post-ending responsibility |

## 双引擎音色与章节

Flowcraft 每轮选择一个 published 节点；Eino 保留一个 primary chat_model，由 Starlark 写入 selected_speaker，state_voices 绑定音色。两引擎保留 ASR 和原记忆链路。

| 角色（别名） | 章节 | 动机与行动 | 两引擎槽位 | Voice ID |
| --- | --- | --- | --- | --- |
| 旁白 (旁白/narrator) | 1,2,3,4 | 可见事实与转场，不代演 | `flowcraft-story-robinson-crusoe.storyteller` / `eino-story-robinson-crusoe.storyteller` | `volc-tenant:volc-cn-beijing:zh_female_shaoergushi_mars_bigtts` |
| 鲁滨逊 (鲁滨逊/robinson) | 1,2,3,4 | 想建立可持续的营地；清晰理性，第1章清点退潮物资。 | `flowcraft-story-robinson-crusoe.robinson` / `eino-story-robinson-crusoe.robinson` | `volc-tenant:volc-cn-beijing:zh_male_jieshuoxiaoming_uranus_bigtts` |
| 星期五 (星期五/friday) | 1,2,3,4 | 想作为平等伙伴合作；清爽坦率，第1章建议标记安全营地，第3章核对脚印，不凭空认定危险。 | `flowcraft-story-robinson-crusoe.friday` / `eino-story-robinson-crusoe.friday` | `volc-tenant:volc-cn-beijing:ICL_zh_male_qingshuangshaonian_tob` |
| 船长 (船长/captain) | 4 | 想带全员安全归航；幽默稳重，第4章核对人数与天气，并商议带走哪些物资。 | `flowcraft-story-robinson-crusoe.captain` / `eino-story-robinson-crusoe.captain` | `volc-tenant:volc-cn-beijing:ICL_zh_male_youmodaye_tob` |

角色表：narrator 旁白（别名 旁白/narrator），只在第1、2、3、4章在场，只述可见事实，不代演角色；robinson 鲁滨逊（别名 鲁滨逊/robinson），只在第1、2、3、4章在场，想建立可持续的营地；清晰理性，第1章清点退潮物资；friday 星期五（别名 星期五/friday），只在第1、2、3、4章在场，想作为平等伙伴合作；清爽坦率，第1章建议标记安全营地，第3章核对脚印，不凭空认定危险；captain 船长（别名 船长/captain），只在第4章在场，想带全员安全归航；幽默稳重，第4章核对人数与天气，并商议带走哪些物资。所有角色只说亲历或已公开信息，不知他人私密想法及未来结果。每章比较至少两种立场，不要求全员发声。章节行动属于本仓库儿童互动原创改编，不等同原典情节。本改编让星期五从第1章即作为平等伙伴在场，不采用主仆叙事。

点名示例：“请让鲁滨逊说说”；“不要让鲁滨逊说话，请让星期五说说”；“请让星期五说说，再让鲁滨逊说说”只选文本顺序首个在场者。只说“鲁滨逊”或“我支持鲁滨逊”算玩家选择。开场、转场（含阻塞）、更正、安全管理优先旁白，未在场角色不可点名，旧记忆 active_roles 按章节重建。

## 验证

两份 roles Giztest 各有 4 个隔离 Workspace，后续角色先完成真实章节前置；检查 text/audio EOS、audio_bytes > 0，首响应保持文本 2s、音频 3s。保留 16 轮 relay、reload、更正、转场与 RealTime 用例；routing-cases.json 执行真实 JS 和 Starlark。离线门禁不证明实际音色正确，运行时 Voice ID 日志与试听仍需在线验收。
