# GizClaw Raids

[![CI](https://github.com/GizClaw/raids/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/GizClaw/raids/actions/workflows/ci.yml?query=branch%3Amain)

Reusable resource loadouts for [GizClaw](https://github.com/GizClaw/gizclaw)
AI workflows.

**Raids** stands for **Resources for AI Drivers & Scenarios**. Like a raid
loadout in a game, each collection brings together the workflows, models,
voices, credentials, and provider definitions needed for an AI scenario.

## Layout

Resources are grouped by kind. Credential, Tenant, Model, MemoryLayout, and Tool
resources are flat because their `metadata.id` already provides the
stable identity. Voice catalogs keep one grouping level per Tenant; Workflows are grouped by
scenario (raid), with one file per engine implementation plus the scenario's
Tester, metadata, and README:

```text
credentials/<credential-name>.yaml
tenants/<tenant-name>.yaml
models/<model-name>.yaml
memory-layouts/<layout-name>.yaml
tools/<tool-name>.yaml
voices/<tenant-name>/<voice-id>.yaml
workflows/<raid-name>/<engine>.yaml        # one directory per scenario: eino.yaml, eino.multi-role.yaml, ...
workflows/<raid-name>/test.yaml            # original Tester Workflow (id <raid-name>-test)
workflows/<raid-name>/raid.json            # scenario metadata: rating, category, tags, voices, models, testing
workflows/<raid-name>/README.md            # human-readable play and test route
workflows/<raid-name>/routing-cases.json   # shared dual-engine routing cases for multi-voice raids
cards/figure/<人物>.txt                     # knowledge card: facts about one historical figure
cards/guess/<subject>/<谜底>.txt            # knowledge card: facts about one guess answer
runtime-profiles/<profile-name>.yaml
registration-tokens/<token-name>.yaml
runtime-profile.example.yaml
raids.txt                                  # one raid ID per line: the table of contents
```

Cards describe an entry itself — a person, an idiom, a landmark — and are the
factual reference a generator embeds in prompts so the model does not invent
facts; how a raid plays with the entry lives in its `workflows/<raid>/` package.

File names are repository-local. Each applyable catalog Resource declares its
immutable, caller-defined Admin identity in `metadata.id`. Every ID-bearing
reference in that catalog contains the exact target Resource ID, so consumers
submit the selected graph without name lookup or reference rewriting.

Generic Admin `metadata.name` is unsupported. RuntimeProfile map keys remain
Peer-facing aliases scoped by that profile. Model and Voice bindings point to
Admin Resource IDs. A Tool binding selects exactly one HTTP Resource ID, fixed
MHS instance/operation, or predefined ClientTool procedure.

Every RuntimeProfile alias — Workflow, Model, Voice
Tool and memory binding keys, and `app_config` keys — is 1-63 bytes of
dot-separated lowercase kebab-case segments, for example
`learn.chinese-poetry-grade1-eino` or `story.animal-kingdom`. Underscores and
uppercase letters are rejected. GizClaw v0.18.15 enforces this when a Server
normalizes the profile, which `gizclaw admin validate` does not do, so
`make test-unit-resources` checks it offline and rejects the legacy nested Workflow collection shape.

Admin IDs are opaque and kind-qualified. They contain at most 1,024 Unicode
characters, preserve internal characters exactly, and cannot have surrounding
whitespace or be the standalone URI dot segments `.` and `..`.

Current drivers:

- `ast-translate`
- `doubao-realtime`
- `eino`

[`runtime-profiles/default.yaml`](runtime-profiles/default.yaml) is the
canonical, applyable public `RuntimeProfile/default`. It selects every public
Workflow in this repository and binds the Model, Voice, and MemoryLayout
aliases needed by that catalog.
[`registration-tokens/default.yaml`](registration-tokens/default.yaml)
publishes the matching `RegistrationToken/default-runtime`; its stable public
client value is `28c4e4e9-a05f-5a7e-815e-9cf9afb6878f`.

### Workspace safety fence

Every player-facing Eino and Doubao Realtime implementation places the Workspace
`safety_fence_level` prompt first in the system message, then a blank line and
the scenario instructions. The Workspace chooses `off`, `general`, or `child`;
the RuntimeProfile owns the complete text in
`spec.safety_fences.{off,general,child}.prompt`. `child` does not inherit `general`.
In 0.23.2 these are Profile-defined string IDs rather than fixed enums. The
`testing` Profile's `off` entry only says to follow the Workflow's own rules;
its existing `general` and `child` policy text is unchanged. Ordinary Giztests
select `off` explicitly, while the child boundary tests select `child`. A Profile
with fence definitions requires a selection; omitting it is not an implicit off.
Player Workflows still receive only the selected Profile text through the
standard placeholder, without fallback policy inside the Workflow.

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

```yaml
# Doubao Realtime instructions; GizClaw substitutes and trims the result
instructions: |
  ${input.safety_fence}

  Original scenario instructions.
```

Eino input keys become template variable names; no extra State field is
needed. All current player prompts use `f_string`: `{safety_fence}` is the
variable, while `{{` and `}}` escape literal braces. This formatter does not trim the prompt. With no Profile fence
definitions and no selection, the empty prefix becomes exactly two newlines.
The testing Profile's named `off` instead inserts its neutral prompt. We retain the existing
formats rather than change every template to remove that whitespace. Future
`go_template` prompts can use `{{if .safety_fence}}{{.safety_fence}}`, a blank
line, then `{{end}}` immediately before the original text; `jinja2` can use
`{% if safety_fence %}{{ safety_fence }}`, a blank line, then `{% endif %}`.
These conditional forms omit the separator when the fence text is empty. Realtime drivers
substitute `${input.safety_fence}` and trim the result, so Doubao Realtime
leaves no leading blank lines for empty fence text; the dotted name is not expanded as an
environment variable by `gizclaw admin apply`.

Only player replies receive the variable, including every narrator/character
and each alternative response prompt. Player-visible conclusions are replies too. Internal JSON classifiers,
routing, memory extraction, and summaries do not receive it. Tester Workflows
play the user and do not receive the fence. Existing scenario safety rules
remain part of the scenario even at `off`.

`make test-unit-resources` runs `scripts/test/safety_fences.py` and its fixture
tests before schema validation. Discovery includes every Workflow YAML under
each raid, excluding Tester/Giztest files. Realtime instructions must start
with `${input.safety_fence}` and a blank line; `ast-translate` is exempt because
GizClaw gives it no system prompt entry, and any other driver fails until its
coverage is reviewed.
The check follows Eino prompt outputs consumed by published text ChatModels. Every
such prompt must start with its bound fence and a blank line. A graph without
a recognized player reply path fails and needs an explicit coverage review
when adding a new graph shape.

**Runtime dependency:** the fence needs **GizClaw v0.20.2** or later for both
validation and serving; CI now pins v0.27.0 with Profile-defined string IDs. Earlier releases reject Eino's
`input.safety_fence` binding as undeclared.

This contract covers every raid with Eino implementations and
`doubao-realtime`. `ast-translate` has no system prompt entry, so GizClaw
accepts the level without providing a fence to it.

`tests/giztest/safety-fence/chat-assistant.eino.giztest.yaml` checks the
fence end to end: the same request to repeat an insult is answered verbatim in
an `off` Workspace and refused in a `child` Workspace, and both replies are
printed from Workspace history. It needs the fenced `eino-chat-assistant`
and the `testing` profile's `safety_fences` deployed; run it with
`gizclaw test run tests/giztest/safety-fence`. It is outside `make test-e2e`.

### Tools

`tools/` holds Tool resources that a chat Model can call during a turn. The
only one is `volc-web-search` (private resource invoke name `web_search`), an `http_request`
Tool for Volcengine's Doubao Search Custom API
(`https://open.feedcoopapi.com/search_api/web_search`). It authenticates with
`auth.method: volc_search`, so GizClaw reads `search_api_key` from
`volc-credential` (`GIZCLAW_VOLC_SEARCH_API_KEY`) on each call; the key never
appears in the Tool. The schema requires the Model to send `search_type: web`
and `count: 3`, because an HTTP Tool cannot set fixed body fields. An optional
`time_range` (`OneDay`, `OneWeek`, `OneMonth`, `OneYear`) maps to `TimeRange`:
results are ranked by relevance, not date, so “最近/最新” news needs it. The
Tool returns the response's `Result` object.

A RuntimeProfile binds `resources.tools.web.search` to `volc-web-search` and
explicitly injects that alias through
`workflows.general-assistant.toolkit.tool_names`. Both public
profiles and the product example use this GizClaw v0.27.0 contract. The alias
maps to the Model function name `web_search`; the HTTP resource's private
`invoke_name` does not select model identity. Workflow bindings without
`toolkit.tool_names` get no Tools, and Workspace `toolkit.tool_names` can only
narrow that selection. The Workflow resource's legacy `tool_ids` grants no
authority. Eino `chat_model` nodes attach the exposed Tools to each Model call
and let the Model decide when to call them. Only the `general-assistant` binding selects search; its prompt
lists what needs a search (weather, news, dates, prices, “今天/最新”) and what
does not (chat, common knowledge, facts already in the conversation or memory).
`make test-unit-resources` validates `tools/`, and `APPLY=1 make test-e2e`
applies it before the Workflows. The chat-assistant quality tier asks for
live weather and today's date, and fails on an offline refusal such as
“无法联网”.

### Device tools

The public profiles and product example also bind nine inner Tools for Chat:

| Profile alias | Fixed source |
| --- | --- |
| `screen.get` / `screen.brightness` | MHS `display.main`, read / write `brightness_percent` |
| `light.get` / `light.brightness` | MHS `led.status`, read / write `brightness_percent` |
| `music.status` | ClientTool `audioplayer.get` |
| `music.playlist` | ClientTool `audioplayer.playlist.get` |
| `music.play` / `music.stop` | ClientTool `audioplayer.play` / `audioplayer.stop` |
| `workflow.switch` | ClientTool `run.workspace.set` |

`spec.mhs.v0.devices` declares the H106 screen and status-light instance IDs.
Products with different hardware must replace the manifest and matching Tool
bindings. Only `brightness_percent` is exposed for writes; H106 does not support
the generic HWD `enabled` field. H106 accepts brightness in 10-percent steps;
the generated HWD schema bounds integers to 0–100, while the device enforces
its step constraint. Tool descriptions require clarification instead of silent
rounding. These aliases are injected only into
`general-assistant`, alongside `web.search`. The runtime generates argument
schemas and dispatches directly to the current authenticated Peer. There are no
synthetic Admin Tool resources or HTTP calls back to GizClaw.

Configured capability and observed support are separate. The current device
must report the MHS instances/write fields and installed ClientTool handlers.
Unknown, unsupported or offline capabilities remain discoverable through
`server.tool.list/get` with `available: false` and an unavailability reason,
and are omitted from model Tool definitions.

Music plays the existing device playlist. Song selection first reads that
playlist and uses its zero-based index; it does not search for music or generate
media URLs. Program selection uses a bound Profile `workflow_name` alias.
Omitted/false `kickoff` selects the program without starting opening speech;
true requires an explicit request for the new agent to speak first.

Chat also selects `toolkit.verification_model: eino-chat-assistant.model`.
GizClaw v0.27.0 uses a separate model request to check device-operation intent
and final replies against conversation and Tool results. These checks add
latency and provider cost, and buffer final text until accepted. The normal
Chat model still emits native ToolCalls; this is not a Match node.

Chat also has a deterministic cancellation guard over real user History.
A bare percentage after a cancelled brightness request produces a clarification
without entering the model or invoking any Tool. Only a new explicit brightness
request reopens the numeric follow-up; assistant text, state queries and
preferences do not supply that authority. Normal model replies keep streaming
through the graph's first-output mode.

### Runtime alias ownership

The catalog retains `doubao-seed-2-0-lite` unchanged and adds
`doubao-seed-2-1-lite` as a separate Model resource. Existing external profiles
may keep selecting 2.0 Lite; both resource IDs remain available.

Narration and Tester judging use `doubao-seed-2-1-lite-260915` through the
`doubao-seed-2-1-lite` Model resource in both public RuntimeProfiles. Thinking
is disabled by default; the supported values are `enabled` and `disabled`.
Tester judges allow 1024 output tokens so longer reviews can include a verdict.
The speech input path still uses ASR; this Model remains text-only.

RuntimeProfile Model and Voice aliases are opaque flat keys. Dots make
ownership visible; they do not create nested maps, fallback, wildcard, or
prefix lookup. Workflow-owned slots use the canonical Workflow
`metadata.id` as their namespace:

```text
<Workflow metadata.id>.<role>
```

`asr` is the only shared Model alias, and every ASR-capable Workflow uses it.
MemoryLayout policies describe the extraction scope and instructions for each
supported provider. For self-hosted Mem0, the service owns the extraction Model
and embedding configuration; the RuntimeProfile binds only its endpoint and
optional API key. MemoryLayouts have no catalog extraction Model aliases.

Each Raid can otherwise select its own Model independently, even when several
slots currently bind the same Model resource:

| Workflow `metadata.id` | Model alias |
| --- | --- |
| `doubao-realtime-conversation` | `doubao-realtime-conversation.model` |
| `eino-chat-assistant` | `eino-chat-assistant.model` |
| `ast-translate-ja-zh` | `ast-translate-ja-zh.model` |
| `ast-translate-ko-zh` | `ast-translate-ko-zh.model` |
| `ast-translate-zh-en-auto` | `ast-translate-zh-en-auto.model` |
| `ast-translate-zh-es` | `ast-translate-zh-es.model` |
| `ast-translate-zh-fr` | `ast-translate-zh-fr.model` |
| `ast-translate-zh-ja` | `ast-translate-zh-ja.model` |
| `ast-translate-zh-ko` | `ast-translate-zh-ko.model` |
| `eino-murder-mystery` | `eino-murder-mystery.model` |
| `eino-journey-history` | `eino-journey-history.model` |
| `eino-journey-memory-recall` | `eino-journey-memory-recall.model` |
| `eino-journey-memory-async` | `eino-journey-memory-async.model` |
| `eino-story-aesop` | `eino-story-aesop.model` |
| `eino-story-alice` | `eino-story-alice.model` |
| `eino-adventure-space-rescue` | `eino-adventure-space-rescue.model` |
| `eino-adventure-monster-maze` | `eino-adventure-monster-maze.model` |
| `eino-adventure-castle-mystery` | `eino-adventure-castle-mystery.model` |
| each `eino-learn-chinese-poetry-grade*` Workflow | `eino-learn-chinese-poetry-grade<N>.model` |
| each `eino-learn-math-grade*` Workflow | `eino-learn-math-grade<N>.model` |
| each `eino-learn-science-grade*` Workflow | `eino-learn-science-grade<N>.model` |
| `eino-learn-chinese-stories` | `<Workflow>.model` |
| `eino-learn-chinese-words` | `<Workflow>.model` |
| each `eino-guess-*` Workflow | `eino-guess-<subject>.model` |

Voice roles use the same Workflow namespace:

| Workflow `metadata.id` | Voice roles |
| --- | --- |
| `doubao-realtime-conversation` | `assistant` |
| `eino-chat-assistant` | `assistant` |
| each `ast-translate-*` Workflow | `translator` |
| `eino-murder-mystery` | `game-master`, `housekeeper`, `chef`, `heir`, `lawyer` |
| each `eino-story-*` Workflow | `storyteller` plus every title-specific character role declared by its `raid.json` |
| each `eino-adventure-*` Workflow | `adventure-guide` plus every scene-specific character role declared by its `raid.json` |

Eino spoken implementations declare these additional Voice roles:

| Workflow `metadata.id` | Voice role |
| --- | --- |
| each `eino-story-*` Workflow | `storyteller` |
| each `eino-adventure-*` Workflow | `adventure-guide` |
| each `eino-learn-*` Workflow | `tutor` |
| each `eino-guess-*` Workflow | `host` |
| `eino-journey-history`, `eino-journey-memory-async`, `eino-journey-memory-recall` | `narrator` |

Each alias is `<Workflow metadata.id>.<role>`. Both public RuntimeProfiles bind each alias to its declared role Voice.
Journey's three Eino variants accept text and push-to-talk input and synthesize
spoken output. Like every Eino voice adapter, they select the shared
`asr` Model alias; custom RuntimeProfiles must bind it alongside their Voice aliases.

For example, Journey resolves `eino-journey-memory-async.narrator` exactly.
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

RuntimeProfile Workflow bindings are a flat map. Each original catalog grouping
is retained as an opaque tag, with IDs, i18n, model/voice/memory aliases and
app_config unchanged. Tag selectors use intersection semantics in GizClaw.

MemoryLayouts include an independent `mem0_self_hosted` policy for GizClaw v0.26.0
and later. A `mem0_self_hosted` RuntimeProfile connection selects its own `scope`
and `custom_instructions`; Cloud categories, multilingual and decay settings stay
in `mem0`. Endpoint, authentication, models and pgvector provisioning belong to
the deployment and the self-hosted service.

The public MemoryLayout catalog is organized by reusable scenario:

- `user-chat-with-assistant` stores durable user conversation context in the owner Peer's
  shared memory scope for Mem0 Cloud, self-hosted Mem0, and Volc Mem0. Other layouts explicitly
  select the Workspace scope for each implementation, so story, adventure, and
  learning state stays private to each Workspace.
- `story-teller` separates Graph-written progress from narrated continuity.
- `adventure` stores player-visible investigation state, discoveries,
  interviews, and explicit corrections.
- `learner` stores the child's stated grade, items actually taught, answered
  and open questions, and explicit corrections for `learn-*` raids.

Knowledge-extension raids use the `learn-<subject>-<topic>` naming scheme and
bindings tagged `category:learn`. Each one embeds a verified knowledge card in its
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

### Guessing-game raids

The `guess` category is a yes-or-no guessing game: the host secretly holds a
target (a historical figure, a physics word, …), the child asks yes-or-no
questions, and each correct guess climbs one named level. Levels do not map to
school grades, so children of any age play the same package and simply stop at
different levels. There is one raid per subject; subjects whose answers depend
on the child's culture are split by region and named `guess-<subject>-<region>`
(for example `guess-history-figures-cn`), while universal subjects carry no
region (`guess-physics-terms`). A product picks its regional content when its
RuntimeProfile is assembled; both public profiles bind the Eino Workflows in the
bindings tagged `category:guess` as `guess.<subject>[-<region>]-eino`.

The catalog has ten guess raids: `guess-history-figures-cn` (the only regional
one), `guess-chinese-idioms` (idioms and the folk stories behind them, for
Chinese speakers anywhere), `guess-world-figures`, `guess-physics-terms`, `guess-chemistry-terms`,
`guess-math-terms`, `guess-animals`, `guess-body-health`,
`guess-world-landmarks`, and `guess-inventions-discoveries`. Each has ten named
levels and about 144 answers. They all target kindergarten to high school
(`raids-age-v2`: `preschool`, `child`, `teen`): level 1 suits kindergarten and
the levels climb through primary, middle and high school.

The packages are Eino-only. Eino keeps no hidden state between turns, so each
level's puzzles are a fixed list and every turn rebuilds the game from the
spoken History: the latest `谜题来啦！第 N 关…，第 K 题。` (or `Puzzle time!
Level N, …, puzzle K.`) opening names the level and the puzzle counter, and the
counter walks the level's list without repeats. Every turn makes one model call.
The control script recognises names, aliases and whole-name Mandarin homophone
transcriptions, a give-up, and a hint request. A matched correct guess goes to
`read-winning-reply` with the already decided announcement, without the raw
guess or conversation for the model to rejudge. Other questions activate the
current puzzle's own prompt node. Its instruction privately supplies the same
fixed answer every turn; its card supplies the facts. The host can use established
knowledge beyond the card and recognise an equivalent guess, while keeping the
answer secret until the round ends. It replies in the child's current language,
Chinese or English.

Each puzzle has a knowledge card, `cards/guess/<subject>/<谜底>.txt` (`<subject>` is the raid ID without `guess-`): one
`字段：值` line per field, in the order of that raid's `_template.txt`, ending
with three prewritten small hints. The Workflow gives every card its own prompt
node; the control script only picks the node for the current puzzle, so the
host reads that one card with the private fixed-answer instruction. `workflows/<raid>/puzzles.json` keeps the level order (card names
per level), level titles, judge and hint guidance, and the scripted test route.
Run `python3 scripts/guess/generate.py` to refresh the Workflow, Tester,
manifest, README, and Giztests; `make test-unit-guess` regenerates every package in a
temporary directory, fails on drift, and replays the game-state scenarios in
`scripts/guess/cases.py` through the Starlark interpreter GizClaw uses.

### Historical-figure raids

The `figure` category lets a child talk with a historical person who tells
their own life in the first person, one chapter per life stage, and then stays
for free conversation. It reuses the chaptered story contract below. The
child's choices may send the person down a path they did not take; what stays
fixed is knowledge: the person only knows their own era, and later legends are
told as legend. The catalog has twelve: `figure-li-bai`, `figure-confucius`,
`figure-sima-qian`, `figure-su-shi`, `figure-zhang-qian`, `figure-li-shizhen`,
`figure-marie-curie`, `figure-einstein`, `figure-da-vinci`, `figure-edison`,
`figure-nightingale` and `figure-galileo`. Each ships one implementation,
continuous Eino multi-role narration, and the default profile binds it in the
bindings tagged `category:figure` as `figure.<key>`.

Facts and script are kept apart. `cards/figure/<人物>.txt` is a knowledge card
about the real person — era, life events, the people around them, works, famous
lines, later legends and what they cannot know — embedded in the prompt as the
factual reference so the model does not invent them. `workflows/<raid>/figure.json`
is the raid's script: chapters, cast, opening and free-talk topics.
`python3 scripts/figure/generate.py` builds each package from the two;
`make test-unit-figure` regenerates every package in a temporary directory and
fails on drift. See [`scripts/figure/README.md`](scripts/figure/README.md) for the
fields.

The public story catalog contains 19 titles, each with original and multi-role
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
the next “继续”, “好”, “要” or “进入下一章” enters the adjacent chapter. The last chapter ends by asking whether to
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

Original Eino stories preserve the story/state contract with
one `text/plain` primary output synthesized by the `storyteller` default Voice.


The multi-role variants of 19 stories and 11 adventures use continuous audiobook narration in Eino: one narration LLM emits 300–600 characters per ordinary turn, with
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
allowed. The prompt names the voiced markers and states that everyone else has
no Voice: people outside the cast, characters from the source work and
companions the model would invent are quoted inside a `【旁白】` paragraph.
Chapter headings and the closing question carry a marker too, and actions or
moods go into narration instead of a bracketed stage direction before a line.
AudioDock reads an unconfigured `【…】` aloud in the default Voice and keeps
the previous Voice for an unmarked paragraph, so either fault puts a line in
the wrong Voice. `voice_adapter.speaker_voices` maps these names to existing aliases;
`default_voice` is the narrator alias. AudioDock strips configured markers from
device text, serializes audio and prefetches the next segment. Interruption
cancels current and pending segments. This requires **GizClaw v0.18.12**.
`murder-mystery` retains its existing single-speaker routing contract on both
engines: a selector script picks the host or one witness for each turn, and the
Eino variant branches into that speaker's prompt in front of one model.

The Eino variants retain ASR, existing voice slots and matching role Voice resources
in `default` and `testing` RuntimeProfiles. Chapter controls and investigation
phase rules feed the single narration LLM instead of selecting a speaking node.

Workflows and `raid.json` reference only Voice aliases named
`eino-<raid>-mr.<role>` for multi-role variants. Original aliases retain their Workflow namespace. Narrator slots retain
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

Each Layout defines portable Mem0 Cloud, self-hosted Mem0 and Volc Mem0
policies. Both public profiles select `driver: mem0` and
`connection.type: mem0_self_hosted`. Set `GIZCLAW_MEM0_ENDPOINT` and
`GIZCLAW_MEM0_API_KEY` in the consuming environment before applying a Profile;
`.env.example` declares empty values only. The endpoint must be reachable by the
consuming Server. Configure the self-hosted service's LLM, embedding and vector
store separately; these belong to the service, not to a RuntimeProfile.

Graph-authoritative `memory_observe.facts` writes require direct-fact support.
Self-hosted Mem0 accepts multiple direct facts in one observation, preserves
attributes and complete scope, and owns batch idempotency and resumable retries.
Cloud/Volc Mem0 retain a single-fact direct-import limit, so a multi-fact Workflow
needs a compatible binding. Layout policy alone does not prove extraction,
recall, provider access or latency. These bindings do not import or migrate
previous business data.

[`runtime-profile.example.yaml`](runtime-profile.example.yaml) remains a
complete one-assistant composition example with native Model, Voice, Tool and
Memory bindings. It is validated offline and is applied only when a consuming
product explicitly selects it.

The MemoryLayout definitions require a GizClaw build containing the MemoryLayout contract
merged by [GizClaw #590](https://github.com/GizClaw/gizclaw/pull/590).

## GizClaw 0.27.0 compatibility

The catalog requires **GizClaw v0.27.0** for configuration validation and serving.
CI pins that release and its published package SHA256; native contract tests use
the matching immutable Go module. Flowcraft was retired upstream in
[GizClaw #1451](https://github.com/GizClaw/gizclaw/pull/1451). Current catalog
Workflows use native Eino Prompt, ChatModel, typed State, branches, History and
Memory. The retired driver, Memory policy and Store connections are absent.

Both public RuntimeProfiles use a flat `spec.workflows` map. Public aliases,
i18n, age ratings and bare/category tags retain their identities; entries now
resolve to their existing Eino implementations. Exact tag matching remains AND.
Workspace creation names only the alias. Model, Voice, Tool and Memory ownership
remains explicit. Retired implementation aliases and extraction Model slots are
removed. Chat selects HTTP search and inner device Tools through the Profile's
`web.search` alias and per-Workflow injection list. Product-owned Profiles must
configure that selection when upgrading; the old Workflow fixed-ID list no
longer grants search access.

Memory uses the self-hosted Mem0 connection described above. Server-owned Eino
History and optional persistent State use `services.agent_host.persistence.history_store`
and `services.agent_host.persistence.state_store`. Existing database contents are not
rewritten by these catalog files. An environment must validate its bindings and
perform real recall/reload acceptance before activating this catalog.

## Static resource validation

Raids uses the released GizClaw binary as the only authority for declarative
Resource format validation. With GizClaw v0.27.0 or later on `PATH`, validate
every applyable catalog Resource with:

```sh
make test-unit-resources
```

Use `GIZCLAW=/path/to/gizclaw make test-unit-resources` to select an explicit
binary. The target validates each YAML file under the applyable Resource
directories independently, checks every RuntimeProfile alias against the
Server's alias syntax, and then validates the
declarative Giztest corpus with `gizclaw test validate`. It also validates
`runtime-profile.example.yaml`. It is offline: it does not use a GizClaw context, contact Server, or mutate
resources.

Checks and generators are Python 3 behind the shell Make entry points; only the
routing gate invokes native Starlark through its Node.js coordinator and Go. The Python scripts need PyYAML and the Guess generator needs pypinyin, both pinned in `scripts/requirements.txt`:

```sh
python3 -m pip install -r scripts/requirements.txt
```

Every public Make target dispatches to the same-named script under
`scripts/<group>/<target>.sh`; the Makefile itself only declares targets,
default variables, and exports. `make help` lists the complete surface:
`test-unit-resources`, `test-unit-learn`, `test-unit-guess`, `test-unit-figure`,
`test-unit-voices`, `test-unit-chat-assistant`, `test-e2e`, and
`test-e2e-chat-assistant`. CI runs each
`test-unit-*` target as its own step; there is no aggregate target.

`make test-unit-chat-assistant` loads the shipped Chat Workflow, profiles, Tool
and quality probe inputs into the GizClaw v0.27.0 Eino runtime. A scripted Model
and HTTP transport fixture replace the external providers. The real Tool
catalog and AgentHost ToolInvoker resolve the shipped Profile alias; the HTTP
executor must receive the mapped search request, return an unpredictable result,
and feed it into the final answer. A fabricated weather/date answer is rejected
when no search ran; a casual turn makes no search request. The completed turn's
Memory observation must retain both user input and assistant output in one
two-fact write, without waiting for Memory completion. The real self-hosted
Mem0 adapter submits that batch to a local HTTP fixture so its batch request,
source identity and scope contract are covered. This target requires Go 1.26.4 and downloads
pinned Go modules on the first run; it uses no provider credentials or live
deployment. This text/HTTP suite disables CGO and does not test native audio
codecs. It also checks both public Profiles and the product example, that
unselected Workflows receive no Tools, and that omitted/empty Profile selection
or an empty Workspace selection prevents search. Device transport fixtures
exercise generated MHS/ClientTool schemas, fixed target/procedure dispatch and
unpredictable returned receipts. Missing/out-of-range values, target/procedure
overrides, unsupported H106 fields, unbound programs, unavailable capabilities
and revoked selections must not dispatch. These deterministic checks do not run
the live semantic verifier or qualify physical hardware. Its source and checksums are maintained under
`scripts/test/chat-assistant/`.

`make test-e2e-chat-assistant` starts disposable Docker Server/Edge containers
using the released GizClaw v0.27.0 image, plus pinned Mem0 and PostgreSQL images.
It applies the complete original default/testing closure, runs real Doubao
conversations against Giztest's typed MHS/ClientTool handlers, and then runs
the unchanged Chat smoke, quality and soak files. Generated cases check exact
targets, parameters and call counts after each user turn, missing-slot follow-up,
cancellation, music playlist selection, failure replies, Workflow switching,
Workspace narrowing and isolation between two Peers. The 28 scenarios run on
both public Profiles, three times each by default. Static CI validates their
56 generated documents without running providers.

```sh
RAIDS_CHAT_E2E_CREDENTIAL_FILE=/path/to/provider.env make test-e2e-chat-assistant
```

The input file supplies the six `GIZCLAW_VOLC_*` variables declared in
`.env.example`; values stay in process/container environments. The harness
archives generated Giztest inputs, full synthetic reply/device receipts,
source hashes and container logs under `tests/giztest/reports/raids-chat-*/`.
It removes its own containers, networks, volumes and ephemeral admin identities
on completion. It does not Apply to the configured Dev/E2E deployment or qualify
physical H106 hardware. `RAIDS_CHAT_E2E_REPEAT`, `RAIDS_CHAT_E2E_FILTER` and
`RAIDS_CHAT_E2E_STANDARD=none|smoke|quality|soak|all` select focused reruns;
`PARALLEL` controls simultaneous tasks.

Chat and Journey reply length is not a pass/fail metric. Numeric brevity hints
are judged by their intent and content, without exact counting; exact-answer
instructions retain literal matching. `test-unit-resources` runs
`scripts/test/test_reply_lengths.py` through native Starlark to accept longer or
shorter complete replies while retaining exact-answer and fact/correction checks.

For static schema validation, the target exports a fixed non-secret placeholder
for each empty variable declared by `.env.example`. It never reads or requires
real provider credentials; `.env.example` remains the maintained list of
allowed Credential and Tenant placeholders and validation fails if that file
contains a populated value.

The target also checks the manifest → speaker mapping → both RuntimeProfiles →
Voice resource chain, distinct role Voices and matching bindings across engines.
For 42 continuous-narration raids it verifies a single narration LLM, configured
Chinese markers, 300–600-character story probes, clean text, complete serial
audio and zero underruns. First-response gates remain unchanged. Quality keeps
safety, transitions, choice endings and correction/recovery contracts; soak
keeps the relay/reload structure. Limited administrative/safety replies retain
their original bounds. Quality budgets are 30 minutes for these longer stories.

Each raid supplies a version-1 `routing-cases.json`. The gate executes actual
native Eino Starlark against state and content-control
assertions. Single-speaker naming/order assertions have been removed from the
42 story/adventure/figure fixtures; murder mystery retains its existing native tests. Python,
Node.js and a local Go toolchain with cached Starlark dependencies are required;
Go module downloads are disabled. Offline validation cannot establish real
provider voice switching, timing, interruption or audible continuity.

Passing this check establishes schema, binding, and deterministic routing
contracts, not live behavior. CI pins the immutable v0.27.0 Linux package
and verifies its published SHA-256 digest before validation.
`make test-unit-voices` separately requires exactly 635 MiniMax Voice files and exactly one
`model: speech-2.6-turbo` field in each. Per-file schema validation alone does
not prove other runtime-only requirements such as cross-resource references or
aliases resolve, provider credentials work, or a live Server
will accept and run the complete catalog. Apply, runtime, `make test-e2e`,
release, and Beijing Default E2E remain separate evidence.

## Raid packages

Every scenario is one package directory `workflows/<raid>/`: one Workflow per
engine implementation (`eino.yaml`, `eino.multi-role.yaml`, …), the scenario's single
original relay Tester (`test.yaml`, id `<raid>-test`), a `raid.json` manifest, and a
README. `raid.json` declares the implementations and the slots each needs —
model aliases, voice aliases, Tool aliases, MemoryLayout — without binding them to concrete
resources; rating (`raids-age-v2`), category, and tags make the catalog
filterable. It is descriptive metadata for consumers and reviewers, not an
input to a generator: `runtime-profiles/default.yaml` and
`runtime-profiles/testing.yaml` stay hand-written, and adding a raid to a
profile means adding its Workflow to the flat map with category tags and declaring the model and
voice aliases the manifest lists.

The audio-only `ast-translate` (category `translate`, one implementation per
language pair) and `doubao-realtime` packages speak through their driver rather
than a voice adapter and have no Tester or soak tier, so their manifests omit
`tester` and register only smoke and quality tests. Figure raids ship only an Eino
multi-role implementation, so their manifests omit `tester` and declare the
multi-role Tester under `testers`.

### Age rating

`rating.age` lists every life stage a raid suits, youngest first, each at most
once. `raids-age-v2` allows only these five stages:

| Stage | Audience | Ages |
| --- | --- | --- |
| `preschool` | preschool children | 3–5 |
| `child` | primary-school children | 6–11 |
| `teen` | teenagers | 12–17 |
| `adult` | adults | 18–59 |
| `senior` | older adults | 60+ |

A general tool such as an assistant lists all five. `rating.content` separately
names content advisories such as `mild-peril` or `mystery-death`.

### Raid list

[`raids.txt`](raids.txt) at the repository root is the table of contents: one
raid ID per line, sorted, for every package under `workflows/`. Read
`workflows/<id>/raid.json` for its title, rating, category, and tags. After
adding or removing a raid, run `python3 scripts/test/raid-manifests.py` to
rewrite the list; `make test-unit-resources` fails when it is stale, when a
package lacks a `raid.json`, or when a manifest uses any other age value.

## Declarative live tests

Live tests use `tests/giztest/{smoke,quality,soak}/<raid>.<implementation>.giztest.yaml`, one implementation per file, named after its Workflow file. There are **340 tier files**: **116 smoke**, **116 quality**, and **108 soak**. The **75 device** files, the two external H106 files and the `safety-fence` end-to-end file remain separate, for **418 `.giztest.yaml` files** total; generated reports are excluded. Selected files run concurrently with `gizclaw test run --parallel N`.

- **smoke** measures speed, latency and responsiveness, including complete audio and independent first-response probes.
- **quality** enforces deterministic quality and safety guardrails, including transitions, corrections, language and role boundaries. Independent suite responses run in parallel and finish together within the existing file budget; long Tester relays live in soak.
- **soak** runs long conversations between the Tester and target Workflow, including reload and memory continuity.
- **device** replays the H106 entry flow for every story, adventure, figure and Journey implementation: “开始”, “我选第一个”, “继续”, leave and re-enter (`server.run.stop` + reload), “继续上次的内容”, “开始”. Every reply must end with a question; original stories must enter chapter 2 on “继续”, resume there, and restart at chapter 1. The files are generated by `python3 scripts/test/device-flow.py`, are not registered in `raid.json`, and run with `make test-e2e TIER=device`.

The audio-only `ast-translate` and `doubao-realtime` targets have no soak protocol. Figure raids are Eino multi-role only. Journey tests its three Eino implementations against equal gates, including recall; its history-only implementation has no recall exemption.

```sh
make test-e2e TIER=smoke RAID=story-aesop
make test-e2e TIER=quality RAID=all
make test-e2e TIER=soak RAID=journey-guide
make test-e2e TIER=device RAID=all
```

Set `GIZCLAW_TEST_ENDPOINT` and `GIZCLAW_TEST_REGISTRATION_TOKEN` for live runs. Defaults are `TIER=all RAID=all PARALLEL=4 APPLY=0`; H106 is excluded. `REPORT` selects the output JSON. `APPLY=1` retains its existing behavior: apply the entire testing closure with the Admin context before running the selected files.

`make test-unit-resources` validates schemas, tier inventory, manifest registration, Voice/role closure, internal routing fixtures and native Journey parity offline. It checks client idle gaps (180s scheduling budget, including cleanup) and compares the three Journey variants for complete inputs, assertions, captures, timeouts and relay plans after normalizing client identifiers and Workspace implementation settings. `make test-unit-voices` checks the Voice catalog.

Smoke retains the 2-second first-text / 3-second first-audio probes and the original complete-response gates. Complete streams additionally require closed, non-overlapping audio, zero underruns and a nonnegative minimum playback buffer under Giztest’s 500ms prebuffer model; packet gaps remain diagnostic evidence. The CLI must support `/audio_integrity` and `/audio_pacing`. Necessary role setup can exceed the two-minute target; file budgets do not relax per-step gates. A failure stops subsequent steps: skipped steps are not passes, and cleanup is reported separately. See the [test guide](tests/giztest/README.md) for the full layout, selection rules and Tester protocol.

## Catalog behavior notes

Default General Assistant intentionally keep Memory extraction
asynchronous. Same-Workspace turn continuity and reload recall come from the
GizClaw Eino History store; deployments must configure
`services.agent_host.persistence.history_store`. Memory supplies longer-lived
semantic recall and must not become a per-turn response barrier.

[Murder Mystery](workflows/murder-mystery/README.md) remains a free-investigation
`adventure`, rated **teen, adult / mystery-death**. Its host handles openings, evidence
checks, corrections, reasoning, provisional accusations, and conclusions.
The housekeeper, chef, Shen Zhiqiu (沈知秋), and lawyer answer individual
interviews in first person using their own testimony and public dialogue;
they do not receive the host's private truth or raw recall notes. The host does
not impersonate witnesses. The Eino variants retain the 26-response investigation
regression and five-role audio and handoff/leakage-guard tests; the Eino
variants rebuild state each turn, using their declared History and Memory contract: the latest shoe size stated in History is authoritative, recalled
facts cover turns History no longer holds, and a fact is written only on a turn
that states a size, so an unrelated turn cannot overwrite a correction.

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

Release `v0.18.0` selects Eino for the public Chat and stable Journey entries,
adds Profile-bound Chat web search, and validated against GizClaw v0.24.2.
Self-hosted Mem0 requires the current runtime for Chat's single-node two-fact writes;
the catalog does not split observations according to the chosen provider.

Release `v0.2` includes the public `chatroom` and `pet-care` system Workflows
for Desktop consumers.

Release `v0.3.0` is the first catalog release using scenario MemoryLayouts,
the historical graph payload and storage contracts. Its archive is not
compatible with the current runtime.

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

Original story, adventure and learn Eino Workflows use their Workflow-scoped default Voice for the complete primary text output; multi-role Eino variants add character Voice switching. The Eino implementations use ASR for paced RealTime audio input. Journey Eino history, asynchronous-memory and recall variants also retain ASR and the narrator default Voice. RuntimeProfiles bind these aliases to their declared role Voice.

The smoke RealTime probes require complete text/audio output and separate 2-second text / 3-second audio first responses for TTS-capable implementations. Offline checks validate Eino Voice ownership, manifest declarations and resolution in both RuntimeProfiles alongside tier parity and multi-role Voice closure.
