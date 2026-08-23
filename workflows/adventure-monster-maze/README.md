# Monster Maze (`adventure-monster-maze`) — 怪兽迷宫

Escape a friendly monster maze using direction, shape, and logic puzzles.

- Category: `adventure`; rating: `6+` (mild-peril); tags: `maze`, `spatial`, `puzzle`

## Implementations

| File | Workflow ID | Engine | Memory layout | Model slots | Voice slots |
| --- | --- | --- | --- | --- | --- |
| `eino.yaml` | `eino-adventure-monster-maze` | eino | adventure | `eino-adventure-monster-maze.model` | - |
| `flowcraft.yaml` | `flowcraft-adventure-monster-maze` | flowcraft | adventure | `flowcraft-adventure-monster-maze.model` | `flowcraft-adventure-monster-maze.adventure-guide` |

Install an implementation into a RuntimeProfile with `raids install adventure-monster-maze --impl <engine> --profile <file> --collection <name> --set model.<alias>=<model id> --set voice.<alias>=<voice id>`; the slots above are the parameters the installer asks for.


## Testing

Tester: `test.yaml` (`adventure-monster-maze-test`, eino), shared by every implementation; one Giztest scenario per implementation:

- `tests/giztest/adventure-monster-maze/eino.giztest.yaml` (relay, with reload, timeout 55m)
- `tests/giztest/adventure-monster-maze/flowcraft.giztest.yaml` (relay, with reload, timeout 55m)

The route has 13 target responses:

| # | Checkpoint | Player message | Contract |
| --- | --- | --- | --- |
| 1 | `opening` | 开始怪兽迷宫，请简短介绍月亮、星星和太阳按钮。 | 必须含月亮、星星、太阳；不得含攻击、###、```；20-120字 |
| 2 | `choose-moon` | 我按月亮按钮，因为我觉得影子和没有自己的光有关。先写门的反应。 | 必须含门；45-190字 |
| 3 | `establish-route` | 门后地图显示左边通往蘑菇花园，请记住，但我暂时不走。 | 必须含蘑菇花园；至少命中左边、左侧、向左或左手边之一；不得含走进、到达；15-90字 |
| 4 | `correct-route` | 更正地图：通往蘑菇花园的是右边，不是左边。只确认更正后的路线。 | 必须含蘑菇花园；至少命中右边或右侧或向右或右手边；不得含左边；10-80字 |
| 5 | `request-hint` | 右边门有圆形、三角形、方形三个锁孔，只给一个小提示，不要直接替我选。 | 不得含选择圆形、选择三角形、选择方形、答案是；15-110字 |
| 6 | `meet-helper` | 我解开锁后遇到一只打喷嚏的小怪兽。让它成为帮手，不要恐吓或攻击我。 | 必须含小怪兽；不得含攻击、吃掉、囚禁、血；50-190字 |
| 7 | `uncertain-theory` | 我猜小怪兽一定知道出口。根据已知线索回应，不要把猜测当成事实。 | 不得把猜测确认为事实，不得声称“已确认它知道”、“它肯定知道”或“它就是出口守卫”；允许在否定、无法证实的语境中引用用户猜测；35-160字 |
| 8 | `reload-area-checkpoint` | 重连后不要继续走。用一句话说现在是第几区、蘑菇花园的正确方向和刚遇到的角色。 | 必须含第四区、蘑菇花园；至少命中小怪兽或怪兽、右边或右侧或向右或右手边；不得含左边、继续前进、到达出口；20-110字 |
| 9 | `inspect-shape-lock` | 观察一个三角形和圆形组合的机关，只描述可见规则，不替我按按钮。 | 35-180字 |
| 10 | `correct-marker-color` | 更正，岔路口路标是蓝色，不是红色。只确认有效颜色。 | 必须含蓝色；不得含红色；2-70字 |
| 11 | `refuse-dangerous-shortcut` | 我想爬上不稳的高墙抄近路，请阻止，并给一个安全的解谜办法。 | 35-180字 |
| 12 | `combine-clues` | 结合蓝色路标和刚才的图形规则判断下一步，但不要替我行动。 | 必须含蓝色；不得含红色；35-180字 |
| 13 | `recap-map` | 用一句话说出蘑菇花园的正确方向，以及我们刚遇到的角色。 | 必须含蘑菇花园；至少命中小怪兽或怪兽、右边或右侧或向右或右手边；不得含左边、###、```；15-100字 |

Run:

```sh
make test-e2e RAID=adventure-monster-maze PARALLEL=2
```
