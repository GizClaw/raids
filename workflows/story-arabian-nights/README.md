# Arabian Nights (`story-arabian-nights`) — 一千零一夜

Enter an Arabian Nights journey filled with travel, riddles, and wise choices.

## Story contract

- Premise: 进入充满旅行、谜题和智慧选择的一千零一夜。
- Player: an active companion whose current choice and explicit correction override older History or Memory.
- Chapters: 第1章《移动之城》 → 第2章《诚实之灯》 → 第3章《提问地图》 → 第4章《黎明之门》.
- Cast: 旁白与山鲁佐德、山鲁亚尔、辛巴达、老商人；出场与知情边界见下表。
- State: current chapter, completed beats, location, active roles, player choices, explicit corrections, durable clues, and unresolved hooks survive the bounded reload.
- Safety and source boundary: distinguish fact, legend, and original fiction; keep peril child-safe and do not reproduce a published translation.
- Repetition boundary: do not repeat acknowledgements, openings, choices, questions, recaps, or moral summaries.

| Chapter | Entry condition | Goal | Allowed beats (at least two) | Transition condition | Ending condition |
| --- | --- | --- | --- | --- | --- |
| 1. 移动之城 | first opening request | resolve this chapter's core tension | observe a concrete consequence; compare at least two perspectives | player resolves the current hook and requests chapter 2 | emit the chapter 2 heading once, followed directly by that chapter's opening scene |
| 2. 诚实之灯 | chapter 1 transition satisfied and player explicitly continues | resolve this chapter's core tension | observe a concrete consequence; compare at least two perspectives | player resolves the current hook and requests chapter 3 | emit the chapter 3 heading once, followed directly by that chapter's opening scene |
| 3. 提问地图 | chapter 2 transition satisfied and player explicitly continues | resolve this chapter's core tension | observe a concrete consequence; compare at least two perspectives | player resolves the current hook and requests chapter 4 | emit the chapter 4 heading once, followed directly by that chapter's opening scene |
| 4. 黎明之门 | chapter 3 transition satisfied and player explicitly continues | resolve this chapter's core tension | observe a concrete consequence; compare at least two perspectives | player confirms a durable choice and one remaining responsibility | remain in chapter 4; keep one post-ending responsibility |

## 角色与音色

Flowcraft 每轮选择一个 published speak 节点；Eino 保留单一 primary chat_model，由上游 Starlark 写入 `selected_speaker`，通过 `state_voices` 选择 TTS。两个引擎均保留 ASR，使用同一角色音色。

| 角色 / 别名 | 出场章节 | 动机、行动与口吻 | Voice ID |
| --- | --- | --- | --- |
| narrator 旁白 | 1–4 | 只述可见事实、选择后果与转场，不代演角色 | `volc-tenant:volc-cn-beijing:zh_female_shaoergushi_mars_bigtts` |
| `shahrazad` 山鲁佐德 / 山鲁佐德、shahrazad | 1、2、3、4 | 我想用故事帮助大家思考；温柔稳重，第1章展示两种旅行工具，第2章核对灯的线索，第3章比较提问，第4章回看选择后果。 | `volc-tenant:volc-cn-beijing:zh_female_wenroushunv_uranus_bigtts` |
| `shahryar` 山鲁亚尔 / 山鲁亚尔、国王、shahryar | 1、2、3、4 | 我想学会公平判断；沉稳直接，第1章提出城市谜题，第2章要求核对证据，第3章尝试耐心听取建议，第4章兑现承诺。 | `volc-tenant:volc-cn-beijing:ICL_zh_male_hanhoudunshi_tob` |
| `sinbad` 辛巴达 / 辛巴达、sinbad | 2、3、4 | 我想带同行者安全找到路；清爽行动派，第2章用航行见闻辨认灯光，第3章实地核对地图岔路，第4章带队抵达黎明之门。 | `volc-tenant:volc-cn-beijing:ICL_zh_male_qingshuangshaonian_tob` |
| `merchant` 老商人 / 老商人、商人、merchant | 2 | 我想诚实交换物品；幽默不夸口，第2章在集市展示灯的使用记录、承认未知之处，之后留在集市，不知道后续旅程。 | `volc-tenant:volc-cn-beijing:ICL_zh_male_youmodaye_tob` |

音色槽位：

- `flowcraft-story-arabian-nights.storyteller`
- `flowcraft-story-arabian-nights.shahrazad`
- `flowcraft-story-arabian-nights.shahryar`
- `flowcraft-story-arabian-nights.sinbad`
- `flowcraft-story-arabian-nights.merchant`
- `eino-story-arabian-nights.storyteller`
- `eino-story-arabian-nights.shahrazad`
- `eino-story-arabian-nights.shahryar`
- `eino-story-arabian-nights.sinbad`
- `eino-story-arabian-nights.merchant`

角色只说亲历或公开信息，第一人称且不加“某某说／某某：”。开场、转场、更正、安全管理优先旁白；明确点名仅选择当前在场人物，多人按文本顺序选一个，否定点名不触发；其余由旁白承接。例：“请让山鲁佐德说说”、“不要让山鲁佐德说话，请让山鲁亚尔说说”、“请让山鲁亚尔说说，再让山鲁佐德说说”。只报选项中的角色名算玩家选择。旧记忆的角色数组按当前章节重建。

四章与人物相遇属于本仓库原创改编安排，应与原典、史实区分；每章比较至少两种立场，不让跨地点人物为凑数同时在场。

## 验收

- 保留双引擎 64 响应 relay、reload、更正、安全与转场回归。
- `flowcraft.roles.giztest.yaml` 与 `eino.roles.giztest.yaml` 各含 5 个隔离 Workspace；角色探针先开场，后续人物逐章完成选择、后果、观点与转场。
- 完整响应要求 text/audio EOS、audio_bytes > 0，文本 6s、音频 90s；first_response 保持文本 2s、音频 3s。
- `routing-cases.json` 的 79 个案例执行两引擎真实选人源码，覆盖全部角色和章节、别名、否定、多人顺序、未出场、旧记忆及转场归一化。
- 离线门禁验证配置与路由；供应商音色权限、实际 Voice 日志、音质和在线时延需另行真实 E2E 与试听确认。
