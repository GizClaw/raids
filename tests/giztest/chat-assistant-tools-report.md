# Chat Assistant native Tool qualification — 2026-10-09

The final shipped configuration passed real-provider Docker qualification on
GizClaw 0.27.0. This tests Raids configuration and the device protocol boundary;
the MHS/ClientTool endpoints are Giztest handlers, not physical H106 hardware.

## Environment and scope

- Released Server/Edge/CLI image: `ghcr.io/gizclaw/gizclaw@sha256:122619e0ecc54e2fc7b3718f6ba08148ce868b7f3890b3ff9ee993ea271f5df5`.
- Pinned real Mem0 0.27.1 and PostgreSQL/pgvector, with a dedicated agent History
  log for reload continuity. SQLite lives in a disposable Docker volume.
- Actual Doubao Seed 2.1 Lite, Volcengine search, ASR/TTS and embedding credentials
  enter process/container environments; no provider credential is archived.
- Both original default/testing Profiles and their complete 270-Resource closure
  are applied without graph or alias rewrites. The default Profile has 322
  Workflow aliases; testing has 287. Chat selects ten Tool aliases.
- Containers, networks, volumes and temporary identities are deleted afterwards.
  The shared E2E cluster's default RuntimeProfile is not required or modified.

## Final results

| Check | Result |
| --- | --- |
| 28 device/dialog scenarios × two Profiles × three repetitions | 168/168 PASS |
| Review follow-up: scoped cancellation, new request and unrelated numeric answer | 18/18 PASS |
| Reply turns, including real model clarification and follow-up | 246/246 PASS |
| Actual device mutation receipts | 108; exact targets/arguments/call counts |
| Original Chat smoke | PASS |
| Original Chat quality, including real weather/date search | PASS |
| Original Chat soak and reload recall | PASS |
| Six repository unit targets, released CLI schema validation and hygiene | PASS |

The complete device run and standard-tier run used identical source-file hashes
and Resource-closure hashes. All assertions and original timing/audio thresholds
remain enabled. Required tasks and steps passed; skipped steps are not passes.
The subsequent review fix scopes cancellation to an active brightness request
and ends that context on an unrelated task while preserving acknowledgments.
Its changed paths passed the additional 18-task native run and deterministic
negative-control unit tests. The generator now contains 29 scenarios (58
documents; 174 tasks at the default repetition), including that new boundary.

Device replies' first-text time was 3,557 ms median, 6,362 ms P95 and 11,750 ms
maximum. These measure the complete reply path, including memory, native model
selection, semantic verification and device continuation; they are not the
latency of one model ToolCall.

The scenarios cover screen/status-light reads and exact writes, missing values
or targets, cancellation and a new request after cancellation, corrections,
negation, recorded preferences, out-of-range/unsupported settings, default/named/
next-song playback, stop, empty/unknown playlists, exact/ambiguous Workflow
selection, knowledge discussion, capability filtering, Workspace narrowing and
isolation between two Peers. Mutation counts and typed receipts are checked
after every turn, separately from spoken completion claims.

## Failures found and addressed

Ordinary playback initially guessed `index` or supplied JSON null. The prompt
now requires omission for device-default playback. Next-song selection must
read current status and the actual playlist in the current turn. Failed device
operations are not retried automatically. A program-selection ACK is confirmed
as acceptance, without claiming that reload or opening speech has finished.

One earlier repetition executed brightness after cancellation followed by a
bare percentage, despite model verification. A bounded Starlark History guard
now routes that input to deterministic clarification without entering the model
or invoking Tools. Only a new explicit brightness request reopens that flow;
assistant text, state queries and recorded preferences cannot. Native unit
tests and repeated real dialogs verify both blocked and reopened paths.

The fixture also exposed missing internal History persistence on reload, which
was corrected in its process configuration. Read observers were corrected to
permit actual reads, spoken Chinese numbers are accepted, and legitimate
unavailability/value-clarification wording is recognized. Those changes do not
relax action targets, values, mutation counts, or timing/audio gates.

Prior attempts remain available, including a weather first-text outlier of
15,734 ms against a 15,000 ms gate and a post-load opening of 7,319 ms against
6,000 ms. The unchanged standard tiers subsequently passed in a fresh fixture.
The measurements show provider/load variability; this is sample qualification,
not a guarantee that every future conversation meets those deadlines. Semantic
verification can reject and correct model proposals; final execution precision
does not establish perfect first-proposal model accuracy.

## Reproduction and receipts

```sh
RAIDS_CHAT_E2E_CREDENTIAL_FILE=/path/to/provider.env make test-e2e-chat-assistant
```

The credential file supplies the six Volcengine variables in `.env.example`.
The default command runs all device scenarios three times on both Profiles and
then the three original tiers. `RAIDS_CHAT_E2E_FILTER` supports focused reruns;
unknown case names fail instead of silently skipping device qualification.

Ignored local receipts:

- `reports/raids-chat-22b83cfa33/tools.json`: complete 168-task run.
- `reports/raids-chat-216c259196/{smoke,quality,soak}.json`: standard tiers.
- `reports/raids-chat-b9e2c01e92/tools.json`: 18-task review regression.
- `reports/chat-release-qualification.json`: matching-source audit and summary.
- Each run retains `giztest-inputs.zip`, source hashes and redacted container logs.
