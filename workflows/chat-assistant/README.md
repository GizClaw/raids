# Chat Assistant (`chat-assistant`) — 聊天助手

- Category: `assistant`; rating: `preschool`, `child`, `teen`, `adult`, `senior`; tags: `assistant`, `memory`, `scheduling`, `web-search`

## Workspace safety fence

The player prompt starts with `{safety_fence}`, then a blank line and the
scenario instructions. With empty fence text, only two leading newlines remain. Internal routing/memory nodes and
Tester Workflows do not receive the variable. See the root
[contract and GizClaw compatibility requirement](../../README.md#workspace-safety-fence).

## Implementations

| File | Workflow ID | Engine | Memory layout | Model slots | Voice slots |
| --- | --- | --- | --- | --- | --- |
| `eino.yaml` | `eino-chat-assistant` | eino | user-chat-with-assistant | `eino-chat-assistant.model` | `eino-chat-assistant.assistant` |

Install the Workflow resource and add a flat `spec.workflows` binding to its Workflow ID. Bind the slots above under `spec.resources.models` and `spec.resources.voices`; use `category:*` tags for discovery.

Both public profiles bind it as `spec.workflows.general-assistant`
(聊天助手), tagged `category:assistants`. It bound `flowcraft-chat-assistant` until the
Flowcraft implementation was removed, so a consumer that overrides that alias
or keys assets by Workflow ID must switch to `eino-chat-assistant`.

It is a plain ASR → LLM → TTS pipeline: the shared `asr` Model transcribes
speech, `eino-chat-assistant.model` answers, and the Voice adapter speaks the
reply. It recalls and observes `user-chat-with-assistant` memory, and it can
search the web.

The asynchronous observation includes both the captured user input and the
generated assistant reply, so confirmed facts present in the reply remain
available to the existing Memory layout.

## Web search

`spec.toolkit.tool_ids` allows one Tool, `volc-web-search`
([`tools/volc-web-search.yaml`](../../tools/volc-web-search.yaml), runtime name
`web_search`); the RuntimeProfile must bind it under `resources.tools`
(`web-search` in both public profiles). The Model decides when to search. The
system prompt tells it to search for current weather/date queries, news,
sports, prices and uncertain facts. User-supplied facts to remember, confirm or
correct are answered directly, including future plans and dates; confirmations
contain only the requested new fields. Chat, common knowledge and facts already
in the conversation or memory are answered directly. Before a
search it says one short phrase such as “我查一下。” in the same reply as the
tool call; Eino streams that text before running the Tool, so the user hears
it while the search and the second Model round run. The Model must support
tool calls.

The Tool posts `{Query, SearchType: "web", Count: 3}` to Volcengine's Doubao
Search Custom API, plus `TimeRange` when the Model sets `time_range` for
“最近/最新” questions (results are ranked by relevance, not date). Omission or
JSON null means no publication-time filter; invalid ranges remain rejected.
Authentication uses the `search_api_key` from `volc-credential`
(`GIZCLAW_VOLC_SEARCH_API_KEY`). A searched turn costs one extra Model round
plus the search (about 1s) and adds 5–25K prompt tokens of results. A timeout
(10s) returns an error result to the Model. A malformed call, a non-200
response or a response over 1 MiB fails the turn. Eino gets no clock input, so
the Model takes dates from search results.

## Testing

Ordinary replies have no fixed character ceiling. Upper-bound checks apply only
to a user request that explicitly limits characters or requires exact wording;
content, memory, response timing and audio completion checks still apply.

Tester: `test.yaml` (`chat-assistant-test`, eino); one Giztest scenario per tier:

- `tests/giztest/soak/chat-assistant.eino.giztest.yaml` (relay, with reload, timeout 52m)

The quality tier also checks web search live: it asks for Shanghai's weather
and today's date and fails on missing weather/date words, an offline refusal
such as “无法联网”, or a first text later than 15s. Those two probes need
`tools/volc-web-search.yaml`, the testing profile's `web-search` binding and a
`search_api_key` in `volc-credential`.

The live weather/date keyword checks establish spoken response availability;
they do not prove that search executed. `make test-unit-chat-assistant` also
runs those same inputs through the shipped graph and real HTTP Tool executor
with a scripted Model and controlled HTTP result. It checks one actual request,
the mapped query and Count, the pre-search phrase, and the exact unpredictable
result in the answer; an invented weather/date response without a request
fails that oracle. The same target checks both user and assistant observation
and that a casual turn sends no search request.

The route has 12 target responses:

| # | Checkpoint | Player message | Contract |
| --- | --- | --- | --- |
| 1 | `establish-trip` | 我下周三要去杭州见周宁，车次是G7331，请记住；用一句自然口语复述这四项，不要标签或追问。 | 不得含需要我、要不要、是准备、还是、吗、呀、时间：、目的地：、会见对象：、车次：；语义维度：fact-establishment、naturalness |
| 2 | `establish-purpose` | 这次是讨论青桥项目，会议在下午两点开始；只确认项目和时间，不要复述其他行程。 | 必须含青桥、两点；不得含需要我、要不要、G7331、杭州、周宁；语义维度：fact-establishment、response-completeness |
| 3 | `correct-destination-train` | 更正一下，不是杭州，是苏州；车次也改成G7105。新值覆盖旧值，只复述这两个新值。 | 必须含苏州、G7105；不得含杭州、G7331、周宁、青桥、两点、需要我、还需要、要不要；语义维度：correction-handling、response-completeness |
| 4 | `short-encouragement` | 先用不超过10个字鼓励我，不要谈行程。 | 不得含苏州、杭州、G7105、G7331、周宁；用户要求至多10字；语义维度：instruction-following、relevance |
| 5 | `exact-answer` | 只回答“收到”，不要加其他内容。 | 必须含收到；用户要求至多2字；语义维度：instruction-following |
| 6 | `challenge-stale-trip` | 我是不是还是去杭州坐G7331？请按最新事实直接纠正我。 | 必须含苏州、G7105；不得含仍去杭州、还是杭州、车次仍是G7331、还是G7331、对的、没错；语义维度：correction-handling、non-sycophancy |
| 7 | `partial-recall` | 只告诉我见谁、谈什么项目，不要复述其他信息。 | 必须含周宁、青桥；不得含苏州、G7105、两点；语义维度：history-continuity、instruction-following |
| 8 | `correct-day-time` | 日期也更正为下周四，会议时间从下午两点改到下午三点。 | 必须含下周四、三点；不得含下周三、两点、需要我、要不要、核对一遍；语义维度：correction-handling |
| 9 | `unrelated-turn` | 8个字以内提醒我早点休息，不要提行程。 | 不得含苏州、G7105、周宁、青桥；用户要求至多8字；语义维度：instruction-following、relevance |
| 10 | `reload-recall` | 35个字以内完整告诉我：哪天、去哪、见谁、坐哪趟车、几点、谈什么项目。 | 必须含下周四、苏州、周宁、G7105、三点、青桥；不得含下周三、杭州、G7331、两点；用户要求至多35字；语义维度：long-term-continuity、correction-handling、response-completeness |
| 11 | `compact-recall` | 20个字以内只说目的地、联系人和车次。 | 必须含苏州、周宁、G7105；不得含杭州、G7331；用户要求至多20字；语义维度：instruction-following、history-continuity |
| 12 | `final-confirmation` | 最后只回答“行程已更新”，不要加标点或解释。 | 必须含行程已更新；用户要求至多5字；语义维度：instruction-following |

Run:

```sh
make test-e2e RAID=chat-assistant PARALLEL=2
```
