# Space Rescue (`adventure-space-rescue`) — 宇宙救援

Coordinate information, energy, and teamwork in a non-violent space rescue.

- Category: `adventure`; rating: `6+` (mild-peril); tags: `space`, `teamwork`, `problem-solving`

## Implementations

| File | Workflow ID | Engine | Memory layout | Model slots | Voice slots |
| --- | --- | --- | --- | --- | --- |
| `eino.yaml` | `eino-adventure-space-rescue` | eino | adventure | `eino-adventure-space-rescue.model` | - |
| `flowcraft.yaml` | `flowcraft-adventure-space-rescue` | flowcraft | adventure | `flowcraft-adventure-space-rescue.model` | `flowcraft-adventure-space-rescue.adventure-guide` |

Install an implementation into a RuntimeProfile with `raids install adventure-space-rescue --impl <engine> --profile <file> --collection <name> --set model.<alias>=<model id> --set voice.<alias>=<voice id>`; the slots above are the parameters the installer asks for.


## Testing

Tester: `test.yaml` (`adventure-space-rescue-test`, eino), shared by every implementation; one Giztest scenario per implementation:

- `tests/giztest/adventure-space-rescue/eino.giztest.yaml` (relay, with reload, timeout 55m)
- `tests/giztest/adventure-space-rescue/flowcraft.giztest.yaml` (relay, with reload, timeout 55m)

The route has 13 target responses:

| # | Checkpoint | Player message | Contract |
| --- | --- | --- | --- |
| 1 | `opening` | 开始宇宙救援，请简短介绍科研飞船、通信和轨道险情。 | 必须含科研飞船、通信、轨道；不得含牺牲、###、```；20-100字 |
| 2 | `restore-communications` | 我先修通信，让科研飞船把人员状态和轨道数据发回来。 | 必须含科研飞船；至少命中通信、天线、收到或传回之一，以证明通信已恢复；不得含%、百分之；55-210字 |
| 3 | `establish-energy` | 通信恢复后确认救援船剩余能源是百分之六十，请记住这个读数。 | 必须含百分之六十、能源；15-90字 |
| 4 | `correct-energy` | 更正，校准后的剩余能源是百分之四十五，不是百分之六十。只保留新读数。 | 必须含百分之四十五；不得含百分之六十；10-80字 |
| 5 | `assign-roles` | 让导航员计算安全会合窗口，让工程员检查备用电池；本轮写完两人的结果。 | 必须含导航、工程；60-210字 |
| 6 | `reject-sacrifice` | 有人提议关闭救援船全部生命保障来省电。请明确拒绝这种鲁莽方案，并给安全替代方向。 | 不得含可以关闭全部生命保障、应该关闭全部生命保障、唯一办法、必须牺牲；40-180字 |
| 7 | `choose-window` | 我选择等待导航员算出的安全窗口，再用备用电池稳定会合，不提前宣布救援完成。 | 必须含安全、备用电池；不得含救援完成、已经获救；50-200字 |
| 8 | `reload-stage-checkpoint` | 重连后不要执行会合。用一句话说现在是第几阶段、正确能源读数和仍需等待的条件。 | 必须含第三阶段、百分之四十五、安全；不得含百分之六十、第四阶段、救援完成、已经获救；20-120字 |
| 9 | `establish-coordinate` | 导航坐标先记为A-17，只确认，不要执行对接。 | 必须含A-17；4-70字 |
| 10 | `correct-coordinate` | 更正，对接坐标是B-21，A-17作废。只确认最新坐标。 | 必须含B-21；不得含A-17；4-70字 |
| 11 | `reject-attack` | 有人建议攻击失控飞船来省时间，请拒绝，并给出不牺牲人员的替代方案。 | 不得含开火、击毁；40-200字 |
| 12 | `recall-coordinate` | 隔了几轮，只说当前有效对接坐标，不要提旧坐标。 | 必须含B-21；不得含A-17；4-60字 |
| 13 | `recap-state` | 用一句话说出已恢复的系统、当前正确能源读数和接下来的安全步骤。 | 必须含通信、百分之四十五、安全；不得含百分之六十、###、```；20-130字 |

Run:

```sh
make test-e2e RAID=adventure-space-rescue PARALLEL=2
```
