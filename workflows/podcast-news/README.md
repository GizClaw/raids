# News Podcast (`podcast-news`) — 新闻播客

“开始” asks which domain the listener wants and waits for an answer. Naming a
subject directly starts playback. The host first scans today's news and gives
a brief overview, then automatically explores each story's additional facts,
background and attributed mainstream-media commentary. “停一下” pauses,
“继续” resumes, and “换成国际新闻” changes the subject.

An interruption such as “刚才那条消息已经发生了吗？” receives a brief factual
answer from the cached sources and recent narration. It keeps the topic and
queue, performs no new search, and waits for “继续” before resuming playback.
The host and test listener both use 周怀远 (Arthur), the male cast selected as
Forge's article narrator in Deploy's `aigc/settings/voice_cast.json`:
`zh_male_ruyayichen_saturn_bigtts` with `seed-tts-2.0`.

Facts take most of the airtime. A media comment is explicitly attributed to its
organization and date and kept to one or two sentences; reporting a quotation
does not make it the outlet's own editorial position. Missing commentary is not
invented, and the host avoids adding its own opinions, predictions or investment
advice. Publication dates and event dates remain distinct.

## Batch search and playback

Both public Profiles inject only `news.search`, bound to
[`volc-news-search`](../../tools/volc-news-search.yaml). The Tool calls the
[Doubao Search Custom API](https://www.volcengine.com/docs/87772/2272953) with
`volc-credential.search_api_key`; configure `GIZCLAW_VOLC_SEARCH_API_KEY` when
applying that Credential. Ordinary assistant search keeps its existing Tool.

The graph separates collection from public narration:

1. **Scan once:** request ten `OneDay` results and collect up to five distinct,
   dated events. Internal collection records are never published or spoken.
   A bounded field-record parser treats quotes as data, ignores preambles and
   rejects unfinished records. Date, source and event checks follow.
2. **Overview:** briefly present each event's core fact with its source and date.
3. **Explore:** reuse cached additional facts and attributed comments, one event
   per section. If any story lacks a sourced media comment, supplement the whole
   batch
   once with ten `OneWeek` results. Never search once per playback section or
   once per cached event.
4. **Refill:** scan again only after consuming the queue. Previously covered
   events and facts remain excluded across batches and changes of domain.

The queue rejects duplicate normalized event identifiers, canonical article
URLs (including tracking variants), and identical brief content. A separate
ledger rejects facts already covered in an overview or earlier deep dive.
The collector also merges semantically equivalent reports; that semantic step
and source fidelity still require real-provider acceptance. Meaningful URL query
parameters such as article IDs are preserved. Search relevance order is not
chronological order, so dates are checked against the current Beijing date.

The overview is about 200–300 Chinese characters; each deeper section is about
150–200. No reliable new news or additional detail is reported honestly rather
than filling airtime with repetition or fabricated content. In that condition
playback waits for new listener input. A batch with usable content continues
automatically and is interruptible throughout.

## State and engine requirements

`bulletin` persists the topic, cached stories, cursor and seven days of covered
event/fact identities in the Workspace's Eino State store. Yesterday's remaining
queue is refreshed on the next iteration. Changing domains resets the queue
while preserving that ledger. Model and Voice slots are
`eino-podcast-news.model` and `eino-podcast-news.host`; PTT/realtime ASR select
`asr` from the Profile. Playback and History follow the
[continuous podcast contract](../podcast/README.md#continuous-playback-and-history).

Reliable pause/resume requires an engine that commits selected persistent State
**after each completely delivered generation and its History record**. GizClaw
v0.31.5 saves only at successful turn completion: interruption loses uncommitted
queue progress. [GizClaw #1517](https://github.com/GizClaw/gizclaw/pull/1517)
implements that fix and is included in v0.31.7. The Beijing E2E Server was still
v0.31.5 in the 2026-10-13 dual-Workflow run; its resume stage stopped early.
A partially delivered
section must not advance the durable cursor; resuming can
restart that incomplete section. v0.31.5 also shares a 32-call Tool budget across
one turn; [GizClaw #1516](https://github.com/GizClaw/gizclaw/pull/1516) renews the
bounded budget per generation, also released in v0.31.7. Deploy v0.31.7 or later
and verify pause/resume before claiming durable interruption/resume or unlimited
operation.

## Tests

```sh
make test-unit-podcast
make test-e2e RAID=podcast-news TIER=smoke
make test-e2e RAID=podcast-news TIER=quality
make test-e2e RAID=podcast-news TIER=soak
```

The unmodified Starlark scripts cover control, batch depletion, enrichment,
midnight refresh, date validation, event/URL/fact deduplication and restoration.
Native Eino executes the shipped Graph through the Profile catalog and real HTTP
executor with unpredictable fixture news. Contracts verify one search for an
overview plus three deep dives, refill only after exhaustion, cross-batch dedup,
one batch enrichment with attributed comments, interruption, and restoration
of a remaining queue with no search or repeated overview. The restoration test
starts from an existing snapshot; actual per-generation State commits belong to
the engine's SQL State/History tests and need deployed E2E verification.

Smoke checks real search, continuous text/audio, source dates, replayable History
and pause. Quality and soak add PTT/realtime ASR, resume and domain redirection.
[`test-persona.yaml`](test-persona.yaml) is a second, finite listener Workflow
bound only in `testing`, with the same Forge narrator voice. The host first
asks what the listener wants. Its actual reply audio is sent to the persona;
the persona generates an interest reply, and that reply's audio starts the news
host. No topic reply is prerecorded in the Giztest. The persona then hears the
captured narration audio and asks a factual question. The host's answer is sent
back to the persona, which naturally acknowledges the explanation or thanks
the host. Giztest cleanup then stops both Workspaces.
Its dialogue phase persists between these finite responses.
With Giztest v0.31.8 or later, run the interruption scenario with
`gizclaw test run tests/giztest/dialogue/podcast-news-question.eino.giztest.yaml --output /path/to/new-report-directory`
to export a standalone HTML recording of the opening question and interest
reply, continuous narration, a spoken interruption, a finite factual answer
and the listener's response. Each handoff sends the actual captured response audio to
the other Workspace for PTT recognition. Spoken test instructions are excluded.
Short spoken replies are forwarded at their normal 20 ms packet pacing.
PTT receipts contain an ASR transcript stream as well as the narration stream.
The companion
`podcast-news.eino.giztest.yaml` keeps one receiving stream open for 210 seconds
and records all narration audio. The persona receives the opening wording
captured from that same turn's actual text output and generates a factual
question about it. This long variant uses text for that handoff: replaying the
entire recording through the deployed short-utterance ASR timed out at
finalization. The listener's question, host answer and continuation request
still use actual captured audio and PTT. After sustained narration, the host
must switch to one finite factual answer. The v0.31.5 Server answered the
question but did not produce the newer runner's `interrupt_observed` marker;
that marker is not treated as proof of interruption on this deployment.
After the factual answer, the persona hears
the explanation and says “继续”; the test requires another 120 seconds of
continuous narration. It then sends the persona's spoken “停一下” and checks
that playback stays quiet. Run this file with `--output` for the long report.
It needs the v0.31.7 State fix. Both are separate from the standard
smoke/quality/soak inventory. Failed resume receipts remain valid failure
evidence, rather than qualifying the question-only run as durable resume.
Deliver the unmodified native `index.html` generated by Giztest. Its embedded
data and audio make it standalone; forwarded audio and parallel startup probes
remain visible in the native replay.
Supply a deployment endpoint and RegistrationToken with these bindings.
Search invocation counts and the overview/deep-dive order must also be checked
against real Server logs and captured History. Physical-device audio and echo
cancellation need separate qualification.
