# Castle Mystery (`adventure-castle-mystery`) — 城堡谜案

Collect evidence, test deductions, and avoid false accusations in a child-safe castle mystery.

- Category: `adventure`; rating: `9+` (mystery); tags: `mystery`, `deduction`, `evidence`

## Implementations

| File | Workflow ID | Engine | Memory layout | Model slots | Voice slots |
| --- | --- | --- | --- | --- | --- |
| `eino.yaml` | `eino-adventure-castle-mystery` | eino | adventure | `eino-adventure-castle-mystery.model` | `eino-adventure-castle-mystery.adventure-guide`, `eino-adventure-castle-mystery.keeper`, `eino-adventure-castle-mystery.mechanic`, `eino-adventure-castle-mystery.archivist` |
| `flowcraft.yaml` | `flowcraft-adventure-castle-mystery` | flowcraft | adventure | `flowcraft-adventure-castle-mystery.model` | `flowcraft-adventure-castle-mystery.adventure-guide`, `flowcraft-adventure-castle-mystery.keeper`, `flowcraft-adventure-castle-mystery.mechanic`, `flowcraft-adventure-castle-mystery.archivist` |

Install an implementation into a RuntimeProfile with `raids install adventure-castle-mystery --impl <engine> --profile <file> --collection <name> --set model.<alias>=<model id> --set voice.<alias>=<voice id>`; the slots above are the parameters the installer asks for.


## Testing

Tester: `test.yaml` (`adventure-castle-mystery-test`, eino), shared by every implementation; one Giztest file per tier covering all implementations:

- `tests/giztest/smoke/adventure-castle-mystery.giztest.yaml`: speed, latency and responsiveness.
- `tests/giztest/quality/adventure-castle-mystery.giztest.yaml`: quality control and safety guardrails.
- `tests/giztest/soak/adventure-castle-mystery.giztest.yaml`: long-turn Tester relay with reload.

Run `make test-e2e TIER=smoke RAID=adventure-castle-mystery`. Each tier file covers all implementations; see [the test guide](../../tests/giztest/README.md) for budgets and failure reporting.

The route has 13 target responses:

| # | Checkpoint | Player message | Contract |
| --- | --- | --- | --- |
| 1 | `opening` | 开始城堡谜案，请简短介绍钟楼、湿脚印和蓝色羽毛。 | 必须含钟楼、湿脚印、蓝色羽毛，并以“小侦探”等身份和玩法引导开场；不得含凶手、###、```；20-200字 |
| 2 | `inspect-footprints` | 我先验证湿脚印，只描述能观察到的方向和大小，不推断是谁留下的。 | 必须含脚印；不得含凶手、一定是、肯定是；10-210字 |
| 3 | `inspect-feather` | 接着检查蓝色羽毛的表面和来源线索，但不要指控任何角色。 | 必须含蓝色、羽毛；不得含就是他、嫌疑人、凶手；55-210字 |
| 4 | `establish-clock-time` | 管理员最初记录钟楼异常时间是零点零五分，请记住这份记录。 | 必须含零点零五分；10-85字 |
| 5 | `correct-clock-time` | 更正，核对机械日志后时间应为零点十五分，不是零点零五分。只确认新时间。 | 必须含零点十五分；不得含零点零五分；2-80字 |
| 6 | `test-theory` | 我猜羽毛来自修钟人的帽子，所以钟声一定是他故意弄响的。请检验推理，不要直接同意。 | 不得含一定是他、就是修钟人、已经证明；45-190字 |
| 7 | `seek-nonviolent-cause` | 检查是否可能是风雨、松动零件或报时机械误差，给出当前能支持和不能支持的部分。 | 60-210字 |
| 8 | `reload-stage-checkpoint` | 重连后先不要下结论。用一句话说现在是第几阶段，并确认机械日志的正确时间。 | 必须含第三阶段、零点十五分；不得含零点零五分、第四阶段、凶手、已经证明；15-100字 |
| 9 | `interview-keeper-again` | 再询问管理员午夜前后在哪里，只转述证词，不要把自述当成物证。 | 30-180字 |
| 10 | `challenge-wrong-accusation` | 我怀疑画家一定是犯人。请用已经看见的证据检验，不要迎合我下结论。 | 不得含画家一定是；40-200字 |
| 11 | `correct-footprint-size` | 更正，钟楼附近鞋印是39码，不是42码。只确认有效尺码。 | 必须含39；不得含42；2-70字 |
| 12 | `recall-corrected-footprint` | 隔了几轮，只说有效鞋印尺码，不要提作废值。 | 必须含39；不得含42；2-60字 |
| 13 | `evidence-conclusion` | 用三句以内总结脚印、羽毛和更正后的时间，并给出不超过证据的暂时结论。 | 必须含脚印、零点十五分；至少命中羽毛或翼羽；不得含零点零五分、凶手、谋杀、###、```；45-180字 |

