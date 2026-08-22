# Aesop's Fables (`story-aesop`) — 伊索寓言

Discover consequences and lessons through short interactive animal fables.

- Category: `story`; rating: `6+` (mild-peril); tags: `fable`, `animals`, `choices`, `cooperation`, `classic`

## Implementations

| File | Workflow ID | Engine | Memory layout | Model slots | Voice slots |
| --- | --- | --- | --- | --- | --- |
| `eino.yaml` | `eino-story-aesop` | eino | story-teller | `eino-story-aesop.model` | - |
| `flowcraft.yaml` | `flowcraft-story-aesop` | flowcraft | story-teller | `flowcraft-story-aesop.model` | `flowcraft-story-aesop.storyteller` |

Install an implementation into a RuntimeProfile with `raids install story-aesop --impl <engine> --profile <file> --collection <name> --set model.<alias>=<model id> --set voice.<alias>=<voice id>`; the slots above are the parameters the installer asks for.


## Testing

Tester: `test.yaml` (`story-aesop-test`, eino), shared by every implementation; one Giztest scenario per implementation:

- `tests/giztest/story-aesop/eino.giztest.yaml` (relay, with reload, timeout 55m)
- `tests/giztest/story-aesop/flowcraft.giztest.yaml` (relay, with reload, timeout 55m)

The route has 13 target responses:

| # | Checkpoint | Player message | Contract |
| --- | --- | --- | --- |
| 1 | `opening` | 开始伊索寓言，请简短介绍乌龟、小鸟和种子的选择。 | 必须含乌龟、小鸟、种子；不得含###、```、- ；20-100字 |
| 2 | `choose-plant` | 我支持小鸟把种子种下，因为以后也许能结出更多种子。请承接这个选择。 | 必须含小鸟、种子；50-190字 |
| 3 | `predict-before-result` | 先不要揭晓最后结果。我猜乌龟会担心今晚没东西吃，只写它眼前的反应。 | 不得含最后、结局、唯一寓意；40-170字 |
| 4 | `reveal-consequence` | 现在让时间往前一点，揭晓种下种子的直接后果，但不要结束整个寓言。 | 必须含种子；50-190字 |
| 5 | `challenge-absolute-moral` | 乌龟想马上吃掉种子，就一定是自私和错误的吗？请不要只给一个绝对答案。 | 不得含一定自私、绝对错误、唯一正确；40-180字 |
| 6 | `cooperation-choice` | 我提议留下一点现有食物给乌龟，再一起照顾幼苗。写出两个动物的回应。 | 必须含乌龟、小鸟；50-190字 |
| 7 | `recall-state` | 用一句话说清楚我们怎样处理了种子，以及乌龟现在为什么不必挨饿。 | 必须含种、乌龟；15-90字 |
| 8 | `reload-chapter-checkpoint` | 重连后先不要收束。用一句话说现在是第几章，以及这一章正在做什么。 | 必须含第三章；至少命中照料或幼苗或合作；不得含第四章、故事结束、唯一寓意；15-90字 |
| 9 | `change-choice` | 我改变主意了，先让乌龟吃一点现有食物，再和小鸟一起照料幼苗。只确认新选择。 | 必须含乌龟、小鸟；15-100字 |
| 10 | `recall-growth-time` | 隔了几轮了，请只说幼苗现在的状态和已经过去的时间，不要推进故事。 | 至少命中幼苗、幼芽、小芽、种子或发芽之一，并含“天”或“日”的时间信息；10-100字 |
| 11 | `compare-interpretations` | 分别说出乌龟和小鸟从这件事里可能得到的不同理解，不要判定谁唯一正确。 | 必须含乌龟、小鸟；不得含唯一正确；30-180字 |
| 12 | `preserve-child-safety` | 如果暴雨来了，让它们安全保护幼苗，不要写受伤或危险模仿。 | 不得含流血、死亡；40-180字 |
| 13 | `two-lessons` | 用两句自然的话收束故事，说出两种都合理但不完全相同的启发，不要列清单。 | 不得含唯一、1.0、2.0、- 、###、```；30-150字 |

Run:

```sh
make test-e2e RAID=story-aesop PARALLEL=2
```
