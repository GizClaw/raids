# GizClaw Raids

[![CI](https://github.com/GizClaw/raids/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/GizClaw/raids/actions/workflows/ci.yml?query=branch%3Amain)

Reusable resource loadouts for [GizClaw](https://github.com/GizClaw/gizclaw)
AI workflows.

**Raids** stands for **Resources for AI Drivers & Scenarios**. Like a raid
loadout in a game, each collection brings together the workflows, models,
voices, credentials, and provider definitions needed for an AI scenario.

## Layout

Resources are grouped by kind. Credential, Tenant, Model, and MemoryLayout
resources are flat because their `metadata.id` already provides the
stable identity. Voice catalogs keep one grouping level per Tenant; Workflows are grouped by
scenario (raid), with one file per engine implementation plus the scenario's
Tester, metadata, and README:

```text
credentials/<credential-name>.yaml
tenants/<tenant-name>.yaml
models/<model-name>.yaml
memory-layouts/<layout-name>.yaml
voices/<tenant-name>/<voice-id>.yaml
workflows/<raid-name>/<engine>.yaml        # one directory per scenario: flowcraft.yaml, eino.yaml, ...
workflows/<raid-name>/test.yaml            # original Tester Workflow (id <raid-name>-test)
workflows/<raid-name>/raid.json            # scenario metadata: rating, category, tags, voices, models, testing
workflows/<raid-name>/README.md            # human-readable play and test route
workflows/<raid-name>/routing-cases.json   # shared dual-engine routing cases for multi-voice raids
runtime-profiles/<profile-name>.yaml
registration-tokens/<token-name>.yaml
runtime-profile.example.yaml
```

File names are repository-local. Each applyable catalog Resource declares its
immutable, caller-defined Admin identity in `metadata.id`. Every ID-bearing
reference in that catalog contains the exact target Resource ID, so consumers
submit the selected graph without name lookup or reference rewriting.

Generic Admin `metadata.name` is unsupported. RuntimeProfile map keys remain
Peer-facing aliases scoped by that profile; each binding points to an Admin
Resource ID and does not create an alternate Admin selector.

Every RuntimeProfile alias — Workflow collection names, Workflow, Model, Voice
and memory binding keys, and `app_config` keys — is 1-63 bytes of
dot-separated lowercase kebab-case segments, for example
`learn.chinese-poetry-grade1-eino` or `story.animal-kingdom`. Underscores and
uppercase letters are rejected. GizClaw v0.18.15 enforces this when a Server
normalizes the profile, which `gizclaw admin validate` does not do, so
`make test-unit-resources` checks it offline and also rejects a Workflow alias
bound in more than one collection.

Admin IDs are opaque and kind-qualified. They contain at most 1,024 Unicode
characters, preserve internal characters exactly, and cannot have surrounding
whitespace or be the standalone URI dot segments `.` and `..`.

Current drivers:

- `ast-translate`
- `doubao-realtime`
- `eino`
- `flowcraft`

[`runtime-profiles/default.yaml`](runtime-profiles/default.yaml) is the
canonical, applyable public `RuntimeProfile/default`. It selects every public
Workflow in this repository and binds the Model, Voice, and MemoryLayout
aliases needed by that catalog.
[`registration-tokens/default.yaml`](registration-tokens/default.yaml)
publishes the matching `RegistrationToken/default-runtime`; its stable public
client value is `28c4e4e9-a05f-5a7e-815e-9cf9afb6878f`.

### Workspace safety fence

Every player-facing Flowcraft and Eino implementation places the Workspace
`safety_fence_level` prompt first in the system message, then a blank line and
the scenario instructions. The Workspace chooses `off`, `general`, or `child`;
the RuntimeProfile owns the complete text in
`spec.safety_fences.{general,child}.prompt`. `child` does not inherit `general`.
Raids does not choose a level or supply fallback fence text.

```yaml
# Flowcraft LLM config
system_prompt: |-
  ${board.safety_fence}

  Original scenario instructions.
```

```yaml
# Eino prompt node; retain all existing inputs alongside safety_fence
inputs:
  safety_fence: {from: input.safety_fence}
  history: {from: input.messages}
format: f_string
messages:
  - role: system
    template: |-
      {safety_fence}

      Original scenario instructions.
  - placeholder: history
```

Eino input keys become template variable names; no extra State field is
needed. All current player prompts use `f_string`: `{safety_fence}` is the
variable, while `{{` and `}}` escape literal braces. Neither this formatter
nor Flowcraft's variable resolver trims the prompt. At `off`, the prefix
becomes exactly two newlines, with no label, punctuation, or unresolved
variable. These are valid system-message whitespace. We retain the existing
formats rather than change every template to remove that whitespace. Future
`go_template` prompts can use `{{if .safety_fence}}{{.safety_fence}}`, a blank
line, then `{{end}}` immediately before the original text; `jinja2` can use
`{% if safety_fence %}{{ safety_fence }}`, a blank line, then `{% endif %}`.
These conditional forms omit the separator at `off`.

Only player replies receive the variable, including drafts forwarded through
published scripts, every narrator/character, and each alternative response
prompt. Player-visible conclusions are replies too. Internal JSON classifiers,
routing, memory extraction, and summaries do not receive it. Tester Workflows
play the user and do not receive the fence. Existing scenario safety rules
remain part of the scenario even at `off`.

`make test-unit-resources` runs `scripts/test/safety-fences.rb` and its fixture
tests before schema validation. Discovery includes every Workflow YAML under
each raid, excluding Tester/Giztest files. `ast-translate` and the realtime
drivers are listed as unfenced (see below); any other driver fails until its
coverage is reviewed.
The check follows directly published Flowcraft LLMs, drafts read by published
scripts, and Eino prompt outputs consumed by published text ChatModels. Every
such prompt must start with its bound fence and a blank line. A graph without
a recognized player reply path fails and needs an explicit coverage review
when adding a new graph shape.

**Runtime dependency:** Eino's reserved `input.safety_fence` binding requires
the GizClaw Workspace safety fence change. CI is currently pinned to
**v0.18.12**, which rejects it with `binding source "input.safety_fence" is not
declared`. Until GizClaw releases that support and CI's pinned artifact and
checksum are upgraded, `make test-unit-resources` fails on the Eino catalog.
Local offline validation can use `GIZCLAW=/absolute/path/to/gizclaw` built from
the fence-enabled source. The CI pin and validation remain intact.

This contract covers every raid with Flowcraft/Eino implementations.
`ast-translate` has no system prompt entry, so GizClaw provides no fence to it.
`doubao-realtime` is player-facing but **not yet fenced**: GizClaw expects a
`${safety_fence}` placeholder in realtime `instructions`, while manifest loading
expands every `${NAME}` as an environment variable with no escape, so
`gizclaw admin validate/apply` rejects or rewrites it. It stays unfenced until
GizClaw resolves that conflict.

### Runtime alias ownership

RuntimeProfile Model and Voice aliases are opaque flat keys. Dots make
ownership visible; they do not create nested maps, fallback, wildcard, or
prefix lookup. Workflow-owned slots use the canonical Workflow
`metadata.id` as their namespace:

```text
<Workflow metadata.id>.<role>
```

`asr` is the only shared Model alias, and every ASR-capable Workflow uses it.
Every public MemoryLayout keeps its `spec.flowcraft.extraction` policy object
while selecting `<MemoryLayout metadata.id>.extract`. The schema field
`extraction` is not a Model alias. Scoped extraction aliases may bind the same
Model resource while remaining independently configurable.

| MemoryLayout `metadata.id` | Extraction Model alias |
| --- | --- |
| `user-chat-with-assistant` | `user-chat-with-assistant.extract` |
| `story-teller` | `story-teller.extract` |
| `adventure` | `adventure.extract` |
| `learner` | `learner.extract` |

Each Raid can otherwise select its own Model independently, even when several
slots currently bind the same Model resource:

| Workflow `metadata.id` | Model alias |
| --- | --- |
| `doubao-realtime-conversation` | `doubao-realtime-conversation.model` |
| `flowcraft-chat-assistant` | `flowcraft-chat-assistant.model` |
| `ast-translate-ja-zh` | `ast-translate-ja-zh.model` |
| `ast-translate-ko-zh` | `ast-translate-ko-zh.model` |
| `ast-translate-zh-en-auto` | `ast-translate-zh-en-auto.model` |
| `ast-translate-zh-es` | `ast-translate-zh-es.model` |
| `ast-translate-zh-fr` | `ast-translate-zh-fr.model` |
| `ast-translate-zh-ja` | `ast-translate-zh-ja.model` |
| `ast-translate-zh-ko` | `ast-translate-zh-ko.model` |
| `flowcraft-murder-mystery` | `flowcraft-murder-mystery.model` |
| `flowcraft-journey-guide` | `flowcraft-journey-guide.model` |
| `eino-journey-history` | `eino-journey-history.model` |
| `eino-journey-memory-recall` | `eino-journey-memory-recall.model` |
| `eino-journey-memory-async` | `eino-journey-memory-async.model` |
| `flowcraft-story-aesop` | `flowcraft-story-aesop.model` |
| `eino-story-aesop` | `eino-story-aesop.model` |
| `flowcraft-story-alice` | `flowcraft-story-alice.model` |
| `eino-story-alice` | `eino-story-alice.model` |
| `flowcraft-adventure-space-rescue` | `flowcraft-adventure-space-rescue.model` |
| `eino-adventure-space-rescue` | `eino-adventure-space-rescue.model` |
| `flowcraft-adventure-monster-maze` | `flowcraft-adventure-monster-maze.model` |
| `eino-adventure-monster-maze` | `eino-adventure-monster-maze.model` |
| `flowcraft-adventure-castle-mystery` | `flowcraft-adventure-castle-mystery.model` |
| `eino-adventure-castle-mystery` | `eino-adventure-castle-mystery.model` |
| each `flowcraft-learn-chinese-poetry-grade*` Workflow | `flowcraft-learn-chinese-poetry-grade<N>.model` |
| each `eino-learn-chinese-poetry-grade*` Workflow | `eino-learn-chinese-poetry-grade<N>.model` |
| each `flowcraft-learn-math-grade*` Workflow | `flowcraft-learn-math-grade<N>.model` |
| each `eino-learn-math-grade*` Workflow | `eino-learn-math-grade<N>.model` |
| each `flowcraft-learn-science-grade*` Workflow | `flowcraft-learn-science-grade<N>.model` |
| each `eino-learn-science-grade*` Workflow | `eino-learn-science-grade<N>.model` |
| `flowcraft-learn-chinese-stories` / `eino-learn-chinese-stories` | `<Workflow>.model` |
| `flowcraft-learn-chinese-words` / `eino-learn-chinese-words` | `<Workflow>.model` |

Voice roles use the same Workflow namespace:

| Workflow `metadata.id` | Voice roles |
| --- | --- |
| `doubao-realtime-conversation` | `assistant` |
| `flowcraft-chat-assistant` | `assistant` |
| each `ast-translate-*` Workflow | `translator` |
| `flowcraft-murder-mystery` | `game-master`, `housekeeper`, `chef`, `heir`, `lawyer` |
| `flowcraft-journey-guide` | `narrator` |
| each `flowcraft-story-*` / `eino-story-*` Workflow | `storyteller` plus every title-specific character role declared by its `raid.json` |
| each `flowcraft-adventure-*` / `eino-adventure-*` Workflow | `adventure-guide` plus every scene-specific character role declared by its `raid.json` |
| each `flowcraft-learn-chinese-poetry-grade*` Workflow | `tutor` |
| each `flowcraft-learn-math-grade*` Workflow | `tutor` |
| each `flowcraft-learn-science-grade*` Workflow | `tutor` |
| `flowcraft-learn-chinese-stories` | `tutor` |
| `flowcraft-learn-chinese-words` | `tutor` |

Eino spoken implementations declare these additional Voice roles:

| Workflow `metadata.id` | Voice role |
| --- | --- |
| each `eino-story-*` Workflow | `storyteller` |
| each `eino-adventure-*` Workflow | `adventure-guide` |
| each `eino-learn-*` Workflow | `tutor` |
| `eino-journey-history`, `eino-journey-memory-async`, `eino-journey-memory-recall` | `narrator` |

Each alias is `<Workflow metadata.id>.<role>`. Both public RuntimeProfiles
bind it to the same Voice resource as the corresponding Flowcraft default.
Journey's three Eino variants accept text and push-to-talk input and synthesize
spoken output. Like every Eino/Flowcraft voice adapter, they select the shared
`asr` Model alias; custom RuntimeProfiles must bind it alongside their Voice aliases.

For example, Journey resolves `flowcraft-journey-guide.narrator` exactly.
Different scoped aliases may bind the
same canonical Voice without becoming interchangeable. Catalog resources that
have no current Workflow or MemoryLayout role remain available but are not
published as unowned RuntimeProfile aliases.

These dotted aliases require the RuntimeProfile grammar introduced by
[GizClaw #828](https://github.com/GizClaw/gizclaw/issues/828). A GizClaw build
without that contract rejects this catalog rather than rewriting its aliases.

Translation Voice roles follow the output language rather than the input
language or provider used by the translation Model. The default Chinese-to-
Japanese, Chinese-to-Korean, Chinese-to-Spanish, and Chinese-to-French
Workflows select the public MiniMax system Voices `Japanese_CalmLady`,
`Korean_CalmLady`, `Spanish_SereneElder`, and `French_MovieLeadFemale`, which the
[MiniMax system Voice catalog](https://platform.minimaxi.com/docs/faq/system-voice-id)
classifies for those languages. These bindings add `MiniMaxTenant/minimax-cn`
and its environment-owned Credential to the default dependency closure; Raids
contains no credential value. Every public MiniMax Voice selects
`speech-2.6-turbo` through `spec.provider_data.model`; GizClaw v0.7.0 and later
require that Voice-owned provider model when constructing MiniMax TTS and do
not substitute a hidden model default.

The public MemoryLayout catalog is organized by reusable scenario:

- `user-chat-with-assistant` stores durable user conversation context.
- `story-teller` separates Graph-written progress from narrated continuity.
- `adventure` stores player-visible investigation state, discoveries,
  interviews, and explicit corrections.
- `learner` stores the child's stated grade, items actually taught, answered
  and open questions, and explicit corrections for `learn-*` raids.

Knowledge-extension raids use the `learn-<subject>-<topic>` naming scheme and
the `learn` collection. Each one embeds a verified knowledge card in its
prompt, keeps the sources in its package `knowledge.json`, teaches anything
the child brings up, and must say "没有确切记载" instead of inventing details
the card does not hold. The poetry set is `learn-chinese-poetry-grade1` through
`learn-chinese-poetry-grade6`, one package per 统编版 grade so each prompt
carries only that grade's poems plus a title index of the rest. The math set is
`learn-math-grade1` through `learn-math-grade6`, one package per 人教版 grade
with its units, verified extension problems, puzzles, mathematical culture,
and a title-only index of the other grades. The science set is
`learn-science-grade1` through `learn-science-grade6`, one package per 教科版
grade with its units, safe home experiments, checked facts, common
misconceptions, shared scientist facts, and a title-only index of the other
grades. Two all-grades Chinese packages round out 语文: `learn-chinese-stories`
(文言文, 寓言, 成语故事, and 快乐读书吧 books, telling copyrighted books only by
gist) and `learn-chinese-words` (谚语, 歇后语, 名言 with disputed attributions
flagged, 对子, and 汉字小故事).

### Maintaining knowledge-extension raids

Each learn package's `knowledge.json` is its source of truth. Edit the card,
then run `python3 scripts/learn/generate.py` to refresh every generated
Workflow, Tester, manifest, README, and Giztest, or pass one or more raid IDs
to refresh only those packages. `make test-unit-learn` regenerates all
`learn-*` packages in a temporary directory and fails on drift. Runtime
profiles remain hand-written and are never generated by this tool.

The public story catalog contains 19 titles, each with paired Flowcraft and
Eino implementations. Every title owns an independent four-chapter bible,
player role, character knowledge boundaries, transition and ending conditions,
fact/legend/fiction rules, child-safety rules, correction precedence, durable
clues, unresolved hooks, and anti-repetition policy. A transition happens only
when the current choice satisfies the adjacent chapter condition; entering a
chapter emits its localized title once and continues straight into that
chapter's opening scene in the same reply, while ordinary turns never repeat
it. Every chapter-one opening states the setting, the child's role, and the
currently present characters, previews later arrivals, and explains how to play:
answer with a choice, ask a named character to speak, and say “进入下一章” once the chapter's choice is made.
Whenever a story asks the child to choose, the question names the concrete
options. After the chapter's choice and its consequences, the narrator sums the
chapter up and ends once with “这一章的选择完成啦！想听下一章就说‘继续’或‘进入下一章’，要继续听吗？”;
the next “继续”, “好”, “要” or “进入下一章” enters the adjacent chapter (Flowcraft
maps both to the adjacent chapter). The last chapter ends by asking whether to
hear the story again.

H106 devices submit “开始” (or “继续上次的内容”) once when the child enters a
story, adventure or 西游记 and never speak on their own afterwards, so every
reply ends with a question to the child — named options or whether to go on —
except safety refusals and turns where the user limits length or only asks to
confirm facts. “开始” always opens the first chapter (西游记 opens at 石猴出世),
even when history or memory exists; “继续上次的内容” recalls progress, says in
one sentence where the story stopped and carries on. Multi-role variants keep
their automatic chapter flow and end every narration with an in-story question.
The Wizard of Oz additionally preserves its explicit English chapter-one
restart and established English opening on both implementations.

### Narrator and character voices

Original Flowcraft stories reconstruct `story_contract_v1` after reload and
route narrator or character turns to one published model node with its own
Voice alias. Original Eino stories preserve the same story/state contract with
one `text/plain` primary output synthesized by the `storyteller` default Voice.


The multi-role variants of 19 stories and 11 adventures use continuous audiobook narration in both
engines: one narration LLM emits 300–600 characters per ordinary turn, with
narration and 2–4 present characters alternating paragraphs. A scene with only
one eligible character keeps that cast. Children may interrupt at any time;
naming a present character increases that character's dialogue in the segment.
Chapter/scene eligibility, knowledge boundaries, corrections and legacy memory
recovery remain authoritative. The narrator ends with 2–3 concrete choices,
except where the existing choice-completion sentence, final chapter, safety or
limited confirmation/correction contract requires a different ending. Limited
administrative and safety responses may be shorter than 300 characters.
Ordinary narration targets 400–500 Unicode characters (including English spaces
and punctuation), in five bounded paragraphs, leaving margin inside the 300–600
contract. Corrections that also request continued narration are ordinary turns.

Every raid with multi-role variants has a separate `test.multi-role.yaml`
(`<raid>-test-multi-role`). Its deterministic checks strip known speaker markers
and apply the multi-role reply contracts, retaining content and safety checks.
`raid.json` keeps `tester` for originals and registers the variant under
`testers.multi-role`, with explicit `implementations`. Soak multi-role clients
select this Tester in `raidtest-testers`. Profiles must register its Workflow;
it reuses the original `<raid>-test.model` judge alias. Murder-mystery retains
its exact opening, bounded witness replies, correction and short-summary rules.

Every paragraph begins with exactly one configured `【旁白】` or Chinese
character marker, immediately followed by prose; no other `【】` markers are
allowed. `voice_adapter.speaker_voices` maps these names to existing aliases;
`default_voice` is the narrator alias. AudioDock strips configured markers from
device text, serializes audio and prefetches the next segment. Interruption
cancels current and pending segments. This requires **GizClaw v0.18.12**.
`murder-mystery` retains its existing single-speaker routing contract.

Both engines retain ASR, existing voice slots and matching role Voice resources
in `default` and `testing` RuntimeProfiles. Chapter controls and investigation
phase rules feed the single narration LLM instead of selecting a speaking node.

Workflows and `raid.json` reference only Voice aliases named
`flowcraft-<raid>-mr.<role>` or `eino-<raid>-mr.<role>` for multi-role variants. Original aliases retain their Workflow namespace. Narrator slots retain
`.storyteller` for stories, `.adventure-guide` for adventures, and `.game-master`
for murder mystery. Within each raid implementation, narrator and character
slots must bind to distinct voices; the same role uses the same voice across
engines. Per-raid READMEs document roles, Chinese names, aliases, and engine
segment mappings.

Concrete Voice resources are bound at runtime through `runtime-profiles/*.yaml`
under `spec.resources.voices`; deployment bindings are owned by deploy's profile.
Workflow and raid documentation does not pin concrete Voice resource IDs.

New voices require **online verification in the tenant**. Catalog bindings and
offline checks do not establish provider access, actual selected voices,
latency, or sound quality; synthesis logs and listening remain separate
acceptance evidence.

Each Layout defines portable Flowcraft, Mem0, and Volc Mem0 policy. The public
default profile selects Flowcraft with `connection.type: flowcraft_bbh`; it
does not publish an endpoint, key, project ID, DSN, or directory. The consuming
Server derives managed BBH storage from its own Workspace.

Provider policy does not bypass runtime capability checks. In particular,
Graph-authoritative `memory_observe.facts` writes require a Store with
direct-fact support, which the public default Flowcraft binding provides. The
current Mem0 and Volc Mem0 adapters accept conversation extraction but not
direct structured facts, so Workflows that write authoritative facts must not
be switched to those drivers until the adapters add that capability. Their
Layout blocks remain the policy contract for configuring compatible
environment-owned projects; their presence alone is not proof of runtime
compatibility or successful extraction.

A Flowcraft `memory_observe` operation never combines conversation extraction
with direct Facts. Workflows use separate ordered nodes when they need both, so
model extraction and Graph-authoritative idempotent writes retain independent
ownership. Every public top-level or nested Flowcraft graph also keeps two to
eight iterations of headroom above its longest acyclic route. This covers
terminal memory nodes without replacing `max_iterations` as the bounded loop
guard.

[`runtime-profile.example.yaml`](runtime-profile.example.yaml) remains a
documentation-only composition example with unresolved Voice placeholders. It
is not discovered or applied as a catalog resource.

The MemoryLayout definitions require a GizClaw build containing the MemoryLayout contract
merged by [GizClaw #590](https://github.com/GizClaw/gizclaw/pull/590).

## Static resource validation

Raids uses the released GizClaw binary as the only authority for declarative
Resource format validation. With GizClaw v0.18.15 or later on `PATH`, validate
every applyable catalog Resource with:

```sh
make test-unit-resources
```

Use `GIZCLAW=/path/to/gizclaw make test-unit-resources` to select an explicit
binary. The target validates each YAML file under the applyable Resource
directories independently, checks every RuntimeProfile alias against the
Server's alias syntax, and then validates the
declarative Giztest corpus with `gizclaw test validate`. It does not read
`runtime-profile.example.yaml`. It is offline: it does not use a GizClaw context, contact Server, or mutate
resources.

Every public Make target dispatches to the same-named script under
`scripts/<group>/<target>.sh`; the Makefile itself only declares targets,
default variables, and exports. `make help` lists the complete surface:
`test-unit-resources`, `test-unit-learn`, `test-unit-voices`, and `test-e2e`. CI runs each
`test-unit-*` target as its own step; there is no aggregate target.

For static schema validation, the target exports a fixed non-secret placeholder
for each empty variable declared by `.env.example`. It never reads or requires
real provider credentials; `.env.example` remains the maintained list of
allowed Credential and Tenant placeholders and validation fails if that file
contains a populated value.

The target also checks the manifest → speaker mapping → both RuntimeProfiles →
Voice resource chain, distinct role Voices and matching bindings across engines.
For 31 continuous-narration raids it verifies a single narration LLM, configured
Chinese markers, 300–600-character story probes, clean text, complete serial
audio and zero underruns. First-response gates remain unchanged. Quality keeps
safety, transitions, choice endings and correction/recovery contracts; soak
keeps the relay/reload structure. Limited administrative/safety replies retain
their original bounds. Quality budgets are 30 minutes for these longer stories.

Each raid supplies a version-1 `routing-cases.json`. The gate executes actual
Flowcraft JavaScript and Eino Starlark against state and content-control
assertions. Single-speaker naming/order assertions have been removed from the
31 story/adventure/figure fixtures; murder mystery retains its existing tests. Ruby,
Node.js and a local Go toolchain with cached Starlark dependencies are required;
Go module downloads are disabled. Offline validation cannot establish real
provider voice switching, timing, interruption or audible continuity.

Passing this check establishes schema, binding, and deterministic routing
contracts, not live behavior. CI still pins the immutable v0.18.2 Linux package
and verifies its published SHA-256 digest; that pin predates `speaker_voices`
and must be upgraded separately to validate this merged catalog.
`make test-unit-voices` separately requires exactly 635 MiniMax Voice files and exactly one
`model: speech-2.6-turbo` field in each. Per-file schema validation alone does
not prove other runtime-only requirements such as cross-resource references or
aliases resolve, provider credentials work, or a live Server
will accept and run the complete catalog. Apply, runtime, `make test-e2e`,
release, and Beijing Default E2E remain separate evidence.

## Raid packages

Every scenario is one package directory `workflows/<raid>/`: one Workflow per
engine implementation (`flowcraft.yaml`, `eino.yaml`, …), the scenario's single
original relay Tester (`test.yaml`, id `<raid>-test`), a `raid.json` manifest, and a
README. `raid.json` declares the implementations and the slots each needs —
model aliases, voice aliases, MemoryLayout — without binding them to concrete
resources; rating (`raids-age-v1`), category, and tags make the catalog
filterable. It is descriptive metadata for consumers and reviewers, not an
input to a generator: `runtime-profiles/default.yaml` and
`runtime-profiles/testing.yaml` stay hand-written, and adding a raid to a
profile means binding its Workflow in a collection and declaring the model and
voice aliases the manifest lists.

## Declarative live tests

Live tests use `tests/giztest/{smoke,quality,soak}/<raid>.<implementation>.giztest.yaml`, one implementation per file, named after its Workflow file. There are **529 tier files**: **179 smoke**, **179 quality**, and **171 soak**. The **128 device** files and the two external H106 files remain separate, for **659 `.giztest.yaml` files** total; generated reports are excluded. Selected files run concurrently with `gizclaw test run --parallel N`.

- **smoke** measures speed, latency and responsiveness, including complete audio and independent first-response probes.
- **quality** enforces deterministic quality and safety guardrails, including transitions, corrections, language and role boundaries. Independent suite responses run in parallel and finish together within the existing file budget; long Tester relays live in soak.
- **soak** runs long conversations between the Tester and target Workflow, including reload and memory continuity.
- **device** replays the H106 entry flow for every story, adventure and Journey implementation: “开始”, “我选第一个”, “继续”, leave and re-enter (`server.run.stop` + reload), “继续上次的内容”, “开始”. Every reply must end with a question; original stories must enter chapter 2 on “继续”, resume there, and restart at chapter 1. The files are generated by `ruby scripts/test/device-flow.rb`, are not registered in `raid.json`, and run with `make test-e2e TIER=device`.

The audio-only `ast-translate` and `doubao-realtime` targets have no soak protocol. Murder Mystery is Flowcraft-only. Journey tests all four implementations against equal gates, including recall; its history-only implementation has no recall exemption.

```sh
make test-e2e TIER=smoke RAID=story-aesop
make test-e2e TIER=quality RAID=all
make test-e2e TIER=soak RAID=journey-guide
make test-e2e TIER=device RAID=all
```

Set `GIZCLAW_TEST_ENDPOINT` and `GIZCLAW_TEST_REGISTRATION_TOKEN` for live runs. Defaults are `TIER=all RAID=all PARALLEL=4 APPLY=0`; H106 is excluded. `REPORT` selects the output JSON. `APPLY=1` retains its existing behavior: apply the entire testing closure with the Admin context before running the selected files.

`make test-unit-resources` validates schemas, tier inventory, manifest registration, Voice/role closure, internal routing fixtures and equivalent implementation steps offline. It checks client idle gaps (180s scheduling budget, including cleanup) and compares implementation files per variant for complete inputs, assertions, captures, timeouts and relay plans after normalizing client identifiers and Workspace implementation settings. `make test-unit-voices` checks the Voice catalog.

Smoke retains the 2-second first-text / 3-second first-audio probes and the original complete-response gates. Complete streams additionally require closed, non-overlapping audio, zero underruns and a nonnegative minimum playback buffer under Giztest’s 500ms prebuffer model; packet gaps remain diagnostic evidence. The CLI must support `/audio_integrity` and `/audio_pacing`. Necessary role setup can exceed the two-minute target; file budgets do not relax per-step gates. A failure stops subsequent steps: skipped steps are not passes, and cleanup is reported separately. See the [test guide](tests/giztest/README.md) for the full layout, selection rules and Tester protocol.

## Catalog behavior notes

Default General Assistant intentionally keep Memory extraction
asynchronous. Same-Workspace turn continuity and reload recall come from the
GizClaw Flowcraft History store; deployments must configure
`services.agent_host.flowcraft.history_store`. Memory supplies longer-lived
semantic recall and must not become a per-turn response barrier.

[Murder Mystery](workflows/murder-mystery/README.md) remains a free-investigation
`adventure`, rated **12+ / mystery-death**. Its host handles openings, evidence
checks, corrections, reasoning, provisional accusations, and conclusions.
The housekeeper, chef, Shen Zhiqiu (沈知秋), and lawyer answer individual
interviews in first person using their own testimony and public dialogue;
they do not receive the host's private truth or raw recall notes. The host does
not impersonate witnesses. Flowcraft retains the 26-response investigation
regression and five-role audio and handoff/leakage-guard tests.

Murder Mystery follows the same History ownership for its full transcript and
observes only its explicit authoritative shoe-size state into Memory. It does
not run a second whole-conversation semantic extraction after publishing each
reply; the bounded Recall barrier still verifies the corrected state before
reload.

Two Default gates require GizClaw runtime support beyond Raids configuration:
Doubao realtime reload memory and deterministic text limits are tracked by
[GizClaw #852](https://github.com/GizClaw/gizclaw/issues/852) and
[GizClaw #853](https://github.com/GizClaw/gizclaw/issues/853). The committed
plans keep those checks active instead of treating the dependencies as passes.

The bidirectional Chinese-English AST Workflow binds a multilingual Voice, so
the same automatic-language entry can synthesize either target language.

## Download

GizClaw Desktop downloads this repository from GitHub as a source archive. The
current development package is always available from:

```text
https://github.com/GizClaw/raids/archive/refs/heads/main.tar.gz
```

Versioned packages use the corresponding Git tag archive, for example:

```text
https://github.com/GizClaw/raids/archive/refs/tags/v0.4.0.tar.gz
```

Release `v0.2` includes the public `chatroom` and `pet-care` system Workflows
for Desktop consumers.

Release `v0.3.0` is the first catalog release using scenario MemoryLayouts,
flattened Flowcraft payloads, explicit Graph memory nodes, and portable
RuntimeProfile BBH bindings.

Release `v0.4.0` is the first catalog release in which every Resource supplies
its own Admin `metadata.id` and every cross-resource field already contains the
target ID. It requires a GizClaw caller-defined Admin ID contract and is not
compatible with the legacy `v0.3.0` name-resolution path.

Release `v0.4.1` scopes Workflow Model and Voice aliases by their owning
Workflow IDs. `v0.4.2` is the next patch release: its source contract fixes the
Beijing E2E Workflow limits and memory observations, selects target-language
Japanese and Korean Voices, and preserves the existing default adoption pool.
A merged source change is not a published release; consumers must pin the later
canonical tag and validate its archive.

The archive contains one generated top-level directory. Consumers locate the
kind directories relative to that root rather than depending on its generated
name.

## Default runtime bootstrap

The public default bootstrap contract consists of two ordinary Admin resources:

- `RuntimeProfile/default` defines the public product composition.
- `RegistrationToken/default-runtime` exposes the stable client bootstrap value
  `28c4e4e9-a05f-5a7e-815e-9cf9afb6878f` and targets that profile.

The public token is a deterministic UUIDv5. Its immutable derivation inputs
are:

```text
namespace = UUIDv5(
  NAMESPACE_URL,
  "https://github.com/GizClaw/raids/registration-tokens",
)
name = "default-runtime/v1"
token = UUIDv5(namespace, name)
```

The UUID is a stable public identifier, not a secret. The versioned name keeps
future token contracts reproducible without changing the v1 value.

Each Server owns its own independent copies of these resources. Reusing the
public token string does not share Server data, credentials, identities,
Terraform state, or lifecycle between Desktop, dev, production, or other
installations. The Server endpoint is selected separately by the client.

Applyable catalog files carry the complete Admin identity graph before
installation:

- Tenants use `credential_id`.
- Models and Voices use `provider.id` and `display_name`.
- RuntimeProfile bindings use `resource_id` and `layout_id`.
- RegistrationTokens use `runtime_profile_id`.

Before creating anything, a consumer validates that each reference identifies
exactly one Resource of the required kind. It expands only deployment-owned
values such as Credential bodies, then submits the selected Resources in
dependency order without changing identities or references:

1. Apply Credential definitions with deployment-owned values.
2. Apply Tenant definitions.
3. Apply Models, Voices, and MemoryLayouts.
4. Apply Workflows.
5. Apply `RuntimeProfile/default`.
6. Apply `RegistrationToken/default-runtime`.

Applying the RegistrationToken before the RuntimeProfile fails because the
profile reference is unresolved. Applying the same desired `(kind, id)` again
is idempotent; after an ambiguous transport failure, a consumer reads or
reapplies that same ID instead of allocating a second logical Resource. An
apply result may be checked against the submitted ID but is never used to edit
another manifest. Products may omit or override the public defaults and may
install additional product- or hardware-specific profiles and tokens.

## Scope

This repository contains public Credential, Tenant, Model, MemoryLayout,
Voice, Workflow, RuntimeProfile, and RegistrationToken source
resources. It publishes the default runtime bootstrap contract while leaving
every applied resource instance under the ownership of its Server and
deployment tooling.

Credential resources define stable IDs, providers, and body shapes, while
their values remain `${ENVIRONMENT_VARIABLE}` examples. The repository never
contains real credential values. Copy [`.env.example`](.env.example) to the
environment configuration managed by the consuming product or deployment and
fill only the credentials it selects.

Voice files are snapshots of provider system catalogs. Purchased, cloned,
generated, trained, and otherwise account-private voices are excluded. Server
timestamps, account status, and raw provider responses are not source
resources and are also excluded.

The MiniMax CN and Global snapshots make the TTS provider model explicit on
each Voice; the current public catalogs select `speech-2.6-turbo`. Volc Voice
identity is generation-specific: the filename stem, `metadata.id` suffix, and
`provider_data.voice_id` preserve the provider's exact `voice_type`, while
`provider_data.resource_id` distinguishes `seed-tts-1.0`, `seed-tts-2.0`, and
realtime resources. Consumers opt into a generation by selecting its concrete
Voice resource; the catalog does not derive counterparts or fall back across
generations.

The Volc `seed-tts-2.0` snapshot comes from the public
[voice list](https://www.volcengine.com/docs/6561/1257544?lang=zh), document
`1257544` updated `2026-08-20T07:24:41Z`. It contains 444 Voices: 93 system,
200 public ICL, and 151 multilingual entries. Provider-documented synthesis
mode restrictions are descriptive selection metadata; the provider remains
the enforcement point. The public ICL entries still use
`seed-tts-2.0`; `seed-icl-2.0` is reserved for account-private trained Voices
and remains outside this snapshot.

Each Voice directory name matches its Tenant `metadata.id`, so catalogs with
different providers, endpoints, or regions remain separate. For example,
`voices/minimax-cn/`, `voices/minimax-global/`, and
`voices/volc-cn-beijing/` correspond to those three Tenant resources.

Workspace instances, real credential values, secrets, private Workflows,
product- or hardware-specific RuntimeProfiles and RegistrationTokens, and other
user or runtime state remain outside this repository.

### Original Eino voice behavior

Original story, adventure and learn Eino Workflows use their Workflow-scoped default Voice for the complete primary text output; multi-role Eino variants add character Voice switching. Both engines use ASR for paced RealTime audio input. Journey Eino history, asynchronous-memory and recall variants also retain ASR and the narrator default Voice. RuntimeProfiles bind these aliases to the same role Voice as Flowcraft.

The smoke RealTime probes require complete text/audio output and separate 2-second text / 3-second audio first responses for TTS-capable implementations. Offline checks validate Eino Voice ownership, manifest declarations and resolution in both RuntimeProfiles alongside tier parity and multi-role Voice closure.
