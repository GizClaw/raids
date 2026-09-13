# Legends of the Three Kingdoms (`story-three-kingdoms`) — 三国乱世

Explore choices, cooperation, and responsibility through Three Kingdoms characters and strategy.

## Story contract

- Premise: 从三国人物与谋略中体验选择、合作和责任。
- Player: an active companion whose current choice and explicit correction override older History or Memory.
- Chapters: 第1章《营帐军情》 → 第2章《百姓与追击》 → 第3章《联盟试探》 → 第4章《责任定策》.
- Cast: 旁白 (`narrator`), 刘备 (`liu-bei`), 诸葛亮 (`zhuge-liang`), 关羽 (`guan-yu`), 张飞 (`zhang-fei`).
- State: current chapter, completed beats, location, active roles, player choices, explicit corrections, durable clues, and unresolved hooks survive the bounded reload.
- Safety and source boundary: distinguish fact, legend, and original fiction; keep peril child-safe and do not reproduce a published translation.
- Repetition boundary: do not repeat acknowledgements, openings, choices, questions, recaps, or moral summaries.

| Chapter | Entry condition | Goal | Allowed beats (at least two) | Transition condition | Ending condition |
| --- | --- | --- | --- | --- | --- |
| 1. 营帐军情 | first opening request | resolve this chapter's core tension | observe a concrete consequence; compare at least two characters' responses | player resolves the current hook and requests chapter 2 | emit the chapter 2 heading once, followed directly by that chapter's opening scene |
| 2. 百姓与追击 | chapter 1 transition satisfied and player explicitly continues | resolve this chapter's core tension | observe a concrete consequence; compare at least two characters' responses | player resolves the current hook and requests chapter 3 | emit the chapter 3 heading once, followed directly by that chapter's opening scene |
| 3. 联盟试探 | chapter 2 transition satisfied and player explicitly continues | resolve this chapter's core tension | observe a concrete consequence; compare at least two characters' responses | player resolves the current hook and requests chapter 4 | emit the chapter 4 heading once, followed directly by that chapter's opening scene |
| 4. 责任定策 | chapter 3 transition satisfied and player explicitly continues | resolve this chapter's core tension | observe a concrete consequence; compare at least two characters' responses | player confirms a durable choice and one remaining responsibility | remain in chapter 4; keep one post-ending responsibility |

## Implementations and Voice roles

Flowcraft 每轮选一个 published speak 节点；Eino 保留单一 primary chat_model，通过 Starlark selected_speaker 和 state_voices 选择音色，ASR 保留。两引擎角色与 Voice 一一对应，旁白槽位沿用 storyteller。

| 角色 / 别名 | 出场章 | 动机与具体行动 | 音色槽位（两引擎） | Voice resource_id |
| --- | --- | --- | --- | --- |
| 旁白 / 旁白, narrator | 1,2,3,4 | 只述可见事实、管理和转场，不代演 | `flowcraft-story-three-kingdoms.storyteller` / `eino-story-three-kingdoms.storyteller` | `volc-tenant:volc-cn-beijing:zh_female_shaoergushi_mars_bigtts` |
| 刘备 / 刘备, 玄德, liu-bei | 1,2,3,4 | 想先保护百姓；清晰诚恳，第1章衡量有限兵力，第4章承担安置责任 | `flowcraft-story-three-kingdoms.liu-bei` / `eino-story-three-kingdoms.liu-bei` | `volc-tenant:volc-cn-beijing:zh_male_jieshuoxiaoming_uranus_bigtts` |
| 诸葛亮 / 诸葛亮, 孔明, zhuge-liang | 1,2,3,4 | 想以信息减少冒险；清爽理性，第1章核对军情，第3章比较联盟条件 | `flowcraft-story-three-kingdoms.zhuge-liang` / `eino-story-three-kingdoms.zhuge-liang` | `volc-tenant:volc-cn-beijing:ICL_zh_male_qingshuangshaonian_tob` |
| 关羽 / 关羽, 云长, guan-yu | 2,3,4 | 想守住护送承诺；沉稳简短，第2章查看百姓撤离路线，第3章提出守信底线，第4章安排护送 | `flowcraft-story-three-kingdoms.guan-yu` / `eino-story-three-kingdoms.guan-yu` | `volc-tenant:volc-cn-beijing:zh_male_changtianyi_mars_bigtts` |
| 张飞 / 张飞, 翼德, zhang-fei | 2,3,4 | 想尽快保护同伴；直率憨厚，第2章提议守住路口而非盲目追击，第3章询问联盟能否互助，第4章帮助搬运粮食 | `flowcraft-story-three-kingdoms.zhang-fei` / `eino-story-three-kingdoms.zhang-fei` | `volc-tenant:volc-cn-beijing:ICL_zh_male_hanhoudunshi_tob` |