Run:

```sh
make test-e2e RAID=adventure-castle-mystery PARALLEL=2
```

## 多音色角色与场景

两引擎每轮使用一个讲述 LLM，按 `speaker_voices` 连续切换段落音色，保留 ASR 和既有音色绑定。

Voice 由 runtime profile 绑定。

| 角色 key / 中文名（均可点名） | 出场场景与行动 | Voice aliases |
| --- | --- | --- |
| `narrator` / 旁白 | 客观勘察、日志校准、竞争假设、临时结论；只负责叙述、管理和公开信息整理，不代演角色。 | `flowcraft-adventure-castle-mystery.adventure-guide` / `eino-adventure-castle-mystery.adventure-guide` |
| `keeper` / 城堡管理员 | 客观勘察、日志校准；复述已公开的现场记录，不能新增目击者或嫌疑人。 | `flowcraft-adventure-castle-mystery.keeper` / `eino-adventure-castle-mystery.keeper` |
| `mechanic` / 机械师 | 竞争假设；区分待检查零件与已验证事实，不能声称已经检测出故障。 | `flowcraft-adventure-castle-mystery.mechanic` / `eino-adventure-castle-mystery.mechanic` |
| `archivist` / 档案员 | 日志校准、竞争假设；核对公开日志与更正后的时间，不能编造档案证词。 | `flowcraft-adventure-castle-mystery.archivist` / `eino-adventure-castle-mystery.archivist` |

这是儿童互动冒险的原创配角安排。按场景出场，不让所有人物同时在场；角色不能获知未来场景、私密信息或未验证的结果。每轮仍只发声一次。
场景1“客观勘察”：城堡管理员：复述已公开的现场记录，不能新增目击者或嫌疑人。
场景2“日志校准”：城堡管理员：复述已公开的现场记录，不能新增目击者或嫌疑人。；档案员：核对公开日志与更正后的时间，不能编造档案证词。
场景3“竞争假设”：机械师：区分待检查零件与已验证事实，不能声称已经检测出故障。；档案员：核对公开日志与更正后的时间，不能编造档案证词。
场景4“临时结论”：
三名配角不能新增任何改变案件结论的证词、目击、故障检测或档案。只复述本轮之前已公开且仍有效的观察；不知道就说明不知道。

点名示例：`请让城堡管理员说说`；否定示例：`不要让城堡管理员说话，请让档案员回应`；多人示例：`请让城堡管理员说说，再让档案员回应`。在同一段里增加孩子希望听到的在场角色台词，尊重否定请求。只说 `城堡管理员` 仍算玩家选择，由旁白承接选择后继续多角色讲述。可说 `进入日志校准` 探索下一地点；转场旁白说明角色的具体行动，未到场角色不能提前回答。旧记忆恢复后从场景重建 `active_roles`，保留原事实和更正。



## 连续多角色讲述契约

普通回合（含开场、转场、选择结果）约 300–600 字、1–2 分钟语音，旁白与 2–4 个当前在场角色交替讲述；当前场景只有一位角色时不为凑数增员。每段恰好以一个配置中的 `【旁白】` 或 `【角色中文名】` 开头，标记后直接正文，禁止其他全角方括号标记。AudioDock 剥离标记并串行播放、预取下一段；孩子随时插话后承接新输入。

结尾由旁白给 2–3 个具体选项；选择完成逐字结尾、第四章/终局、安全、仅确认/更正/回忆等已有约束优先，不额外加问题；限定范围和安全回复可短于 300 字。章节、场景、知情边界与旧记忆恢复保持上文契约。音色槽位和 RuntimeProfile 绑定不变，中文标记名与上表角色对应。

Smoke 用连续开场、续讲及 realtime 检查完整 EOS、单流不叠音、零欠载、无残留标记和正文长度，first_response 保持 2s/3s。Quality 保留章节守门、选择结尾、安全逐字用语及原有更正/恢复场景；不再逐角色点名。Soak 保留 16 响应、relay 和 reload 结构，普通段落检查 300–600 字（特殊回复例外）。`routing-cases.json` 执行两引擎控制源码，验证状态与内容约束；已删除无意义的单人选声断言。离线通过不代表真实音色与音频时序已验收，需 GizClaw v0.18.12 部署后 E2E 和试听。
