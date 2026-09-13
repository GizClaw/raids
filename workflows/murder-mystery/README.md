# Rainy Night Phonograph (Murder Mystery) (`murder-mystery`) — 雨夜留声机（剧本杀）

Long-form detective mystery with free investigation, testimony checks, evidence corrections, and a provisional conclusion.

- Category: `adventure`; rating: `12+` (mystery-death); tags: `murder-mystery`, `deduction`, `role-play`

## Implementations

| File | Workflow ID | Engine | Memory layout | Model slots | Voice slots |
| --- | --- | --- | --- | --- | --- |
| `flowcraft.yaml` | `flowcraft-murder-mystery` | flowcraft | adventure | `flowcraft-murder-mystery.model` | `.game-master`, `.housekeeper`, `.chef`, `.heir`, `.lawyer` |
| `eino.yaml` | `eino-murder-mystery` | eino | adventure | `eino-murder-mystery.model` | `.game-master`, `.housekeeper`, `.chef`, `.heir`, `.lawyer` |

Install an implementation into a RuntimeProfile with `raids install murder-mystery --impl <engine> --profile <file> --collection <name> --set model.<alias>=<model id> --set voice.<alias>=<voice id>`; the slots above are the parameters the installer asks for.


## 小剧场选角与分工

仍属 `adventure`，保留 **12+ / mystery-death**。两个引擎每轮只发一种声音：Flowcraft 条件边选择独立节点；Eino 上游 Starlark 写 `selected_speaker`，唯一 primary chat_model 按身份 prompt 输出，`state_voices` 选择同一角色音色，保留 ASR。

| role / 别名 | 场景行动与边界 | 两引擎完整 Voice 槽位 | Voice resource_id |
| --- | --- | --- | --- |
| `narrator` 主持人 | 开场主持、证据核对、更正、推理、暂定指控与结案；不代演证人 | `flowcraft-murder-mystery.game-master` / `eino-murder-mystery.game-master` | `volc-tenant:volc-cn-beijing:zh_male_changtianyi_mars_bigtts` |
| `housekeeper` 管家 | 管家/老管家：受访时交代门厅位置与主钥匙，未知声响和开门过程明确不知道 | `flowcraft-murder-mystery.housekeeper` / `eino-murder-mystery.housekeeper` | `volc-tenant:volc-cn-beijing:ICL_zh_male_youmodaye_tob` |
| `chef` 厨师 | 厨师/大厨：受访时交代20:50至来电后揉面，自述不是物证 | `flowcraft-murder-mystery.chef` / `eino-murder-mystery.chef` | `volc-tenant:volc-cn-beijing:ICL_zh_male_hanhoudunshi_tob` |
| `heir` 沈知秋 | 沈知秋/次子：受访时只答次子身份、回房拿烟与不清楚鞋印 | `flowcraft-murder-mystery.heir` / `eino-murder-mystery.heir` | `volc-tenant:volc-cn-beijing:ICL_zh_male_qingshuangshaonian_tob` |
| `lawyer` 律师 | 律师：受访时厘清上周修改遗嘱及知情者，不知道当晚是否谈过 | `flowcraft-murder-mystery.lawyer` / `eino-murder-mystery.lawyer` | `volc-tenant:volc-cn-beijing:zh_male_jieshuoxiaoming_uranus_bigtts` |

本案保持自由调查，不新增线性章节。开场只列可采访人物；随后按玩家选择进入单独采访场景，四证人不同时登场、不轮流抢话，沈清如和死者不新增可采访身份或证词。角色名单恢复时按当前角色表归一化，丢弃旧名单；已有鞋印更正仍沿用原权威状态。

点名示例：“我去问厨师：停电前后你在哪里？”、“管家”（只报名字也是选择）、“请先让律师说说，再让厨师说说”（本轮只选律师）、“不要让管家回答，请让厨师说说”（选厨师）。开场、转场、更正、安全、物品调查、证据核对和结案优先主持人；询问沈知秋房间不会误选沈知秋。匿名追问默认主持人，继续证人采访时请再点名。

证人直接第一人称回答，不加“某某说/某某：”标签，只读自己的固定证词与已公开对话；不会收到主持人完整来源表、私密真相或原始召回笔记。Flowcraft 在调用前及回合结束时清理 channel 的 system/非文本消息，证人路径清空旧摘要；Eino 只把 user/assistant 公开正文作为 history 传给模型。主持人只在实际检查时披露对应来源；暂定指控厨师并要求反驳的复合回合仍先明确暂定，再第三人称转述固定厨师否认。

离线校验能验证路由与 Voice 绑定，不能证明供应商开通、真实延迟或音质；在线 E2E、实际 Voice 日志与试听需另行执行。

## Testing

Tester: `test.yaml` (`murder-mystery-test`, eino), shared by both implementations; the same 26 checkpoints and leakage guards run for each engine:

