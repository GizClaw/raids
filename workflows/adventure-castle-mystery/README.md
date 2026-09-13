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

Tester: `test.yaml` (`adventure-castle-mystery-test`, eino), shared by every implementation; one Giztest scenario per implementation:

- `tests/giztest/adventure-castle-mystery/eino.giztest.yaml` (relay, with reload, timeout 55m)
- `tests/giztest/adventure-castle-mystery/flowcraft.giztest.yaml` (relay, with reload, timeout 55m)

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

两引擎每轮只发声一次；Flowcraft 按 published 节点绑定，Eino 保持单一 primary chat_model，通过 `selected_speaker` / `state_voices` 选音色。旁白槽位保留 `.adventure-guide`。

| 角色 key / 中文名（均可点名） | 出场场景与行动 | Voice resource_id |
| --- | --- | --- |
| `narrator` / 旁白 | 客观勘察、日志校准、竞争假设、临时结论；只负责叙述、管理和公开信息整理，不代演角色。 | `volc-tenant:volc-cn-beijing:zh_female_shaoergushi_mars_bigtts` |
| `keeper` / 城堡管理员 | 客观勘察、日志校准；复述已公开的现场记录，不能新增目击者或嫌疑人。 | `volc-tenant:volc-cn-beijing:ICL_zh_male_youmodaye_tob` |
| `mechanic` / 机械师 | 竞争假设；区分待检查零件与已验证事实，不能声称已经检测出故障。 | `volc-tenant:volc-cn-beijing:ICL_zh_male_hanhoudunshi_tob` |
| `archivist` / 档案员 | 日志校准、竞争假设；核对公开日志与更正后的时间，不能编造档案证词。 | `volc-tenant:volc-cn-beijing:zh_female_wenroushunv_uranus_bigtts` |

这是儿童互动冒险的原创配角安排。按场景出场，不让所有人物同时在场；角色不能获知未来场景、私密信息或未验证的结果。每轮仍只发声一次。
场景1“客观勘察”：城堡管理员：复述已公开的现场记录，不能新增目击者或嫌疑人。
场景2“日志校准”：城堡管理员：复述已公开的现场记录，不能新增目击者或嫌疑人。；档案员：核对公开日志与更正后的时间，不能编造档案证词。
场景3“竞争假设”：机械师：区分待检查零件与已验证事实，不能声称已经检测出故障。；档案员：核对公开日志与更正后的时间，不能编造档案证词。
场景4“临时结论”：
明确点名例如“请让城堡管理员说说”才请求角色说话；只报名字或支持某人仍是玩家选项，由旁白承接。多人按文本顺序只选第一个在场且未被否定者。开场、转场、更正、安全、结论由旁白负责；旁白不代演角色，不加“旁白说”“旁白：”等说话人标签。严格开场结束后，下一次探索才简短介绍在场角色及点名玩法。
三名配角不能新增任何改变案件结论的证词、目击、故障检测或档案。只复述本轮之前已公开且仍有效的观察；不知道就说明不知道。

点名示例：`请让城堡管理员说说`；否定示例：`不要让城堡管理员说话，请让档案员回应`；多人示例：`请让城堡管理员说说，再让档案员回应`。仅选择首位在场且未被否定的角色。只说 `城堡管理员` 仍算玩家选择，不切换人物声线。可说 `进入日志校准` 探索下一地点；转场旁白说明角色的具体行动，未到场角色不能提前回答。旧记忆恢复后从场景重建 `active_roles`，保留原事实和更正。

新增 `flowcraft.roles.giztest.yaml` 与 `eino.roles.giztest.yaml`，每引擎 4 个隔离 Workspace；完整探针检查 text/audio EOS、audio_bytes > 0，first_response 保持文本 2s / 音频 3s。后续角色先进入对应场景。`routing-cases.json` 同时执行两引擎真实脚本。原 relay/realtime 的固定中英文开场、事实、安全、记忆和 reload 契约保留。离线验证不代表实际音色试听或供应商权限验收。

阶段式实现保留 `route-phase` / `route-stage` 的权威阶段判断，以及开场、更正、挑战评估、结论的旁白路径。角色输出仍汇入原 `reduce-state`；角色探针先完成原有调查或移动前置动作，再确认所在阶段。场景请求不能代替证据检查、解谜或执行救援。
