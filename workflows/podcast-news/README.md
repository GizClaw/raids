# News Podcast (`podcast-news`) — 新闻播客

“开始” opens 《正声新闻》 with the current Beijing date/time, 程正声's introduction,
a brief warm-up and a question about the listener's interests. The clock comes
from the runtime, and the welcome is recorded once in Workspace State; loops,
answers and resume do not repeat it. Naming a subject directly starts playback
with that same first welcome. The host first scans recent news and gives
a brief overview, then automatically explores each story's additional facts,
background and attributed mainstream-media commentary. “停一下” pauses,
“继续” resumes, and “换成国际新闻” changes the subject.

An interruption such as “刚才那条消息已经发生了吗？” receives a brief factual
answer from the cached sources and recent narration. It keeps the topic and
queue, performs no new search, and waits for “继续” before resuming playback.
The news host uses Deploy's 程正声 (Winston), a middle-aged male announcer
marked for news broadcasting, with clear, steady Standard Mandarin:
MiniMax `Chinese (Mandarin)_Male_Announcer` with `speech-2.6-hd`, matching
Deploy's `gizclaw/catalogs/aigc/casts/winston/cast.yaml`.
The test listener uses Deploy's female 米雅 (Mia) cast,
`saturn_zh_female_keainvsheng_tob`, so the speakers are audibly distinct.

The delivery sounds like a news program, with natural transitions and an
occasional light, restrained line in the welcome or between topics. Humor does
not add judgments about the news or mock its subjects; serious stories remain
steady and factual. Facts take most of the airtime. A media comment is explicitly attributed to its
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
   dated events, preferring today's reports while retaining yesterday's latest
   reports so the midnight boundary does not discard the previous evening.
   The actual reporting date is spoken; yesterday is never presented as today.
   Internal collection records are never published or spoken.
   A bounded field-record parser treats quotes as data, ignores preambles and
   rejects unfinished records. Date, source and event checks follow.
2. **Overview:** briefly present each event's core fact with its source and date.
3. **Explore:** reuse cached additional facts and attributed comments, one event
   per section, keeping unspoken cached facts for later sections of the same
   story. Each section consumes at most two facts and one attributed comment.
   If any story lacks a sourced media comment, supplement the whole
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
chronological order, so primary report dates are checked against today's and
yesterday's Beijing dates, with today's reports first.

