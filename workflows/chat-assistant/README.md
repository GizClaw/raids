# Chat Assistant (`chat-assistant`) — 聊天助手

- Category: `assistant`; rating: `all`; tags: `assistant`, `memory`, `scheduling`

## Implementations

| File | Workflow ID | Engine | Memory layout | Model slots | Voice slots |
| --- | --- | --- | --- | --- | --- |
| `flowcraft.yaml` | `flowcraft-chat-assistant` | flowcraft | user-chat-with-assistant | `flowcraft-chat-assistant.model` | `flowcraft-chat-assistant.assistant` |

Install an implementation into a RuntimeProfile with `raids install chat-assistant --impl <engine> --profile <file> --collection <name> --set model.<alias>=<model id> --set voice.<alias>=<voice id>`; the slots above are the parameters the installer asks for.


## Testing

Tester: `test.yaml` (`chat-assistant-test`, eino), shared by every implementation; one Giztest scenario per implementation:

- `tests/giztest/chat-assistant/flowcraft.giztest.yaml` (relay, with reload, timeout 52m)

The route has 12 target responses:

| # | Checkpoint | Player message | Contract |
| --- | --- | --- | --- |
| 1 | `establish-trip` | 我下周三要去杭州见周宁，车次是G7331，请记住；用一句自然口语复述这四项，不要标签或追问。 | 不得含需要我、要不要、是准备、还是、吗、呀、时间：、目的地：、会见对象：、车次：；语义维度：fact-establishment、naturalness |
| 2 | `establish-purpose` | 这次是讨论青桥项目，会议在下午两点开始；只确认项目和时间，不要复述其他行程。 | 必须含青桥、两点；不得含需要我、要不要、G7331、杭州、周宁；语义维度：fact-establishment、response-completeness |
| 3 | `correct-destination-train` | 更正一下，不是杭州，是苏州；车次也改成G7105。新值覆盖旧值，只复述这两个新值。 | 必须含苏州、G7105；不得含杭州、G7331、周宁、青桥、两点、需要我、还需要、要不要；语义维度：correction-handling、response-completeness |
| 4 | `short-encouragement` | 先用不超过10个字鼓励我，不要谈行程。 | 不得含苏州、杭州、G7105、G7331、周宁；至多10字；语义维度：instruction-following、relevance |
| 5 | `exact-answer` | 只回答“收到”，不要加其他内容。 | 必须含收到；至多2字；语义维度：instruction-following |
| 6 | `challenge-stale-trip` | 我是不是还是去杭州坐G7331？请按最新事实直接纠正我。 | 必须含苏州、G7105；不得含仍去杭州、还是杭州、车次仍是G7331、还是G7331、对的、没错；至多30字；语义维度：correction-handling、non-sycophancy |
| 7 | `partial-recall` | 只告诉我见谁、谈什么项目，不要复述其他信息。 | 必须含周宁、青桥；不得含苏州、G7105、两点；至多20字；语义维度：history-continuity、instruction-following |
| 8 | `correct-day-time` | 日期也更正为下周四，会议时间从下午两点改到下午三点。 | 必须含下周四、三点；不得含下周三、两点、需要我、要不要、核对一遍；语义维度：correction-handling |
| 9 | `unrelated-turn` | 8个字以内提醒我早点休息，不要提行程。 | 不得含苏州、G7105、周宁、青桥；至多8字；语义维度：instruction-following、relevance |
| 10 | `reload-recall` | 35个字以内完整告诉我：哪天、去哪、见谁、坐哪趟车、几点、谈什么项目。 | 必须含下周四、苏州、周宁、G7105、三点、青桥；不得含下周三、杭州、G7331、两点；至多35字；语义维度：long-term-continuity、correction-handling、response-completeness |
| 11 | `compact-recall` | 20个字以内只说目的地、联系人和车次。 | 必须含苏州、周宁、G7105；不得含杭州、G7331；至多20字；语义维度：instruction-following、history-continuity |
| 12 | `final-confirmation` | 最后只回答“行程已更新”，不要加标点或解释。 | 必须含行程已更新；至多6字；语义维度：instruction-following |

Run:

```sh
make test-e2e RAID=chat-assistant PARALLEL=2
```
