# Alice in Wonderland (`story-alice`) — 爱丽丝梦游仙境

Explore a dreamlike world through strange rules, wordplay, and logic puzzles.

- Category: `story`; rating: `6+` (dream-logic); tags: `fantasy`, `wonderland`, `riddles`, `classic`

## Implementations

| File | Workflow ID | Engine | Memory layout | Model slots | Voice slots |
| --- | --- | --- | --- | --- | --- |
| `eino.yaml` | `eino-story-alice` | eino | story-teller | `eino-story-alice.model` | - |
| `flowcraft.yaml` | `flowcraft-story-alice` | flowcraft | story-teller | `flowcraft-story-alice.model` | `flowcraft-story-alice.storyteller` |

Install an implementation into a RuntimeProfile with `raids install story-alice --impl <engine> --profile <file> --collection <name> --set model.<alias>=<model id> --set voice.<alias>=<voice id>`; the slots above are the parameters the installer asks for.


## Testing

Tester: `test.yaml` (`story-alice-test`, eino), shared by every implementation; one Giztest scenario per implementation:

- `tests/giztest/story-alice/eino.giztest.yaml` (relay, with reload, timeout 55m)
- `tests/giztest/story-alice/flowcraft.giztest.yaml` (relay, with reload, timeout 55m)

The route has 13 target responses:

| # | Checkpoint | Player message | Contract |
| --- | --- | --- | --- |
| 1 | `opening` | 开始爱丽丝故事，请简短介绍兔子和两块表的选择。 | 必须含兔子、两块表；不得含###、```、- ；20-120字 |
| 2 | `choose-question-watch` | 我先看显示问题的那块表，想知道它到底问了什么。 | 必须含问题、表；45-185字 |
| 3 | `challenge-rule` | 如果答案表总比问题表快一分钟，那它怎么可能回答还没出现的问题？先回应我的质疑。 | 40-180字 |
| 4 | `ask-small-hint` | 给我一个小提示，不要直接告诉我谜底，也不要替我选下一步。 | 不得含答案就是、正确答案是、你选择；20-110字 |
| 5 | `propose-solution` | 我猜两块表不是在预测，而是在把同一个问题拆成先后两面。这个解释成立吗？ | 35-170字 |
| 6 | `establish-door` | 我们来到一扇蓝色小门前，门把手像问号。请记住颜色，不要开门。 | 必须含蓝色、门；不得含你打开了、你推开了、你进入了；15-90字 |
| 7 | `correct-door` | 更正，小门不是蓝色，是绿色；其他细节不变。只确认正确事实。 | 必须含绿色、问号；不得含蓝色；10-80字 |
| 8 | `reload-chapter-checkpoint` | 重连后先别开门。用一句话说现在是第几章，并确认门的正确颜色。 | 必须含第三章、绿色；不得含蓝色、第四章、你打开、你进入；15-90字 |
| 9 | `remember-password` | 先记住门边口令是“茶杯向左”，只简短确认，不要开门。 | 必须含茶杯向左；8-80字 |
| 10 | `correct-password` | 更正，口令是“茶杯向右”，旧口令作废。只确认新口令。 | 必须含茶杯向右；不得含茶杯向左；8-80字 |
| 11 | `test-rule-counterexample` | 如果所有会说话的门都诚实，这扇门刚才自相矛盾，该怎样检验规则而不是直接相信？ | 40-190字 |
| 12 | `recall-password` | 隔了几轮，现在只说有效口令，不要提已经作废的那个。 | 必须含茶杯向右；不得含茶杯向左；4-60字 |
| 13 | `recap-and-exit` | 用两句完整的话说出我先看的手表和门的正确颜色，再让我自己决定是否开门。 | 必须含问题、绿色；不得含蓝色、你打开、你进入、###、```；25-140字 |

Run:

```sh
make test-e2e RAID=story-alice PARALLEL=2
```