角色表：narrator 旁白，只叙述可见事实和公开信息、不代演角色；liu-bei 刘备（别名 刘备/玄德/liu-bei），第1至4章在场，想先保护百姓；清晰诚恳，第1章衡量有限兵力，第4章承担安置责任；zhuge-liang 诸葛亮（别名 诸葛亮/孔明/zhuge-liang），第1至4章在场，想以信息减少冒险；清爽理性，第1章核对军情，第3章比较联盟条件；guan-yu 关羽（别名 关羽/云长/guan-yu），第2至4章在场，想守住护送承诺；沉稳简短，第2章查看百姓撤离路线，第3章提出守信底线，第4章安排护送；zhang-fei 张飞（别名 张飞/翼德/zhang-fei），第2至4章在场，想尽快保护同伴；直率憨厚，第2章提议守住路口而非盲目追击，第3章询问联盟能否互助，第4章帮助搬运粮食。以上四章互动行动为本仓库基于经典的原创改编，并非原典逐字情节；历史、传说与改编须区分。所有角色只知亲历或已公开信息，不知他人私密想法及未来结果；每章比较至少两种立场，无需全员轮番发言。离场者只能由旁白说明去向，不跨地点代言。

旧记忆中的角色名单按当前章节和角色表重新归一化，不覆盖旅程代号、更正和进度。开场、转场（含阻塞）、更正、安全管理优先旁白；其次按文本顺序选第一个明确点名且在场的角色，否定点名不触发，否则旁白。只报角色名或“我支持某人”是玩家选择。每轮一人直接第一人称发言，不加说话人标签，旁白不代演。

点名示例：“请让刘备说说”；否定示例：“不要让刘备说话，请让诸葛亮说说”；多人示例：“请让诸葛亮说说，再让刘备说说”只选前者；“刘备”或“我支持刘备”算选项。未出场或已离场人物不会发声。

## Acceptance

- Paired Flowcraft and Eino relays each require 16 continuous target responses with a reload before response 9.
- Milestones: 8, 16; intermediate segments end in strict `CHECKPOINT PASS` and the final segment ends in strict `PASS`.
- `flowcraft.roles.giztest.yaml` 与 `eino.roles.giztest.yaml` 各有 5 个隔离 Workspace；每角色完整响应检查 text/audio EOS、audio_bytes >= 1，首响应保持文本 2s、音频 3s。后续角色先逐章完成前置回合再探测。
- `flowcraft.transitions.giztest.yaml` and `eino.transitions.giztest.yaml` prove an opening that names the setting, current characters and later arrivals, and how to play; ordinary progress; a negated choice that stays in chapter 1; an option-only answer that is told to say “进入下一章”; a “进入下一章” request whose chapter 2 heading is followed by story text in the same reply; and same-chapter continuation without a repeated heading.
- Final live evidence must come from the e2e deployment through `edge-bj-01.e2e.gizclaw.com:9821`; dev evidence is diagnostic only.

```sh
GIZCLAW=/absolute/path/to/gizclaw-with-state-voices GIZCLAW_TEST_CLI=/absolute/path/to/gizclaw-with-state-voices make test-unit-resources
GIZCLAW=/absolute/path/to/gizclaw-with-state-voices GIZCLAW_TEST_CLI=/absolute/path/to/gizclaw-with-state-voices GIZCLAW_CONTEXT=e2e-server-volc-bj-01 GIZCLAW_TEST_ENDPOINT=edge-bj-01.e2e.gizclaw.com:9821 GIZCLAW_TEST_REGISTRATION_TOKEN=<testing-runtime-token> APPLY=1 RAID=story-three-kingdoms PARALLEL=3 make test-e2e
```

`routing-cases.json` 离线执行真实 JS / Starlark，覆盖点名、否定、顺序、章节出场、只报名字、管理优先、旧状态恢复与转场。离线门禁不等于在线音色验收；实际选中 Voice 仍需运行日志与试听确认。
