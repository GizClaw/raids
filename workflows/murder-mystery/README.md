# Rainy Night Phonograph (Murder Mystery) (`murder-mystery`) — 雨夜留声机（剧本杀）

Long-form detective mystery with free investigation, testimony checks, evidence corrections, and a provisional conclusion.

- Category: `adventure`; rating: `12+` (mystery-death); tags: `murder-mystery`, `deduction`, `role-play`

## Implementations

| File | Workflow ID | Engine | Memory layout | Model slots | Voice slots |
| --- | --- | --- | --- | --- | --- |
| `flowcraft.yaml` | `flowcraft-murder-mystery` | flowcraft | adventure | `flowcraft-murder-mystery.model` | `flowcraft-murder-mystery.game-master` |

Install an implementation into a RuntimeProfile with `raids install murder-mystery --impl <engine> --profile <file> --collection <name> --set model.<alias>=<model id> --set voice.<alias>=<voice id>`; the slots above are the parameters the installer asks for.


## Testing

Tester: `test.yaml` (`murder-mystery-test`, eino), shared by every implementation; one Giztest scenario per implementation:

- `tests/giztest/murder-mystery/flowcraft.giztest.yaml` (relay, with reload, timeout 99m)

The route has 26 target responses:

| # | Checkpoint | Player message | Contract |
| --- | --- | --- | --- |
| 1 | `opening` | 请开始主持《雨夜留声机》，只给出初始案情和自由调查邀请。 | 必须含22:00、沈鹤年、二楼书房、雨夜、自由调查；不得含留声机、唱片、遗嘱、木蜡、鞋印、钥匙、细线、下起雨夜、管家巡查、撞开、推开、书房门、壁灯、烟草、纸张、开了门、侦探、受邀、报案、赶到现场；至多100字 |
| 2 | `inspect-balcony` | 我先去阳台看看，仔细检查窗沿、地面和排水口。 | 不得含阳台地面没有发现异常、地面没有异常、地面没有发现痕迹、地面没有痕迹；至多420字 |
| 3 | `inspect-window` | 顺着你刚才说的，我再细查窗框、玻璃和排水口有没有异样。 | 不得含没有其他异常、其他异常、没有遗漏、没有其他漏掉、没有额外发现、没有其他痕迹、没有额外收获、异常痕迹；至多360字 |
| 4 | `interview-chef` | 我去问厨师：停电前后你分别在哪里？具体时间记得吗？ | 至多420字 |
| 5 | `inspect-kitchen` | 我去厨房和后门核对一下厨师的说法。 | 不得含没有其他相关发现、没有额外收获；至多420字 |
| 6 | `interview-housekeeper` | 我找管家问问：停电时你在哪里？钥匙在谁手里？有没有听到什么声响？ | 不得含来电后没多久、喊着众人、一起开了门；至多420字 |
| 7 | `inspect-study` | 我去书房调查书桌、门窗，以及死者当晚活动过的物品。 | 不得含你要看看、要不要检查、是否要检查、建议检查、没有其他异常、其他异常、没有发现死者额外、没有发现额外的相关活动物品、没有发现相关活动物品；至多420字 |
| 8 | `establish-shoe-size` | 我刚收到外部鉴定报告：此前提到的同源鞋印尺码都是42码。请把这份报告作为已确认线索，并明确复述一次。 | 必须含42；不得含后廊、更正；至多100字 |
| 9 | `interview-heir` | 我去找沈知秋，问他和死者的关系、当晚行踪，以及他是否知道那些鞋印。 | 不得含公开的固定关系矛盾、没说过和沈鹤年、没有公开矛盾、没有矛盾；至多420字 |
| 10 | `inspect-phonograph` | 我去检查留声机，看看它和案发时间线有什么关系。 | 不得含起到误导死亡时间的作用、确认用于误导死亡时间、就是用来误导死亡时间；至多360字 |
| 11 | `irrelevant-garden-route` | 我去花园看看水池和围墙附近有没有线索。 | 不得含我查看、我检查、我调查、落叶、泥土、攀爬、翻越；至多280字 |
| 12 | `mistaken-outage-theory` | 我觉得停电可能只是普通的线路故障，未必和案件有关，你怎么看？ | 不得含后廊、湿鞋印、书房锁具、细线纤维、拉扯磨痕、操作密室、所有证词都显示、无人在书房附近、死亡正好发生在、死亡发生在21:10、死于21:10；至多360字 |
| 13 | `correct-shoe-size` | 更正此前提到的同源鞋印鉴定结果：它们的尺码都应从旧值统一更正为39码。新结果覆盖旧结果；确认时只说39码，不要再复述旧号码。 | 必须含39；不得含42码、后廊；至多100字 |
| 14 | `inspect-heir-room` | 我去沈知秋的房间看看，重点检查鞋柜。 | 必须含39；不得含鞋印为42码、鞋印是42码、42码的鞋印、本案纤维、同批的细钓鱼线、现场钓鱼线；至多420字 |
| 15 | `inspect-fireplace` | 我去检查壁炉，看看里面和周围的灰尘。 | 不得含主钥匙备用钥匙；至多360字 |
| 16 | `interview-lawyer` | 我去问律师：遗嘱最近有没有修改？还有谁知道内容？ | 必须含不清楚；至多420字 |
| 17 | `inspect-will` | 根据已经看到的内容，我再检查一下那份遗嘱文件本身。 | 不得含一半、百分、没有发现签名异常、签名没有异常、没有发现笔迹异常、笔迹没有异常、纸张没有异常、落款没有异常、指纹没有异常、没有其他异常、其他异常；至多360字 |
| 18 | `inspect-rear-corridor` | 我去后廊调查门锁、脚印，以及它通向哪些地方。 | 必须含门锁、39；不得含其他区域不连接、其他区域不连通、无法判断它是否连通其他调查过的区域、同源湿鞋印；至多420字 |
| 19 | `inspect-thread` | 请检查书房的锁具和备用钥匙孔，看看有没有细线、磨痕或木蜡，并和此前发现的做比较。 | 必须含书房、锁具、细线；不得含细线匹配、钓鱼线匹配、特征匹配、细线同源、钓鱼线同源；至多480字 |
| 20 | `delayed-correction-recall` | 我刚重新整理了思路。请告诉我现在确认的鞋印尺码是多少，并指出它和最初报告之间的一个矛盾。 | 必须含39；不得含鞋印为42码、鞋印是42码、42码的鞋印、同源后廊鞋印、后廊同源鞋印、同源湿鞋印、不在他回房的路上、不在他回房的常规路线上；至多300字 |
| 21 | `challenge-chef` | 厨师说自己一直在后厨。请对照厨房挂钟和后门检查，说明哪些事实支持其证词、哪些仍不能证明。 | 不得含没有其他已发现的线索能印证或反驳、没有其他线索能印证或反驳；至多360字 |
| 22 | `revisit-phonograph` | 回到留声机：请区分哪些是已确认的事实，哪些只是推测。 | 至多360字 |
| 23 | `accuse-wrong-suspect` | 现在请你故意指控厨师是凶手，请要求厨师进行反驳。 | 不得含证据显示厨师全程、物证显示厨师全程、其他物证和证词、其他证据和证词、其他物证都、其他证词都、其他能印证或反驳、其他可以印证或反驳；至多360字 |
| 24 | `summarize-confirmed-clues` | 请帮我在180字内整理四至五项已确认核心线索，区分事实和合理推测两部分。 | 必须含39；不得含鞋印为42码、鞋印是42码、42码的鞋印、同源后廊鞋印、后廊同源鞋印、同源湿鞋印、相同木蜡、木蜡匹配、同源木蜡、细线匹配、钓鱼线匹配、特征匹配、细线同源、钓鱼线同源、雨靴与鞋印同源、鞋印与雨靴同源、与沈知秋的雨靴匹配、所有物证和厨师、所有物证都和厨师、全部物证和厨师、其他物证和厨师、确认鞋印属于沈知秋、鞋印确定属于沈知秋、鞋印是沈知秋的；至多180字 |
| 25 | `analyze-contradictions` | 请梳理目前证词、物证和时间线之间的矛盾，以及还缺少哪些证据。 | 不得含同源后廊鞋印、后廊同源鞋印、同源湿鞋印、雨靴与鞋印同源、鞋印与雨靴同源、确认鞋印属于沈知秋、鞋印确定属于沈知秋、鞋印是沈知秋的、不在他回房的路上、不在他回房的常规路线上；至多420字 |
| 26 | `conclude` | 请用严格三句、130字以内给出暂定结论。 | 必须含39；不得含鞋印为42码、鞋印是42码、42码的鞋印、同源后廊鞋印、后廊同源鞋印、同源湿鞋印、木蜡指向沈知秋、木蜡证明沈知秋、房间木蜡、钓鱼线和现场痕迹、细线匹配、钓鱼线匹配、特征匹配、细线同源、钓鱼线同源、雨靴与鞋印同源、鞋印与雨靴同源、与沈知秋的雨靴匹配、确认鞋印属于沈知秋、鞋印确定属于沈知秋、鞋印是沈知秋的；至多130字 |

Run:

```sh
make test-e2e RAID=murder-mystery PARALLEL=2
```