- `tests/giztest/murder-mystery/{flowcraft,eino}.giztest.yaml`: 26-response relay, with reload, timeout 99m.
- `{flowcraft,eino}.roles.giztest.yaml`: five isolated Workspaces per engine; witnesses receive the unchanged opening before their interview. Complete text/audio EOS and nonempty audio, plus 2s text / 3s audio first-response gates.
- `{flowcraft,eino}.transitions.giztest.yaml`: seven turns covering name-only choice, witness knowledge boundary, negative naming/order, host accusation, unavailable witness and correction.
- `routing-cases.json`: 77 shared offline cases, including every original checkpoint and legacy role normalization.

The route has 26 target responses:

| # | Checkpoint | Player message | Contract |
| --- | --- | --- | --- |
| 1 | `opening` | 请开始主持《雨夜留声机》，只给出初始案情和自由调查邀请。 | 必须含22:00、沈鹤年、二楼书房、雨夜、自由调查，并列出可问话的管家、厨师、沈知秋、律师和可查看的阳台、厨房、花园、壁炉、后廊；不得含留声机、唱片、遗嘱、木蜡、鞋印、钥匙、细线、下起雨夜、管家巡查、撞开、推开、书房门、壁灯、烟草、纸张、开了门、侦探、受邀、报案、赶到现场；至多200字 |
| 2 | `inspect-balcony` | 我先去阳台看看，仔细检查窗沿、地面和排水口。 | 不得含阳台地面没有发现异常、地面没有异常、地面没有发现痕迹、地面没有痕迹；至多420字 |
| 3 | `inspect-window` | 顺着你刚才说的，我再细查窗框、玻璃和排水口有没有异样。 | 不得含没有其他异常、其他异常、没有遗漏、没有其他漏掉、没有额外发现、没有其他痕迹、没有额外收获、异常痕迹；至多360字 |
| 4 | `interview-chef` | 我去问厨师：停电前后你分别在哪里？具体时间记得吗？ | 证人直接第一人称，无说话人标签；至多420字 |
| 5 | `inspect-kitchen` | 我去厨房和后门核对一下厨师的说法。 | 不得含没有其他相关发现、没有额外收获；至多420字 |
| 6 | `interview-housekeeper` | 我找管家问问：停电时你在哪里？钥匙在谁手里？有没有听到什么声响？ | 证人直接第一人称，无说话人标签；不得含来电后没多久、喊着众人、一起开了门；至多420字 |
| 7 | `inspect-study` | 我去书房调查书桌、门窗，以及死者当晚活动过的物品。 | 不得含你要看看、要不要检查、是否要检查、建议检查、没有其他异常、其他异常、没有发现死者额外、没有发现额外的相关活动物品、没有发现相关活动物品；至多420字 |
| 8 | `establish-shoe-size` | 我刚收到外部鉴定报告：此前提到的同源鞋印尺码都是42码。请把这份报告作为已确认线索，并明确复述一次。 | 必须含42；不得含后廊、更正；至多100字 |
| 9 | `interview-heir` | 我去找沈知秋，问他和死者的关系、当晚行踪，以及他是否知道那些鞋印。 | 证人直接第一人称，无说话人标签；不得含公开的固定关系矛盾、没说过和沈鹤年、没有公开矛盾、没有矛盾；至多420字 |
| 10 | `inspect-phonograph` | 我去检查留声机，看看它和案发时间线有什么关系。 | 不得含起到误导死亡时间的作用、确认用于误导死亡时间、就是用来误导死亡时间；至多360字 |
| 11 | `irrelevant-garden-route` | 我去花园看看水池和围墙附近有没有线索。 | 不得含我查看、我检查、我调查、落叶、泥土、攀爬、翻越；至多280字 |
| 12 | `mistaken-outage-theory` | 我觉得停电可能只是普通的线路故障，未必和案件有关，你怎么看？ | 不得含后廊、湿鞋印、书房锁具、细线纤维、拉扯磨痕、操作密室、所有证词都显示、无人在书房附近、死亡正好发生在、死亡发生在21:10、死于21:10；至多360字 |
| 13 | `correct-shoe-size` | 更正此前提到的同源鞋印鉴定结果：它们的尺码都应从旧值统一更正为39码。新结果覆盖旧结果；确认时只说39码，不要再复述旧号码。 | 必须含39；不得含42码、后廊；至多100字 |
| 14 | `inspect-heir-room` | 我去沈知秋的房间看看，重点检查鞋柜。 | 必须含39；不得含鞋印为42码、鞋印是42码、42码的鞋印、本案纤维、同批的细钓鱼线、现场钓鱼线；至多420字 |
| 15 | `inspect-fireplace` | 我去检查壁炉，看看里面和周围的灰尘。 | 不得含主钥匙备用钥匙；至多360字 |
| 16 | `interview-lawyer` | 我去问律师：遗嘱最近有没有修改？还有谁知道内容？ | 证人直接第一人称，无说话人标签；必须含不清楚；至多420字 |
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
