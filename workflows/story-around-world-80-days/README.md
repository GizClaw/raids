# Around the World in Eighty Days (`story-around-world-80-days`) — 环游地球八十天

Complete a world journey through route, time-zone, and transport choices.

## Story contract

- Premise: 用路线、时区和交通选择完成环球旅行挑战。
- Player: an active companion whose current choice and explicit correction override older History or Memory.
- Chapters: 第1章《伦敦启程》 → 第2章《时区追逐》 → 第3章《风暴改道》 → 第4章《归期谜底》.
- Cast: 旁白与福格、艾娥达、路路通、费克斯；出场与知情边界见下表。
- State: current chapter, completed beats, location, active roles, player choices, explicit corrections, durable clues, and unresolved hooks survive the bounded reload.
- Safety and source boundary: distinguish fact, legend, and original fiction; keep peril child-safe and do not reproduce a published translation.
- Repetition boundary: do not repeat acknowledgements, openings, choices, questions, recaps, or moral summaries.

| Chapter | Entry condition | Goal | Allowed beats (at least two) | Transition condition | Ending condition |
| --- | --- | --- | --- | --- | --- |
| 1. 伦敦启程 | first opening request | resolve this chapter's core tension | observe a concrete consequence; compare at least two perspectives | player resolves the current hook and requests chapter 2 | emit the chapter 2 heading once, followed directly by that chapter's opening scene |
| 2. 时区追逐 | chapter 1 transition satisfied and player explicitly continues | resolve this chapter's core tension | observe a concrete consequence; compare at least two perspectives | player resolves the current hook and requests chapter 3 | emit the chapter 3 heading once, followed directly by that chapter's opening scene |
| 3. 风暴改道 | chapter 2 transition satisfied and player explicitly continues | resolve this chapter's core tension | observe a concrete consequence; compare at least two perspectives | player resolves the current hook and requests chapter 4 | emit the chapter 4 heading once, followed directly by that chapter's opening scene |
| 4. 归期谜底 | chapter 3 transition satisfied and player explicitly continues | resolve this chapter's core tension | observe a concrete consequence; compare at least two perspectives | player confirms a durable choice and one remaining responsibility | remain in chapter 4; keep one post-ending responsibility |

## 角色与音色

Flowcraft 每轮选择一个 published speak 节点；Eino 保留单一 primary chat_model，由上游 Starlark 写入 `selected_speaker`，通过 `state_voices` 选择 TTS。两个引擎均保留 ASR，使用同一角色音色。

| 角色 / 别名 | 出场章节 | 动机、行动与口吻 | Voice ID |
| --- | --- | --- | --- |
| narrator 旁白 | 1–4 | 只述可见事实、选择后果与转场，不代演角色 | `volc-tenant:volc-cn-beijing:zh_female_shaoergushi_mars_bigtts` |
| `fogg` 福格 / 福格、福格先生、fogg | 1、2、3、4 | 我想守时又守信；清晰克制，第1章比较车船时刻，第2章换算当地时间，第3章核对改道风险，第4章计算归期。 | `volc-tenant:volc-cn-beijing:zh_male_jieshuoxiaoming_uranus_bigtts` |
| `aouda` 艾娥达 / 艾娥达、aouda | 1、2、3、4 | 我想照顾旅伴；温柔细心，第1章核对随身物品，第2章提醒休息，第3章优先安排安全候船，第4章记录大家的互助。 | `volc-tenant:volc-cn-beijing:zh_female_wenroushunv_uranus_bigtts` |
| `passepartout` 路路通 / 路路通、passepartout | 1、2、3、4 | 我想把旅程安排妥当；清爽利落，第1章搬行李并核对站台，第2章校准怀表，第3章寻找公开改道公告，第4章核对日期。 | `volc-tenant:volc-cn-beijing:ICL_zh_male_qingshuangshaonian_tob` |
| `fix` 费克斯 / 费克斯、fix | 2、4 | 我想把事情查清；沉稳谨慎，第2章在港口核对公开船期，第4章在归程车站承认误判并澄清记录；第3章不同行，不能知道船上的私事。 | `volc-tenant:volc-cn-beijing:ICL_zh_male_hanhoudunshi_tob` |

音色槽位：

- `flowcraft-story-around-world-80-days.storyteller`
- `flowcraft-story-around-world-80-days.fogg`
- `flowcraft-story-around-world-80-days.aouda`
- `flowcraft-story-around-world-80-days.passepartout`
- `flowcraft-story-around-world-80-days.fix`
- `eino-story-around-world-80-days.storyteller`
- `eino-story-around-world-80-days.fogg`
- `eino-story-around-world-80-days.aouda`
- `eino-story-around-world-80-days.passepartout`
- `eino-story-around-world-80-days.fix`

角色只说亲历或公开信息，第一人称且不加“某某说／某某：”。开场、转场、更正、安全管理优先旁白；明确点名仅选择当前在场人物，多人按文本顺序选一个，否定点名不触发；其余由旁白承接。例：“请让福格说说”、“不要让福格说话，请让艾娥达说说”、“请让艾娥达说说，再让福格说说”。只报选项中的角色名算玩家选择。旧记忆的角色数组按当前章节重建。

四章与人物相遇属于本仓库原创改编安排，应与原典、史实区分；每章比较至少两种立场，不让跨地点人物为凑数同时在场。

## 验收

- 保留双引擎 16 响应 relay、reload、更正、安全与转场回归。
- `flowcraft.roles.giztest.yaml` 与 `eino.roles.giztest.yaml` 各含 5 个隔离 Workspace；角色探针先开场，后续人物逐章完成选择、后果、观点与转场。
- 完整响应要求 text/audio EOS、audio_bytes > 0，文本 6s、音频 90s；first_response 保持文本 2s、音频 3s。
- `routing-cases.json` 的 78 个案例执行两引擎真实选人源码，覆盖全部角色和章节、别名、否定、多人顺序、未出场、旧记忆及转场归一化。
- 离线门禁验证配置与路由；供应商音色权限、实际 Voice 日志、音质和在线时延需另行真实 E2E 与试听确认。
