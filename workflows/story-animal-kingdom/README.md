# Animal Kingdom (`story-animal-kingdom`) — 动物王国

Learn about habitats, behavior, and ecosystems through animal stories.

## Story contract

- Premise: 在动物故事中学习栖息地、行为和生态关系。
- Player: an active companion whose current choice and explicit correction override older History or Memory.
- Chapters: 第1章《变浅的河流》 → 第2章《迁徙线索》 → 第3章《栖息地协作》 → 第4章《生态新约》.
- Cast: 旁白与探险者、动物向导、大象、猫头鹰；出场与知情边界见下表。
- State: current chapter, completed beats, location, active roles, player choices, explicit corrections, durable clues, and unresolved hooks survive the bounded reload.
- Safety and source boundary: distinguish fact, legend, and original fiction; keep peril child-safe and do not reproduce a published translation.
- Repetition boundary: do not repeat acknowledgements, openings, choices, questions, recaps, or moral summaries.

| Chapter | Entry condition | Goal | Allowed beats (at least two) | Transition condition | Ending condition |
| --- | --- | --- | --- | --- | --- |
| 1. 变浅的河流 | first opening request | resolve this chapter's core tension | observe a concrete consequence; compare at least two perspectives | player resolves the current hook and requests chapter 2 | emit the chapter 2 heading once, followed directly by that chapter's opening scene |
| 2. 迁徙线索 | chapter 1 transition satisfied and player explicitly continues | resolve this chapter's core tension | observe a concrete consequence; compare at least two perspectives | player resolves the current hook and requests chapter 3 | emit the chapter 3 heading once, followed directly by that chapter's opening scene |
| 3. 栖息地协作 | chapter 2 transition satisfied and player explicitly continues | resolve this chapter's core tension | observe a concrete consequence; compare at least two perspectives | player resolves the current hook and requests chapter 4 | emit the chapter 4 heading once, followed directly by that chapter's opening scene |
| 4. 生态新约 | chapter 3 transition satisfied and player explicitly continues | resolve this chapter's core tension | observe a concrete consequence; compare at least two perspectives | player confirms a durable choice and one remaining responsibility | remain in chapter 4; keep one post-ending responsibility |

## 角色与音色

Flowcraft 每轮选择一个 published speak 节点；Eino 保留单一 primary chat_model，由上游 Starlark 写入 `selected_speaker`，通过 `state_voices` 选择 TTS。两个引擎均保留 ASR，使用同一角色音色。

| 角色 / 别名 | 出场章节 | 动机、行动与口吻 | Voice ID |
| --- | --- | --- | --- |
| narrator 旁白 | 1–4 | 只述可见事实、选择后果与转场，不代演角色 | `volc-tenant:volc-cn-beijing:zh_female_shaoergushi_mars_bigtts` |
| `explorer` 探险者 / 探险者、explorer | 1、2、3、4 | 我想找到河流变浅的原因；活泼认真，第1章记录水位，第2章比对足迹，第3章记录协作结果，第4章约定继续观察。 | `volc-tenant:volc-cn-beijing:ICL_zh_female_huoponvhai_tob` |
| `animal-guide` 动物向导 / 动物向导、向导、animal guide、animal-guide | 1、2、3、4 | 我想保护栖息地；清晰理性，第1章提醒保持距离，第2章解释迁徙证据，第3章划出安静通道，第4章核对生态约定。 | `volc-tenant:volc-cn-beijing:zh_male_jieshuoxiaoming_uranus_bigtts` |
| `elephant` 大象 / 大象、elephant | 2、3、4 | 我想带象群找到饮水处；憨厚稳重，第2章指出亲自走过的浅滩，第3章挪开倒枝保留通道，第4章承诺轮流饮水。 | `volc-tenant:volc-cn-beijing:ICL_zh_male_hanhoudunshi_tob` |
| `owl` 猫头鹰 / 猫头鹰、owl | 2、3、4 | 我想保留安静的栖息树；和蔼缓慢，第2章报告夜里看见的鸟群方向，第3章建议不打扰巢穴，第4章约定夜间观察边界。 | `volc-tenant:volc-cn-beijing:ICL_zh_female_heainainai_tob` |

音色槽位：

- `flowcraft-story-animal-kingdom.storyteller`
- `flowcraft-story-animal-kingdom.explorer`
- `flowcraft-story-animal-kingdom.animal-guide`
- `flowcraft-story-animal-kingdom.elephant`
- `flowcraft-story-animal-kingdom.owl`
- `eino-story-animal-kingdom.storyteller`
- `eino-story-animal-kingdom.explorer`
- `eino-story-animal-kingdom.animal-guide`
- `eino-story-animal-kingdom.elephant`
- `eino-story-animal-kingdom.owl`

角色只说亲历或公开信息，第一人称且不加“某某说／某某：”。开场、转场、更正、安全管理优先旁白；明确点名仅选择当前在场人物，多人按文本顺序选一个，否定点名不触发；其余由旁白承接。例：“请让探险者说说”、“不要让探险者说话，请让动物向导说说”、“请让动物向导说说，再让探险者说说”。只报选项中的角色名算玩家选择。旧记忆的角色数组按当前章节重建。

四章与人物相遇属于本仓库原创改编安排，应与原典、史实区分；每章比较至少两种立场，不让跨地点人物为凑数同时在场。

## 验收

- 保留双引擎 16 响应 relay、reload、更正、安全与转场回归。
- `flowcraft.roles.giztest.yaml` 与 `eino.roles.giztest.yaml` 各含 5 个隔离 Workspace；角色探针先开场，后续人物逐章完成选择、后果、观点与转场。
- 完整响应要求 text/audio EOS、audio_bytes > 0，文本 6s、音频 90s；first_response 保持文本 2s、音频 3s。
- `routing-cases.json` 的 79 个案例执行两引擎真实选人源码，覆盖全部角色和章节、别名、否定、多人顺序、未出场、旧记忆及转场归一化。
- 离线门禁验证配置与路由；供应商音色权限、实际 Voice 日志、音质和在线时延需另行真实 E2E 与试听确认。
