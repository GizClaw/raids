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

两引擎每轮使用一个讲述 LLM，按 `speaker_voices` 连续切换段落音色，保留 ASR 和既有音色绑定。

Voice 由 runtime profile 绑定。

| 角色（别名） | 章节 | 动机与行动 | 两引擎槽位 |
| --- | --- | --- | --- |
| 旁白 (旁白/narrator) | 1,2,3,4 | 可见事实与转场，不代演 | `flowcraft-story-journey-center-earth.storyteller` / `eino-story-journey-center-earth.storyteller` |
| 阿克塞尔 (阿克塞尔/axel) | 1,2,3,4 | 想探索也担心危险；少年直率，第1章观察岩层并提出先核对路线。 | `flowcraft-story-journey-center-earth.axel` / `eino-story-journey-center-earth.axel` |
| 黎登布洛克 (黎登布洛克/lidenbrock) | 1,2,3,4 | 希望找到证据；幽默耐心，第1章解释岩层观察。 | `flowcraft-story-journey-center-earth.lidenbrock` / `eino-story-journey-center-earth.lidenbrock` |
| 汉斯 (汉斯/hans) | 2,3,4 | 想让全队安全前进；憨厚少言，第2章辨认水流方向，第3章带大家退到稳固岩壁，第4章整理路线记录。 | `flowcraft-story-journey-center-earth.hans` / `eino-story-journey-center-earth.hans` |

角色表：narrator 旁白（别名 旁白/narrator），只在第1、2、3、4章在场，只述可见事实，不代演角色；axel 阿克塞尔（别名 阿克塞尔/axel），只在第1、2、3、4章在场，想探索也担心危险；少年直率，第1章观察岩层并提出先核对路线；lidenbrock 黎登布洛克（别名 黎登布洛克/lidenbrock），只在第1、2、3、4章在场，希望找到证据；幽默耐心，第1章解释岩层观察；hans 汉斯（别名 汉斯/hans），只在第2、3、4章在场，想让全队安全前进；憨厚少言，第2章辨认水流方向，第3章带大家退到稳固岩壁，第4章整理路线记录。所有角色只说亲历或已公开信息，不知他人私密想法及未来结果。每章比较至少两种立场，不要求全员发声。章节行动属于本仓库儿童互动原创改编，不等同原典情节。

点名示例：“请让阿克塞尔说说”；“不要让阿克塞尔说话，请让黎登布洛克说说”；“请让黎登布洛克说说，再让阿克塞尔说说”只选文本顺序首个在场者。只说“阿克塞尔”或“我支持阿克塞尔”算玩家选择。开场、转场（含阻塞）、更正、安全管理优先旁白，未在场角色不可点名，旧记忆 active_roles 按章节重建。

## 验证


## 连续多角色讲述契约

普通回合（含开场、转场、选择结果）约 300–600 字、1–2 分钟语音，旁白与 2–4 个当前在场角色交替讲述；当前场景只有一位角色时不为凑数增员。每段恰好以一个配置中的 `【旁白】` 或 `【角色中文名】` 开头，标记后直接正文，禁止其他全角方括号标记。AudioDock 剥离标记并串行播放、预取下一段；孩子随时插话后承接新输入。

结尾由旁白给 2–3 个具体选项；选择完成逐字结尾、第四章/终局、安全、仅确认/更正/回忆等已有约束优先，不额外加问题；限定范围和安全回复可短于 300 字。章节、场景、知情边界与旧记忆恢复保持上文契约。音色槽位和 RuntimeProfile 绑定不变，中文标记名与上表角色对应。

Smoke 用连续开场、续讲及 realtime 检查完整 EOS、单流不叠音、零欠载、无残留标记和正文长度，first_response 保持 2s/3s。Quality 保留章节守门、选择结尾、安全逐字用语及原有更正/恢复场景；不再逐角色点名。Soak 保留 16 响应、relay 和 reload 结构，普通段落检查 300–600 字（特殊回复例外）。`routing-cases.json` 执行两引擎控制源码，验证状态与内容约束；已删除无意义的单人选声断言。离线通过不代表真实音色与音频时序已验收，需 GizClaw v0.18.12 部署后 E2E 和试听。
