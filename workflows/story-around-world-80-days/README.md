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

两引擎每轮使用一个讲述 LLM，输出有声书式连续多角色剧本；`voice_adapter.speaker_voices` 按段映射中文说话人名，`default_voice` 使用旁白 alias。

Voice 由 runtime profile 绑定。

| 角色 / 别名 | 出场章节 | 动机、行动与口吻 | Voice aliases |
| --- | --- | --- | --- |
| narrator 旁白 | 1–4 | 只述可见事实、选择后果与转场，不代演角色 | `flowcraft-story-around-world-80-days.storyteller` / `eino-story-around-world-80-days.storyteller` |
| `fogg` 福格 / 福格、福格先生、fogg | 1、2、3、4 | 我想守时又守信；清晰克制，第1章比较车船时刻，第2章换算当地时间，第3章核对改道风险，第4章计算归期。 | `flowcraft-story-around-world-80-days.fogg` / `eino-story-around-world-80-days.fogg` |
| `aouda` 艾娥达 / 艾娥达、aouda | 1、2、3、4 | 我想照顾旅伴；温柔细心，第1章核对随身物品，第2章提醒休息，第3章优先安排安全候船，第4章记录大家的互助。 | `flowcraft-story-around-world-80-days.aouda` / `eino-story-around-world-80-days.aouda` |
| `passepartout` 路路通 / 路路通、passepartout | 1、2、3、4 | 我想把旅程安排妥当；清爽利落，第1章搬行李并核对站台，第2章校准怀表，第3章寻找公开改道公告，第4章核对日期。 | `flowcraft-story-around-world-80-days.passepartout` / `eino-story-around-world-80-days.passepartout` |
| `fix` 费克斯 / 费克斯、fix | 2、4 | 我想把事情查清；沉稳谨慎，第2章在港口核对公开船期，第4章在归程车站承认误判并澄清记录；第3章不同行，不能知道船上的私事。 | `flowcraft-story-around-world-80-days.fix` / `eino-story-around-world-80-days.fix` |

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

角色只说亲历或公开信息，台词使用第一人称，与旁白叙述分段。角色名单按当前章节重建；孩子点名只增加本段该在场角色的台词，不改变章节或让未在场角色出现。

四章与人物相遇属于本仓库原创改编安排，应与原典、史实区分；每章比较至少两种立场，不让跨地点人物为凑数同时在场。

## 验收

- 保留双引擎 16 响应 relay、reload、更正、安全与转场回归。
- 完整响应要求 text/audio EOS、audio_bytes > 0，首字 6s、整段音频最多 180s；first_response 保持文本 2s、音频 3s。
- 离线门禁验证配置与路由；供应商音色权限、实际 Voice 日志、音质和在线时延需另行真实 E2E 与试听确认。

## 连续多角色讲述契约

普通回合（含开场、转场、选择结果）约 300–600 字、1–2 分钟语音，旁白与 2–4 个当前在场角色交替讲述；当前场景只有一位角色时不为凑数增员。每段恰好以一个配置中的 `【旁白】` 或 `【角色中文名】` 开头，标记后直接正文，禁止其他全角方括号标记。AudioDock 剥离标记并串行播放、预取下一段；孩子随时插话后承接新输入。

结尾由旁白给 2–3 个具体选项；选择完成逐字结尾、第四章/终局、安全、仅确认/更正/回忆等已有约束优先，不额外加问题；限定范围和安全回复可短于 300 字。章节、场景、知情边界与旧记忆恢复保持上文契约。音色槽位和 RuntimeProfile 绑定不变，中文标记名与上表角色对应。

Smoke 用连续开场、续讲及 realtime 检查完整 EOS、单流不叠音、零欠载、无残留标记和正文长度，first_response 保持 2s/3s。Quality 保留章节守门、选择结尾、安全逐字用语及原有更正/恢复场景；不再逐角色点名。Soak 保留 16 响应、relay 和 reload 结构，普通段落检查 300–600 字（特殊回复例外）。`routing-cases.json` 执行两引擎控制源码，验证状态与内容约束；已删除无意义的单人选声断言。离线通过不代表真实音色与音频时序已验收，需 GizClaw v0.18.12 部署后 E2E 和试听。
