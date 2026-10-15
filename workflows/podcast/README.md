# Continuous Podcast (`podcast`) — 连续播客

A Chinese podcast about everyday science. Say “开始” or specify a topic to
start. It keeps generating new content without asking whether to continue.
“停一下” pauses, “继续” resumes, and a new topic redirects the narration.

The public `default` and `testing` Profiles bind the `podcast` alias to
`eino-podcast`. Its Model slot is `eino-podcast.model`, and its Voice slot is
`eino-podcast.host`. Both input audio modes select the shared `asr` Model through
`ptt_asr_model` and `realtime_asr_model` on the Profile binding.

## Continuous playback and History

`conversation.continue_from: keep-speaking` repeats the Graph within one real
user turn. Every generation targets one short section of 150–200 Chinese
characters. The runtime preserves one playback stream and waits for text and
TTS delivery before advancing. The Graph's eight-step budget applies to each
execution, not to the total number of sections.

Each generated section saves its own History entry with corresponding text
and replayable audio. Entries become available during narration. An interruption
cancels the current generation and saves only its delivered prefix; completed
sections remain separate. Resuming and redirecting create new user turns.

The prompt binds the Workspace safety fence first. Recent context is bounded,
and the current real request follows the historical assistant messages once.
This package uses GizClaw v0.31.0 or later; repository CI pins v0.31.5.

## Tests

```sh
make test-unit-podcast
make test-e2e RAID=podcast TIER=smoke
make test-e2e RAID=podcast TIER=quality
make test-e2e RAID=podcast TIER=soak
```

Provide `GIZCLAW_TEST_ENDPOINT` and `GIZCLAW_TEST_REGISTRATION_TOKEN` for a
Server containing the Workflow and its Profile bindings. Smoke verifies text
startup, continuous single-stream audio, per-section History, interruption and
audio download. Quality uses real synthesized PTT input and checks pause,
resume and topic changes. Soak uses realtime ASR input and a longer listening
window. The Giztests create ephemeral Peers and remove their Workspaces.

Server/Edge and real Provider results do not qualify a physical device's
microphone, speaker, echo cancellation or local interruption behavior.
