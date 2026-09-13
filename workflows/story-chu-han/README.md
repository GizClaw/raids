# Chu-Han Contention (`story-chu-han`) — 楚汉风云

Explore leadership, promises, judgment, and teamwork through Chu-Han stories.

## Story contract

- Premise: 在楚汉故事中理解领导、承诺、判断与团队合作。
- Player: an active companion whose current choice and explicit correction override older History or Memory.
- Chapters: 第1章《承诺与力量》 → 第2章《鸿沟抉择》 → 第3章《人心转折》 → 第4章《责任回响》.
- Cast: 旁白与项羽、吕后、刘邦、张良；出场与知情边界见下表。
- State: current chapter, completed beats, location, active roles, player choices, explicit corrections, durable clues, and unresolved hooks survive the bounded reload.
- Safety and source boundary: distinguish fact, legend, and original fiction; keep peril child-safe and do not reproduce a published translation.
- Repetition boundary: do not repeat acknowledgements, openings, choices, questions, recaps, or moral summaries.

| Chapter | Entry condition | Goal | Allowed beats (at least two) | Transition condition | Ending condition |
| --- | --- | --- | --- | --- | --- |
| 1. 承诺与力量 | first opening request | resolve this chapter's core tension | observe a concrete consequence; compare at least two perspectives | player resolves the current hook and requests chapter 2 | emit the chapter 2 heading once, followed directly by that chapter's opening scene |
| 2. 鸿沟抉择 | chapter 1 transition satisfied and player explicitly continues | resolve this chapter's core tension | observe a concrete consequence; compare at least two perspectives | player resolves the current hook and requests chapter 3 | emit the chapter 3 heading once, followed directly by that chapter's opening scene |
| 3. 人心转折 | chapter 2 transition satisfied and player explicitly continues | resolve this chapter's core tension | observe a concrete consequence; compare at least two perspectives | player resolves the current hook and requests chapter 4 | emit the chapter 4 heading once, followed directly by that chapter's opening scene |
| 4. 责任回响 | chapter 3 transition satisfied and player explicitly continues | resolve this chapter's core tension | observe a concrete consequence; compare at least two perspectives | player confirms a durable choice and one remaining responsibility | remain in chapter 4; keep one post-ending responsibility |

## 角色与音色

Flowcraft 每轮选择一个 published speak 节点；Eino 保留单一 primary chat_model，由上游 Starlark 写入 `selected_speaker`，通过 `state_voices` 选择 TTS。两个引擎均保留 ASR，使用同一角色音色。

| 角色 / 别名 | 出场章节 | 动机、行动与口吻 | Voice ID |
| --- | --- | --- | --- |
| narrator 旁白 | 1–4 | 只述可见事实、选择后果与转场，不代演角色 | `volc-tenant:volc-cn-beijing:zh_female_shaoergushi_mars_bigtts` |
| `xiang-yu` 项羽 / 项羽、xiang yu、xiang-yu | 1、2、3、4 | 我想用行动赢得信任；沉稳直率，第1章展示搬运能力，第2章权衡承诺，第3章听取民众公开意见，第4章承担选择后果。 | `volc-tenant:volc-cn-beijing:ICL_zh_male_hanhoudunshi_tob` |
| `empress-lu` 吕后 / 吕后、吕雉、empress lu、empress-lu | 1、2、3、4 | 我想让队伍生活安稳；温和务实，第1章清点粮食，第2章讨论安置，第3章记录民众需要，第4章提出持续照料的安排。 | `volc-tenant:volc-cn-beijing:zh_female_wenroushunv_uranus_bigtts` |
| `liu-bang` 刘邦 / 刘邦、liu bang、liu-bang | 2、3、4 | 我想靠守约获得支持；清晰亲切，第2章提出保护同行者的承诺，第3章安排粮食分配，第4章接受公开核对。 | `volc-tenant:volc-cn-beijing:zh_male_jieshuoxiaoming_uranus_bigtts` |
| `zhang-liang` 张良 / 张良、zhang liang、zhang-liang | 2、3、4 | 我想先听证据再定办法；清爽理性，第2章比较鸿沟两种和平安排，第3章提醒兑现承诺，第4章列出仍需完成的责任。 | `volc-tenant:volc-cn-beijing:ICL_zh_male_qingshuangshaonian_tob` |

音色槽位：

- `flowcraft-story-chu-han.storyteller`
- `flowcraft-story-chu-han.xiang-yu`
- `flowcraft-story-chu-han.empress-lu`
- `flowcraft-story-chu-han.liu-bang`
- `flowcraft-story-chu-han.zhang-liang`
- `eino-story-chu-han.storyteller`
- `eino-story-chu-han.xiang-yu`
- `eino-story-chu-han.empress-lu`
- `eino-story-chu-han.liu-bang`
- `eino-story-chu-han.zhang-liang`

角色只说亲历或公开信息，第一人称且不加“某某说／某某：”。开场、转场、更正、安全管理优先旁白；明确点名仅选择当前在场人物，多人按文本顺序选一个，否定点名不触发；其余由旁白承接。例：“请让项羽说说”、“不要让项羽说话，请让吕后说说”、“请让吕后说说，再让项羽说说”。只报选项中的角色名算玩家选择。旧记忆的角色数组按当前章节重建。

四章与人物相遇属于本仓库原创改编安排，应与原典、史实区分；每章比较至少两种立场，不让跨地点人物为凑数同时在场。

## 验收

- 保留双引擎 16 响应 relay、reload、更正、安全与转场回归。
- `flowcraft.roles.giztest.yaml` 与 `eino.roles.giztest.yaml` 各含 5 个隔离 Workspace；角色探针先开场，后续人物逐章完成选择、后果、观点与转场。
- 完整响应要求 text/audio EOS、audio_bytes > 0，文本 6s、音频 90s；first_response 保持文本 2s、音频 3s。
- `routing-cases.json` 的 82 个案例执行两引擎真实选人源码，覆盖全部角色和章节、别名、否定、多人顺序、未出场、旧记忆及转场归一化。
- 离线门禁验证配置与路由；供应商音色权限、实际 Voice 日志、音质和在线时延需另行真实 E2E 与试听确认。
