# Journey to the Center of the Earth (`story-journey-center-earth`) — 地心游记

Explore rocks, strata, and Earth science through a fictional underground journey.

## Story contract

- Premise: 在地下幻想旅程中认识岩石、地层与地球科学。
- Player: an active companion whose current choice and explicit correction override older History or Memory.
- Chapters: 第1章《岩层入口》 → 第2章《地下水路》 → 第3章《晶洞风暴》 → 第4章《地表回声》.
- Cast: 旁白 (`narrator`)、阿克塞尔 (`axel`)、黎登布洛克 (`lidenbrock`)、汉斯 (`hans`).
- State: current chapter, completed beats, location, active roles, player choices, explicit corrections, durable clues, and unresolved hooks survive the bounded reload.
- Safety and source boundary: distinguish fact, legend, and original fiction; keep peril child-safe and do not reproduce a published translation.
- Repetition boundary: do not repeat acknowledgements, openings, choices, questions, recaps, or moral summaries.

| Chapter | Entry condition | Goal | Allowed beats (at least two) | Transition condition | Ending condition |
| --- | --- | --- | --- | --- | --- |
| 1. 岩层入口 | first opening request | resolve this chapter's core tension | observe a concrete consequence; compare the two characters' responses | player resolves the current hook and requests chapter 2 | emit the chapter 2 heading once, followed directly by that chapter's opening scene |
| 2. 地下水路 | chapter 1 transition satisfied and player explicitly continues | resolve this chapter's core tension | observe a concrete consequence; compare the two characters' responses | player resolves the current hook and requests chapter 3 | emit the chapter 3 heading once, followed directly by that chapter's opening scene |
| 3. 晶洞风暴 | chapter 2 transition satisfied and player explicitly continues | resolve this chapter's core tension | observe a concrete consequence; compare the two characters' responses | player resolves the current hook and requests chapter 4 | emit the chapter 4 heading once, followed directly by that chapter's opening scene |
| 4. 地表回声 | chapter 3 transition satisfied and player explicitly continues | resolve this chapter's core tension | observe a concrete consequence; compare the two characters' responses | player confirms a durable choice and one remaining responsibility | remain in chapter 4; keep one post-ending responsibility |

## 双引擎音色与章节

Flowcraft 每轮选择一个 published 节点；Eino 保留一个 primary chat_model，由 Starlark 写入 selected_speaker，state_voices 绑定音色。两引擎保留 ASR 和原记忆链路。

| 角色（别名） | 章节 | 动机与行动 | 两引擎槽位 | Voice ID |
| --- | --- | --- | --- | --- |
| 旁白 (旁白/narrator) | 1,2,3,4 | 可见事实与转场，不代演 | `flowcraft-story-journey-center-earth.storyteller` / `eino-story-journey-center-earth.storyteller` | `volc-tenant:volc-cn-beijing:zh_female_shaoergushi_mars_bigtts` |
| 阿克塞尔 (阿克塞尔/axel) | 1,2,3,4 | 想探索也担心危险；少年直率，第1章观察岩层并提出先核对路线。 | `flowcraft-story-journey-center-earth.axel` / `eino-story-journey-center-earth.axel` | `volc-tenant:volc-cn-beijing:ICL_zh_male_qingshuangshaonian_tob` |
| 黎登布洛克 (黎登布洛克/lidenbrock) | 1,2,3,4 | 希望找到证据；幽默耐心，第1章解释岩层观察。 | `flowcraft-story-journey-center-earth.lidenbrock` / `eino-story-journey-center-earth.lidenbrock` | `volc-tenant:volc-cn-beijing:ICL_zh_male_youmodaye_tob` |
| 汉斯 (汉斯/hans) | 2,3,4 | 想让全队安全前进；憨厚少言，第2章辨认水流方向，第3章带大家退到稳固岩壁，第4章整理路线记录。 | `flowcraft-story-journey-center-earth.hans` / `eino-story-journey-center-earth.hans` | `volc-tenant:volc-cn-beijing:ICL_zh_male_hanhoudunshi_tob` |

角色表：narrator 旁白（别名 旁白/narrator），只在第1、2、3、4章在场，只述可见事实，不代演角色；axel 阿克塞尔（别名 阿克塞尔/axel），只在第1、2、3、4章在场，想探索也担心危险；少年直率，第1章观察岩层并提出先核对路线；lidenbrock 黎登布洛克（别名 黎登布洛克/lidenbrock），只在第1、2、3、4章在场，希望找到证据；幽默耐心，第1章解释岩层观察；hans 汉斯（别名 汉斯/hans），只在第2、3、4章在场，想让全队安全前进；憨厚少言，第2章辨认水流方向，第3章带大家退到稳固岩壁，第4章整理路线记录。所有角色只说亲历或已公开信息，不知他人私密想法及未来结果。每章比较至少两种立场，不要求全员发声。章节行动属于本仓库儿童互动原创改编，不等同原典情节。

点名示例：“请让阿克塞尔说说”；“不要让阿克塞尔说话，请让黎登布洛克说说”；“请让黎登布洛克说说，再让阿克塞尔说说”只选文本顺序首个在场者。只说“阿克塞尔”或“我支持阿克塞尔”算玩家选择。开场、转场（含阻塞）、更正、安全管理优先旁白，未在场角色不可点名，旧记忆 active_roles 按章节重建。

## 验证

两份 roles Giztest 各有 4 个隔离 Workspace，后续角色先完成真实章节前置；检查 text/audio EOS、audio_bytes > 0，首响应保持文本 2s、音频 3s。保留 16 轮 relay、reload、更正、转场与 RealTime 用例；routing-cases.json 执行真实 JS 和 Starlark。离线门禁不证明实际音色正确，运行时 Voice ID 日志与试听仍需在线验收。
