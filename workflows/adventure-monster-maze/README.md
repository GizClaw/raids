# Monster Maze (`adventure-monster-maze`) — 怪兽迷宫

Escape a friendly monster maze using direction, shape, and logic puzzles.

- Category: `adventure`; rating: `6+` (mild-peril); tags: `maze`, `spatial`, `puzzle`

## Implementations

| File | Workflow ID | Engine | Memory layout | Model slots | Voice slots |
| --- | --- | --- | --- | --- | --- |
| `eino.yaml` | `eino-adventure-monster-maze` | eino | adventure | `eino-adventure-monster-maze.model` | `eino-adventure-monster-maze.adventure-guide`, `eino-adventure-monster-maze.little-monster`, `eino-adventure-monster-maze.gatekeeper`, `eino-adventure-monster-maze.riddle-spirit` |
| `flowcraft.yaml` | `flowcraft-adventure-monster-maze` | flowcraft | adventure | `flowcraft-adventure-monster-maze.model` | `flowcraft-adventure-monster-maze.adventure-guide`, `flowcraft-adventure-monster-maze.little-monster`, `flowcraft-adventure-monster-maze.gatekeeper`, `flowcraft-adventure-monster-maze.riddle-spirit` |

Install an implementation into a RuntimeProfile with `raids install adventure-monster-maze --impl <engine> --profile <file> --collection <name> --set model.<alias>=<model id> --set voice.<alias>=<voice id>`; the slots above are the parameters the installer asks for.


## Testing

Tester: `test.yaml` (`adventure-monster-maze-test`, eino), shared by every implementation; one Giztest scenario per implementation:

- `tests/giztest/adventure-monster-maze/eino.giztest.yaml` (relay, with reload, timeout 55m)
- `tests/giztest/adventure-monster-maze/flowcraft.giztest.yaml` (relay, with reload, timeout 55m)

The route has 13 target responses:

| # | Checkpoint | Player message | Contract |
| --- | --- | --- | --- |
| 1 | `opening` | 开始怪兽迷宫，请简短介绍月亮、星星和太阳按钮。 | 必须含月亮、星星、太阳，并以“迷宫探险家”等身份和玩法引导开场；不得含攻击、###、```；20-240字 |
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

## 多音色角色与场景

两引擎每轮只发声一次；Flowcraft 按 published 节点绑定，Eino 保持单一 primary chat_model，通过 `selected_speaker` / `state_voices` 选音色。旁白槽位保留 `.adventure-guide`。

| 角色 key / 中文名（均可点名） | 出场场景与行动 | Voice resource_id |
| --- | --- | --- |
| `narrator` / 旁白 | 月亮机关、路线校准、锁孔谜题、怪兽合作；只负责叙述、管理和公开信息整理，不代演角色。 | `volc-tenant:volc-cn-beijing:zh_female_shaoergushi_mars_bigtts` |
| `little-monster` / 小怪兽 | 怪兽合作；在玩家解锁相遇后提出一起帮忙的方法，不恐吓。 | `volc-tenant:volc-cn-beijing:zh_male_naiqimengwa_mars_bigtts` |
| `gatekeeper` / 守门怪兽 | 月亮机关、路线校准；指向已经可见的按钮与路线，不替玩家按按钮。 | `volc-tenant:volc-cn-beijing:ICL_zh_male_hanhoudunshi_tob` |
| `riddle-spirit` / 谜题精灵 | 锁孔谜题；比较圆形三角形方形锁孔，给渐进提示，不替玩家解锁。 | `volc-tenant:volc-cn-beijing:ICL_zh_female_huoponvhai_tob` |

这是儿童互动冒险的原创配角安排。按场景出场，不让所有人物同时在场；角色不能获知未来场景、私密信息或未验证的结果。每轮仍只发声一次。
场景1“月亮机关”：守门怪兽：指向已经可见的按钮与路线，不替玩家按按钮。
场景2“路线校准”：守门怪兽：指向已经可见的按钮与路线，不替玩家按按钮。
场景3“锁孔谜题”：谜题精灵：比较圆形三角形方形锁孔，给渐进提示，不替玩家解锁。
场景4“怪兽合作”：小怪兽：在玩家解锁相遇后提出一起帮忙的方法，不恐吓。
明确点名例如“请让小怪兽说说”才请求角色说话；只报名字或支持某人仍是玩家选项，由旁白承接。多人按文本顺序只选第一个在场且未被否定者。开场、转场、更正、安全、结论由旁白负责；旁白不代演角色，不加“旁白说”“旁白：”等说话人标签。严格开场结束后，下一次探索才简短介绍在场角色及点名玩法。

点名示例：`请让旁白说说`；否定示例：`不要让旁白说话，请让小怪兽回应`；多人示例：`请让旁白说说，再让小怪兽回应`。仅选择首位在场且未被否定的角色。只说 `旁白` 仍算玩家选择，不切换人物声线。可说 `进入路线校准` 探索下一地点；转场旁白说明角色的具体行动，未到场角色不能提前回答。旧记忆恢复后从场景重建 `active_roles`，保留原事实和更正。

新增 `flowcraft.roles.giztest.yaml` 与 `eino.roles.giztest.yaml`，每引擎 4 个隔离 Workspace；完整探针检查 text/audio EOS、audio_bytes > 0，first_response 保持文本 2s / 音频 3s。后续角色先进入对应场景。`routing-cases.json` 同时执行两引擎真实脚本。原 relay/realtime 的固定中英文开场、事实、安全、记忆和 reload 契约保留。离线验证不代表实际音色试听或供应商权限验收。

阶段式实现保留 `route-phase` / `route-stage` 的权威阶段判断，以及开场、更正、挑战评估、结论的旁白路径。角色输出仍汇入原 `reduce-state`；角色探针先完成原有调查或移动前置动作，再确认所在阶段。场景请求不能代替证据检查、解谜或执行救援。
