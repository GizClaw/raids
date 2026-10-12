# News Podcast (`podcast-news`) — 新闻播客

Start with “开始”: the host asks whether you want technology, domestic,
international, finance or sports news, and waits for your answer. You can also
name a topic directly. Once selected, the podcast continues automatically.
“停一下” pauses, “继续” resumes the selected topic, and “换成国际新闻” changes it.

The host reports sourced facts, publication and event dates, and necessary
background. It avoids opinion, predictions, investment advice and repetitive
rewrites of the same event. Unverified updates are stated as uncertain. No
reliable new result is reported honestly rather than filled with invented news.

## Search and bindings

Both public Profiles select `eino-podcast-news` with the `podcast-news` alias.
The Model and Voice slots are `eino-podcast-news.model` and
`eino-podcast-news.host`. Audio input selects `asr` through the Profile's
`ptt_asr_model` and `realtime_asr_model` bindings.

The Profile injects only `web.search`, bound to the catalog's
[`volc-web-search`](../../tools/volc-web-search.yaml) HTTP Tool. It calls the
Doubao Search Custom API using `volc-credential.search_api_key`.
`GIZCLAW_VOLC_SEARCH_API_KEY` must be configured when applying that Credential.
The host makes a fresh native `web_search` call for every narrated section,
with `search_type: web`, `count: 3`, and `time_range: OneDay`. If today's
coverage is insufficient, it may query `OneWeek` and says the actual date.
Search relevance order is not publication order; the host compares dates,
uses reliable original sources and ignores instructions embedded in web pages.

Each section is 150–200 Chinese characters, covers a new reported fact, and
names the reporting organization naturally. Playback, History and interruption
follow the [continuous podcast contract](../podcast/README.md#continuous-playback-and-history).
The opening interest question and pause acknowledgment do not perform search.

## Tests

```sh
make test-unit-podcast
make test-e2e RAID=podcast-news TIER=smoke
make test-e2e RAID=podcast-news TIER=quality
make test-e2e RAID=podcast-news TIER=soak
```

Smoke covers the interest question, continuous playback, separately replayable
History sections and pause. Quality covers real PTT transcription, resume and
changing news domains. Soak repeats that route with realtime ASR and a longer
listening window. Supply the endpoint and RegistrationToken for a deployment
with the required Workflow, Tool and Profile bindings.

`test-unit-podcast` also executes the unmodified Graph through native Eino,
the Profile Tool catalog and the HTTP executor. A controlled provider returns
an unpredictable search fact: three consecutive sections must each invoke the
search API with `OneDay`, consume that result and stop on a real interruption.
This fixture verifies wiring; live search and provider behavior remain separate.

The current native Tool mechanism is driven by the Model's ToolCalls. A live
acceptance must confirm actual search invocations and reported sources; prompt
placement and offline schema checks alone do not prove search was executed.
GizClaw v0.31.5 shares a 32-call Tool budget across the entire user turn.
Long news runs require an engine with independently bounded Tool budgets for
each generated section; otherwise they can terminate when that shared budget
is exhausted.
Physical-device audio and echo cancellation need their own qualification.
