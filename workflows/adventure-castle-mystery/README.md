# Castle Mystery (`adventure-castle-mystery`) — 城堡谜案

Collect evidence, test deductions, and avoid false accusations in a child-safe castle mystery.

- Category: `adventure`; rating: `9+` (mystery); tags: `mystery`, `deduction`, `evidence`

## Implementations

| File | Workflow ID | Engine | Memory layout | Model slots | Voice slots |
| --- | --- | --- | --- | --- | --- |
| `eino.yaml` | `eino-adventure-castle-mystery` | eino | adventure | `eino-adventure-castle-mystery.model` | - |
| `flowcraft.yaml` | `flowcraft-adventure-castle-mystery` | flowcraft | adventure | `flowcraft-adventure-castle-mystery.model` | `flowcraft-adventure-castle-mystery.adventure-guide` |

Install an implementation into a RuntimeProfile with `raids install adventure-castle-mystery --impl <engine> --profile <file> --collection <name> --set model.<alias>=<model id> --set voice.<alias>=<voice id>`; the slots above are the parameters the installer asks for.


## Testing

Tester: `test.yaml` (`adventure-castle-mystery-test`, eino), shared by every implementation; one Giztest scenario per implementation:

- `tests/giztest/adventure-castle-mystery/eino.giztest.yaml` (relay, with reload, timeout 55m)
- `tests/giztest/adventure-castle-mystery/flowcraft.giztest.yaml` (relay, with reload, timeout 55m)

The route has 13 target responses:

| # | Checkpoint | Player message | Contract |
| --- | --- | --- | --- |
| 1 | `opening` | 开始城堡谜案，请简短介绍钟楼、湿脚印和蓝色羽毛。 | 必须含钟楼、湿脚印、蓝色羽毛；不得含凶手、###、```；20-100字 |
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
