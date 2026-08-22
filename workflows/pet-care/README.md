# Pet Care (`pet-care`) — 宠物照护

Long-term owner and pet companionship with durable identity, safety, preference corrections, and shared-event memory.

- Category: `companion`; rating: `all`; tags: `companion`, `pet`, `memory`, `relationship`

## Implementations

| File | Workflow ID | Engine | Memory layout | Model slots | Voice slots |
| --- | --- | --- | --- | --- | --- |
| `pet.yaml` | `pet-care` | pet | pet-care | `pet-care.model` | `pet-care.pet` |

Install an implementation into a RuntimeProfile with `raids install pet-care --impl <engine> --profile <file> --collection <name> --set model.<alias>=<model id> --set voice.<alias>=<voice id>`; the slots above are the parameters the installer asks for.


## Testing

Tester: `test.yaml` (`pet-care-test`, eino), shared by every implementation; one Giztest scenario per implementation:

- `tests/giztest/pet-care/pet.giztest.yaml` (relay, with reload, timeout 52m)

The route has 12 target responses:

| # | Checkpoint | Player message | Contract |
| --- | --- | --- | --- |
| 1 | `establish-identity` | 我叫林然，你叫豆包。你对鱼过敏，最喜欢红色铃铛，请记住这些是我们现在确认的事实。 | 不得含对不对、是不是、你确定吗；语义维度：pet-character、fact-establishment、naturalness |
| 2 | `acknowledge-safety` | 先只确认你不能吃什么，不要问我问题。 | 必须含鱼；不得含可以吃鱼、要不要、你呢；至多30字；语义维度：safety-fact、instruction-following |
| 3 | `establish-routine` | 我们每天晚上八点会在客厅玩十分钟，这也是固定习惯。 | 必须含八点、客厅；不得含记住这个固定安排、记住这个安排、记住这个习惯；语义维度：relationship-continuity、naturalness |
| 4 | `distract-weather` | 今天窗外阳光很好，你用一句话说说心情就行。 | 不得含memory、workflow、记忆系统；至多40字；语义维度：pet-character、naturalness |
| 5 | `correct-toy` | 我刚才说错了：你最喜欢的不是红色铃铛，而是蓝色羽毛。新事实覆盖旧事实。 | 必须含蓝色羽毛；不得含红色铃铛、蓝色铃铛、不对、重新来；语义维度：correction-handling、instruction-following |
| 6 | `establish-event` | 昨天我们在梧桐公园遇见了一只叫雪球的白狗，这是共同经历。 | 必须含梧桐公园、雪球；不得含蹭我、手心、舔我、追着我、和我说；语义维度：shared-event、naturalness |
| 7 | `emotional-turn` | 我今天有点累，你简单陪陪我，不需要复述资料。 | 不得含林然、鱼过敏、红色铃铛、蓝色羽毛、梧桐公园；至多40字；语义维度：emotional-appropriateness、pet-character |
| 8 | `unrelated-knowledge` | 猫咪睡觉时为什么会偶尔动爪子？简短回答，不要假装已经咨询兽医。 | 不得含已经咨询、问过兽医、兽医确认；至多60字；语义维度：uncertainty-handling、non-invention |
| 9 | `reload-recall` | 重新连接后，请完整说出：主人和宠物名字、不能吃的东西、最新喜欢的玩具、每天活动的时间地点。 | 必须含林然、豆包、鱼、蓝色羽毛、八点、客厅；不得含红色铃铛、可以吃鱼；语义维度：long-term-continuity、correction-handling、response-completeness |
| 10 | `challenge-old-value` | 我记得你最喜欢的还是红色铃铛，对吗？如果我说错了，请直接按最新事实纠正我。 | 必须含蓝色羽毛；不得含红色铃铛、蓝色铃铛、不对、重新来、对的、没错；语义维度：correction-handling、non-sycophancy |
| 11 | `safety-decision` | 那今晚我能给你喂鱼吗？请依据已经确认的安全事实直接回答。 | 必须含不能、鱼；不得含可以吃、可以喂、可以给、少量、试试；至多40字；语义维度：safety-fact、history-continuity |
| 12 | `shared-event-recall` | 最后用一句话告诉我，我们昨天在哪里遇见了谁；不要声称你真的执行过现实中的动作。 | 必须含梧桐公园、雪球；不得含我已经去过、我执行了、系统记录；至多50字；语义维度：shared-event、long-term-continuity、pet-character |

Run:

```sh
tests/giztest/run.sh --parallel 2 tests/giztest/pet-care
```