The overview is about 200–300 Chinese characters; each deeper section is about
150–200. Exhausted details produce a short transition and trigger the next
batch scan. If that scan has no reliable new news, playback waits for new
listener input rather than filling airtime with repetition or fabricated
content. A batch with usable content continues
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
implements that fix and is included in v0.31.7. A partially delivered section
must not advance the durable cursor; resuming can restart that incomplete
section. [GizClaw #1516](https://github.com/GizClaw/gizclaw/pull/1516) renews the
bounded Tool budget per generation, also released in v0.31.7. The Workflow
requires v0.31.7 or later. Bounded playback and dialogue acceptance remain
separate from qualification of durable original-queue recovery and unlimited
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
bound only in `testing`, with the female listener voice. The host first
asks what the listener wants. Its actual reply audio is sent to the persona;
the persona generates an interest reply, and that reply's audio starts the news
host. No topic reply is prerecorded in the Giztest. The persona then hears the
captured narration audio and asks a factual question. The host's answer is sent
back to the persona, which naturally acknowledges the explanation or thanks
the host. Giztest cleanup then stops both Workspaces.
Its dialogue phase persists between these finite responses.
The listener speaks like an ordinary person: the interest reply is at most
12 characters, a single factual question at most 24, and an acknowledgment at
most eight. It avoids repeating the news, listing listening requirements or
summarizing the host's answer. A final script emits “继续” and “停一下” exactly
for those control phases, preserving the model's other short replies.
If a model reply exceeds its phase's length bound, the script uses a complete
short interest reply, source question or acknowledgment rather than truncating
a sentence. Both dialogue scenarios check these response lengths against actual
model output.
With Giztest v0.31.8 or later, run the interruption scenario with
`gizclaw test run tests/giztest/dialogue/podcast-news-question.eino.giztest.yaml --output /path/to/new-report-directory`
to export a standalone HTML recording of the opening question and interest
reply, continuous narration, a spoken interruption, a finite factual answer
and the listener's response. Each handoff sends the actual captured response audio to
the other Workspace for PTT recognition. Spoken test instructions are excluded.
Short spoken replies are forwarded at their normal 20 ms packet pacing.
PTT receipts contain an ASR transcript stream as well as the narration stream.
The companion
`podcast-news.eino.giztest.yaml` first checks that the listener's spoken subject
choice starts news playback, then keeps one receiving stream open for 210 seconds
and records all narration audio. This startup check catches a failed search or
misclassified interest reply before the long listening window. Natural choices
such as “就听科技新闻” are normalized before topic classification.
A loopback audio-tail bridge decodes that same
capture, retains its last 20 seconds and calls `server.speech.transcribe` for the
persona's next question. It uses the audio that was actually received, rather
than a predefined question or text generated ahead of audible playback. The
bounded tail also stays within the Server's 60-second transcription limit.
The question and answer use native `workspace_relay` with incremental text
forwarding and audio EOS completion. Both Workflows speak with their bound
Voices; the question starts reaching the host while the listener generates it.
Three turns complete the question, host answer and short acknowledgment.
Actual captured audio and PTT start playback, carry “继续” and finally carry
“停一下”. After sustained narration, the host
must switch to one finite factual answer. The v0.31.5 Server answered the
question but did not produce the newer runner's `interrupt_observed` marker;
that marker is not treated as proof of interruption on this deployment.
After the factual answer, the persona hears
the explanation and says “继续”; that audio is sent to the host, and the test
requires another 120 seconds of continuous narration. It extracts and
transcribes that capture's new 20-second tail, then performs a second generated
question, host answer and acknowledgment. The persona's resume phase rearms
question generation, so the second question uses the newly received news.
History recovery counts a short follow-up after resuming even without a question
mark, including “请重复一遍”. The response to that clarification is acknowledged
in the answer phase rather than incorrectly starting another question phase.
After a second spoken “继续”, another 60-second narration window is required.
It then sends the persona's spoken “停一下” and checks
that playback stays quiet. Text relay exposes per-client text metrics and
whole-relay audio bytes; it has no per-client audio-byte assertion fields.
The exported recording retains the question, answer and acknowledgment audio
with their client and stream identities for verification.
Run this file with `--output` for the long report.
Start the bridge from `scripts/test/chat-assistant` with
`CGO_ENABLED=0 go run -mod=readonly ./cmd/news-audio-tail`, using the same
`GIZCLAW_TEST_ENDPOINT` and `GIZCLAW_TEST_REGISTRATION_TOKEN`. Set
`GIZCLAW_TEST_TAIL_ENDPOINT` to the loopback URL printed at startup. Native
Giztest starts an asynchronous `/tail/start` job, keeps recording the host for
25 seconds, then reads `/tail/<job_id>`. The bridge generates neither news nor answers.
`ffmpeg` is required to decode the captured Ogg/Opus. The bridge's temporary
Peer uses only speech RPC, has no Workflow, and is deleted during finalization.
Continuous recording across receive windows requires a Go CLI containing the
active-Opus bootstrap fix in [GizClaw #1537](https://github.com/GizClaw/gizclaw/pull/1537).
The test build uses v0.33.1 plus that unreleased client fix. The recording
renderer and its acceptance data remain native Giztest output. The published
v0.33.1 CLI misses the earlier audio BOS when opening a new mid-stream receive
window; its failed receipt remains separate evidence.

The 210/120/60-second playback and spoken-dialogue gates run first. Underrun and
buffer assertions keep their zero-underrun/nonnegative-buffer requirements and
run after the dialogue. A pacing regression can therefore be recorded without
hiding later interruption behavior; it still marks the native report failed.
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
