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

两引擎每轮使用一个讲述 LLM，输出有声书式连续多角色剧本；`voice_adapter.speaker_voices` 按段映射中文说话人名，`default_voice` 使用旁白 alias。

Voice 由 runtime profile 绑定。

| 角色 / 别名 | 出场章节 | 动机、行动与口吻 | Voice aliases |
| --- | --- | --- | --- |
| narrator 旁白 | 1–4 | 只述可见事实、选择后果与转场，不代演角色 | `flowcraft-story-animal-kingdom.storyteller` / `eino-story-animal-kingdom.storyteller` |
| `explorer` 探险者 / 探险者、explorer | 1、2、3、4 | 我想找到河流变浅的原因；活泼认真，第1章记录水位，第2章比对足迹，第3章记录协作结果，第4章约定继续观察。 | `flowcraft-story-animal-kingdom.explorer` / `eino-story-animal-kingdom.explorer` |
| `animal-guide` 动物向导 / 动物向导、向导、animal guide、animal-guide | 1、2、3、4 | 我想保护栖息地；清晰理性，第1章提醒保持距离，第2章解释迁徙证据，第3章划出安静通道，第4章核对生态约定。 | `flowcraft-story-animal-kingdom.animal-guide` / `eino-story-animal-kingdom.animal-guide` |
| `elephant` 大象 / 大象、elephant | 2、3、4 | 我想带象群找到饮水处；憨厚稳重，第2章指出亲自走过的浅滩，第3章挪开倒枝保留通道，第4章承诺轮流饮水。 | `flowcraft-story-animal-kingdom.elephant` / `eino-story-animal-kingdom.elephant` |
| `owl` 猫头鹰 / 猫头鹰、owl | 2、3、4 | 我想保留安静的栖息树；和蔼缓慢，第2章报告夜里看见的鸟群方向，第3章建议不打扰巢穴，第4章约定夜间观察边界。 | `flowcraft-story-animal-kingdom.owl` / `eino-story-animal-kingdom.owl` |

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
