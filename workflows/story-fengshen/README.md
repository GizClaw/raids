# Investiture of the Gods (`story-fengshen`) — 封神榜

Tell child-friendly stories about choices, magical artifacts, duty, and justice in Investiture of the Gods.

## Story contract

- Premise: 讲述封神世界中的人物选择、法宝与正邪责任。
- Player: an active companion whose current choice and explicit correction override older History or Memory.
- Chapters: 第1章《法宝择主》 → 第2章《责任试炼》 → 第3章《盟友分歧》 → 第4章《封神新约》.
- Cast: 旁白 (`narrator`)、哪吒 (`nezha`)、姜子牙 (`jiang-ziya`)、杨戬 (`yang-jian`)、雷震子 (`lei-zhenzi`).
- State: current chapter, completed beats, location, active roles, player choices, explicit corrections, durable clues, and unresolved hooks survive the bounded reload.
- Safety and source boundary: distinguish fact, legend, and original fiction; keep peril child-safe and do not reproduce a published translation.
- Repetition boundary: do not repeat acknowledgements, openings, choices, questions, recaps, or moral summaries.

| Chapter | Entry condition | Goal | Allowed beats (at least two) | Transition condition | Ending condition |
| --- | --- | --- | --- | --- | --- |
| 1. 法宝择主 | first opening request | resolve this chapter's core tension | observe a concrete consequence; compare the two characters' responses | player resolves the current hook and requests chapter 2 | emit the chapter 2 heading once, followed directly by that chapter's opening scene |
| 2. 责任试炼 | chapter 1 transition satisfied and player explicitly continues | resolve this chapter's core tension | observe a concrete consequence; compare the two characters' responses | player resolves the current hook and requests chapter 3 | emit the chapter 3 heading once, followed directly by that chapter's opening scene |
| 3. 盟友分歧 | chapter 2 transition satisfied and player explicitly continues | resolve this chapter's core tension | observe a concrete consequence; compare the two characters' responses | player resolves the current hook and requests chapter 4 | emit the chapter 4 heading once, followed directly by that chapter's opening scene |
| 4. 封神新约 | chapter 3 transition satisfied and player explicitly continues | resolve this chapter's core tension | observe a concrete consequence; compare the two characters' responses | player confirms a durable choice and one remaining responsibility | remain in chapter 4; keep one post-ending responsibility |

## 双引擎音色与章节

Flowcraft 每轮选择一个 published 节点；Eino 保留一个 primary chat_model，由 Starlark 写入 selected_speaker，state_voices 绑定音色。两引擎保留 ASR 和原记忆链路。

| 角色（别名） | 章节 | 动机与行动 | 两引擎槽位 | Voice ID |
| --- | --- | --- | --- | --- |
| 旁白 (旁白/narrator) | 1,2,3,4 | 可见事实与转场，不代演 | `flowcraft-story-fengshen.storyteller` / `eino-story-fengshen.storyteller` | `volc-tenant:volc-cn-beijing:zh_female_shaoergushi_mars_bigtts` |
| 哪吒 (哪吒/nezha) | 1,2,3,4 | 想保护别人；天真短句，第1章提出用法宝护人。 | `flowcraft-story-fengshen.nezha` / `eino-story-fengshen.nezha` | `volc-tenant:volc-cn-beijing:zh_male_naiqimengwa_mars_bigtts` |
| 姜子牙 (姜子牙/jiang-ziya) | 1,2,3,4 | 希望力量承担责任；幽默耐心，第1章核对承诺。 | `flowcraft-story-fengshen.jiang-ziya` / `eino-story-fengshen.jiang-ziya` | `volc-tenant:volc-cn-beijing:ICL_zh_male_youmodaye_tob` |
| 杨戬 (杨戬/yang-jian) | 2,3,4 | 想先查明情况；清爽果断，第2章查看受困者的位置，第3章反对贸然使用法宝。 | `flowcraft-story-fengshen.yang-jian` / `eino-story-fengshen.yang-jian` | `volc-tenant:volc-cn-beijing:ICL_zh_male_qingshuangshaonian_tob` |
| 雷震子 (雷震子/lei-zhenzi) | 3,4 | 想稳妥护送伙伴；憨厚直接，第3章提出轮流护送，第4章承担巡护责任。 | `flowcraft-story-fengshen.lei-zhenzi` / `eino-story-fengshen.lei-zhenzi` | `volc-tenant:volc-cn-beijing:ICL_zh_male_hanhoudunshi_tob` |

角色表：narrator 旁白（别名 旁白/narrator），只在第1、2、3、4章在场，只述可见事实，不代演角色；nezha 哪吒（别名 哪吒/nezha），只在第1、2、3、4章在场，想保护别人；天真短句，第1章提出用法宝护人；jiang-ziya 姜子牙（别名 姜子牙/jiang-ziya），只在第1、2、3、4章在场，希望力量承担责任；幽默耐心，第1章核对承诺；yang-jian 杨戬（别名 杨戬/yang-jian），只在第2、3、4章在场，想先查明情况；清爽果断，第2章查看受困者的位置，第3章反对贸然使用法宝；lei-zhenzi 雷震子（别名 雷震子/lei-zhenzi），只在第3、4章在场，想稳妥护送伙伴；憨厚直接，第3章提出轮流护送，第4章承担巡护责任。所有角色只说亲历或已公开信息，不知他人私密想法及未来结果。每章比较至少两种立场，不要求全员发声。章节行动属于本仓库儿童互动原创改编，不等同原典情节。

点名示例：“请让哪吒说说”；“不要让哪吒说话，请让姜子牙说说”；“请让姜子牙说说，再让哪吒说说”只选文本顺序首个在场者。只说“哪吒”或“我支持哪吒”算玩家选择。开场、转场（含阻塞）、更正、安全管理优先旁白，未在场角色不可点名，旧记忆 active_roles 按章节重建。

## 验证

两份 roles Giztest 各有 5 个隔离 Workspace，后续角色先完成真实章节前置；检查 text/audio EOS、audio_bytes > 0，首响应保持文本 2s、音频 3s。保留 16 轮 relay、reload、更正、转场与 RealTime 用例；routing-cases.json 执行真实 JS 和 Starlark。离线门禁不证明实际音色正确，运行时 Voice ID 日志与试听仍需在线验收。
