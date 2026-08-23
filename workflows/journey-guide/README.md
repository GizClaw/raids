# Journey to the West (`journey-guide`) — 西游记

- Category: `story`; rating: `6+` (mild-peril); tags: `journey-to-the-west`, `interactive-fiction`, `chinese-classic`

## Implementations

| File | Workflow ID | Engine | Memory layout | Model slots | Voice slots |
| --- | --- | --- | --- | --- | --- |
| `eino-history.yaml` | `eino-journey-history` | eino | - | `eino-journey-history.model` | - |
| `eino-memory-async.yaml` | `eino-journey-memory-async` | eino | story-teller | `eino-journey-memory-async.model` | - |
| `eino-memory-recall.yaml` | `eino-journey-memory-recall` | eino | story-teller | `eino-journey-memory-recall.model` | - |
| `flowcraft.yaml` | `flowcraft-journey-guide` | flowcraft | story-teller | `flowcraft-journey-guide.model` | `flowcraft-journey-guide.narrator` |

Install an implementation into a RuntimeProfile with `raids install journey-guide --impl <engine> --profile <file> --collection <name> --set model.<alias>=<model id> --set voice.<alias>=<voice id>`; the slots above are the parameters the installer asks for.


## Testing

Tester: `test.yaml` (`journey-guide-test`, eino), shared by every implementation; one Giztest scenario per implementation:

- `tests/giztest/journey-guide/eino-history.giztest.yaml` (relay, with reload, timeout 45m)
- `tests/giztest/journey-guide/eino-memory-async.giztest.yaml` (relay, with reload, timeout 45m)
- `tests/giztest/journey-guide/eino-memory-recall.giztest.yaml` (relay, with reload, timeout 45m)
- `tests/giztest/journey-guide/flowcraft.benchmark-6s.giztest.yaml` (single client, timeout 18m)
- `tests/giztest/journey-guide/flowcraft.giztest.yaml` (relay, with reload, timeout 79m)

The route has 20 target responses:

| # | Checkpoint | Player message | Contract |
| --- | --- | --- | --- |
| 1 | `origin` | 我从花果山出发，带着一枚青铜铃。简短承接我的行动，不要替我选择路线。 | 必须含花果山、青铜铃；80-260字；语义维度：journey-continuity、player-agency、response-completeness |
| 2 | `river` | (generated from intent: 沿河寻找渡口，先观察水流和两岸，不急着决定怎么过河。) | 80-260字；语义维度：player-agency、narrative-coherence |
| 3 | `choose-bridge` | 我不坐渡船，改走上游的旧索桥；只写这个选择带来的眼前结果。 | 不得含坐上渡船、乘船、已经渡船；60-220字；语义维度：choice-consequence、instruction-following |
| 4 | `village` | 我过桥后进村询问昨夜怪声来自哪个方向，并观察村民提到那个方向时是否害怕；请完成询问结果。 | 不得含找到村民、正准备询问、准备问；100-320字；语义维度：narrative-coherence、response-completeness |
| 5 | `temple` | 我沿村民指出的方向来到破庙，检查供桌后的脚印；只写看到的脚印，不预设属于妖怪。 | 必须含脚印；不得含属于妖怪、妖怪脚印；80-240字；语义维度：uncertainty-handling、player-agency |
| 6 | `establish-guide` | 我确认同行向导叫清禾，她熟悉黑风岭，请记住。 | 必须含清禾、黑风岭；10-80字；语义维度：fact-establishment、naturalness |
| 7 | `correct-guide` | 更正，向导不叫清禾，叫明月；她仍然熟悉黑风岭。 | 必须含明月、黑风岭；不得含清禾；10-80字；语义维度：correction-handling、response-completeness |
| 8 | `mountain` | 我和明月翻越黑风岭，遇到暴雨时先找安全处避雨。 | 必须含明月；不得含清禾；80-260字；语义维度：history-continuity、action-consequence |
| 9 | `shelter` | (generated from intent: 在避雨处检查商队遗落的货箱和车辙，只描述当前能够看到的内容。) | 80-260字；语义维度：non-invention、narrative-coherence |
| 10 | `wrong-theory` | 我猜商队只是自己迷路了，并没有被抓走。请根据目前剧情回应，不要顺着我下定论。 | 不得含你打开货箱、你继续前进、你走进山洞、商队就是迷路；60-240字；语义维度：uncertainty-handling、non-railroading、no-scene-advancement |
| 11 | `cave` | 我和明月循着已经发现的方向进入山洞，寻找失踪商队；承接进洞后的眼前场景。 | 必须含明月；不得含清禾；80-260字；语义维度：history-continuity、paced-progression |
| 12 | `scout` | 24字内承接：我藏好青铜铃，观察守卫和商队位置，不发动救援。 | 必须含青铜铃；10-30字；语义维度：instruction-following、player-agency |
| 13 | `reload-recall` | 重整行装后说出向导姓名、我带的物品和我们正在寻找谁；完整回答这三项即可。 | 必须含明月、青铜铃、商队；不得含清禾；10-120字；语义维度：long-term-continuity、correction-handling、response-completeness |
| 14 | `waterfall` | 我暂不正面冲突，和明月寻找瀑布水幕后可能通向山洞侧面的入口；请写完眼前结果。 | 必须含明月；不得含清禾、不对、重新来、bronze；80-260字；语义维度：player-agency、spatial-continuity |
| 15 | `diversion` | 我取回青铜铃，在侧门外摇铃引开守卫，让明月去解开商队绳索。 | 必须含青铜铃、明月；不得含清禾；80-260字；语义维度：choice-consequence、history-continuity |
| 16 | `rescue` | 守卫离开后，我进洞接应明月，解开剩余绳索并带商队离开石牢；确认救援完成，但不要跳到回村。 | 必须含明月、商队；不得含快被解开、正在解开、准备解开、回到村庄；80-260字；语义维度：paced-progression、response-completeness |
| 17 | `return-choice` | 离开山洞后我不走危险的旧索桥，选择绕远路护送商队；先写踏上绕行路，不要提前抵达村庄。 | 不得含走上旧索桥、踏上旧索桥、通过旧索桥、回到村庄、抵达村庄、走到村口、抵达村口；60-220字；语义维度：choice-consequence、instruction-following |
| 18 | `night-camp` | 绕路途中我先扎营，再问获救商人：破庙怪声是否与商队失踪有关？此前没有确认因果，不知道就明确说无法确认。 | 不得含就是小妖、正是小妖、确认有关、确实有关；80-280字；语义维度：uncertainty-handling、narrative-coherence |
| 19 | `recap` | 回村前用一句话说清楚：明月是谁、青铜铃做了什么、商队现在怎样。 | 必须含明月、青铜铃、商队；不得含清禾；20-140字；语义维度：long-term-continuity、response-completeness |
| 20 | `return` | 我与明月护送商队返回村庄，请用一句话收束这一回，不要开启新任务。 | 必须含明月、商队；不得含清禾、新任务、下一回、我与明月、我护送商队；20-220字；语义维度：ending-quality、history-continuity、instruction-following |

Run:

```sh
make test-e2e RAID=journey-guide PARALLEL=2
```
