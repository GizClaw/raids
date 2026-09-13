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
workflows/<raid-name>/test.yaml            # the scenario's single Tester Workflow (id <raid-name>-test)
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
| `flowcraft-murder-mystery` / `eino-murder-mystery` | `game-master`, `housekeeper`, `chef`, `heir`, `lawyer` |
| `flowcraft-journey-guide` | `narrator` |
| each `flowcraft-story-*` / `eino-story-*` Workflow | `storyteller` plus every title-specific character role declared by its `raid.json` |
| each `flowcraft-adventure-*` / `eino-adventure-*` Workflow | `adventure-guide` plus every scene-specific character role declared by its `raid.json` |
| each `flowcraft-learn-chinese-poetry-grade*` Workflow | `tutor` |
| each `flowcraft-learn-math-grade*` Workflow | `tutor` |
| each `flowcraft-learn-science-grade*` Workflow | `tutor` |
| `flowcraft-learn-chinese-stories` | `tutor` |
| `flowcraft-learn-chinese-words` | `tutor` |

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
options. After the chapter's choice and its consequences, the narrator tells
the child once that “进入下一章” continues; Flowcraft also accepts that phrase
as a request for the adjacent chapter.
The Wizard of Oz additionally preserves its explicit English chapter-one
restart and established English opening on both implementations.

### Narrator and character voices

All 31 multi-voice raids have paired Flowcraft and Eino implementations:
19 stories use one narrator plus three to five characters; the 11 adventures
use one narrator plus three characters (four in `adventure-space-rescue`);
`murder-mystery` uses one host/narrator plus four witnesses. Characters enter
only in their eligible chapters or scenes. Each turn selects one speaker;
openings, transitions, corrections, safety management, and stage assessment
belong to the narrator. Explicit requests select the first eligible named
speaker in text order, excluding negated requests. Story choice names alone
remain choices, not speaking requests. Roles speak directly in first person
without speaker labels and stay within their knowledge boundaries.

Flowcraft reconstructs story state after reload and routes to one published
speaker output, using `voice_adapter.node_voices` for its Workflow-scoped Voice
alias. Eino preserves one `text/plain` primary model output: an upstream
Starlark selector writes `selected_speaker`, and
`voice_adapter.state_voices` maps that string State to a Voice alias. Both
engines retain ASR and use the same Voice resource for the same role in both
`default` and `testing` RuntimeProfiles, with distinct Voice IDs within each
implementation. Narrator defaults preserve `.storyteller`, `.adventure-guide`,
and `.game-master` slots. Eino state-selected TTS requires **GizClaw >= v0.18.9**
([#1270](https://github.com/GizClaw/gizclaw/issues/1270)).

The shared casting pool contains these 10 Volc Voice IDs. Their full resource
IDs use the prefix `volc-tenant:volc-cn-beijing:`; pool labels describe casting
and are not RuntimeProfile aliases. Per-raid READMEs list the exact roles,
chapter eligibility, aliases, and bindings.

| Pool label | Voice ID | Casting |
| --- | --- | --- |
| narrator | `zh_female_shaoergushi_mars_bigtts` | Warm adult female narrator for stories and adventures |
| clear | `zh_male_jieshuoxiaoming_uranus_bigtts` | Clear, rational male scholar, guide, or companion |
| gentle | `zh_female_wenroushunv_uranus_bigtts` | Gentle adult female caregiver, scientist, or mature character |
| child | `zh_male_naiqimengwa_mars_bigtts` | Young boy, small animal, or sprite |
| mystery | `zh_male_changtianyi_mars_bigtts` | Adult male mystery host or composed character |
| girl | `ICL_zh_female_huoponvhai_tob` | Lively girl or quick-witted companion |
| youth | `ICL_zh_male_qingshuangshaonian_tob` | Youthful male protagonist or active companion |
| solid | `ICL_zh_male_hanhoudunshi_tob` | Steady adult male, large animal, or reliable teammate |
| grandma | `ICL_zh_female_heainainai_tob` | Kind older woman or elder guide |
| grandpa | `ICL_zh_male_youmodaye_tob` | Humorous older man, captain, mentor, or housekeeper |

The five `ICL_*` Voices have **not yet been verified online for this tenant**.
Catalog bindings and offline checks do not establish provider access, actual
selected Voice IDs, latency, or sound quality; synthesis logs and listening
remain separate acceptance evidence.

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
Resource format validation. With GizClaw v0.18.9 or later on `PATH`, validate
every applyable catalog Resource with:

```sh
make test-unit-resources
```

Use `GIZCLAW=/path/to/gizclaw make test-unit-resources` to select an explicit
binary. The target validates each YAML file under the applyable Resource
directories independently, and then validates the
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

The target also checks the manifest → published node / Eino State selector →
Voice alias → both RuntimeProfiles → Voice resource chain, unique Voice IDs
within each implementation, matching role Voices across engines, and registered
role probes with EOS/audio and first-response gates. Each of the 31 migrated
raids supplies a version-1 `routing-cases.json`. The gate executes its actual
Flowcraft JavaScript and Eino Starlark against shared speaker expectations,
covering naming, negation, order, eligibility, management priority, choices,
old memory, and transitions. Expanded Voice mappings or `state_voices` without
a routing fixture fail validation. The runner needs Ruby, Node.js, and a local
Go toolchain with cached Starlark dependencies; Go module downloads are disabled.

Passing this check establishes schema, binding, and deterministic routing
contracts, not live behavior. CI still pins the immutable v0.18.2 Linux package
and verifies its published SHA-256 digest; that pin predates `state_voices`
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
relay Tester (`test.yaml`, id `<raid>-test`), a `raid.json` manifest, and a
README. `raid.json` declares the implementations and the slots each needs —
model aliases, voice aliases, MemoryLayout — without binding them to concrete
resources; rating (`raids-age-v1`), category, and tags make the catalog
filterable. It is descriptive metadata for consumers and reviewers, not an
input to a generator: `runtime-profiles/default.yaml` and
`runtime-profiles/testing.yaml` stay hand-written, and adding a raid to a
profile means binding its Workflow in a collection and declaring the model and
voice aliases the manifest lists.

## Declarative live tests

[`tests/giztest`](tests/giztest/README.md) holds every live Raids test as one
`gizclaw.test/v1alpha1` document: **324 `.giztest.yaml` files**, counted from
this checkout (excluding README and generated reports). These include 106
candidate/Tester relays across story, adventure, learn, Journey, and Murder
Mystery targets, one assistant relay, 100 paced-audio RealTime roundtrips,
62 dual-engine role probes across all 31 multi-voice raids, 38 story transition
contracts, two Murder Mystery handoff/knowledge-boundary contracts, two Wizard
of Oz English restart cases, and 13 benchmark/realtime/translation/external
cases. File counts do not multiply configured qualification repeats.
`gizclaw test run tests/giztest --parallel N` isolates each
file and repeat in its own ephemeral Peers and Workspaces and schedules them
through one global worker pool; `make test-e2e` runs them against a provisioned
deployment and `make test-unit-resources` validates the corpus offline. Each scenario's single Tester Workflow (`workflows/<raid>/test.yaml`, id `<raid>-test`, shared by every engine implementation) speaks the
`workspace_relay` text protocol: they drive the scripted route, audit the
deterministic contracts over their own History. Long story routes end bounded
segments in `CHECKPOINT PASS` and the final segment in `PASS`; each role probe
requires complete text/audio EOS and non-empty synthesized Opus, then applies
independent 2-second first-text and 3-second first-audio gates without waiting
for the second probe's EOS. Provisioning stays outside the runner: `APPLY=1 make test-e2e`
applies the catalog, the Testers, the `testing` RuntimeProfile, and the
`testing-runtime` token with the selected Admin context before running.

CI is pinned to GizClaw v0.18.2, which drops the retired gameplay surface
(PetDefs, the `pet` driver, and RuntimeProfile system Workflow roles) and
names the Workspace initiative enum `CONVERSATION_PARAMETERS_INITIATIVE_*`.
The merged multi-voice catalog requires v0.18.9 or later as described above.
Earlier contracts originated in v0.7.19 for stories and v0.6.0 for the
declarative runner (GizClaw #916, #921, #923). The bounded
story-role first-response gates require the GizClaw #991/#992 contract first
released in v0.7.13. GizClaw #994/#997 removed reload-time RuntimeProfile
dependency revalidation in v0.7.16. The modality-selective first-response
contract from GizClaw #1003/#1004 is first released in v0.7.19 and lets
Eino RealTime tests enforce a text gate independently of audio acceptance.
Reload is reported separately from the measured first-response gates. This corpus
replaces the retired `tools/raidtest` Go runner: validating one locally edited
Workflow is now `APPLY=1 make test-e2e RAID=<raid>/<engine>`, which applies that
raid package and the testing closure before running its scenario.

Each story/adventure RealTime document synthesizes a short Chinese Opus fixture
and sends it at 20 ms pacing through a warmed `WORKSPACE_INPUT_MODE_REALTIME`
Workspace. Flowcraft requires complete assistant text and audio plus a separate
2-second text / 3-second audio first-response sample. Existing Eino RealTime
files still set `require_audio: false` and require complete text plus a separate
2-second text first-response sample. This is their current test scope, not an
Eino TTS limitation: dual-engine `roles` files verify complete role audio and
2-second text / 3-second audio first response for all 31 multi-voice raids.

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
not impersonate witnesses. Both engines retain the 26-response investigation
regression and add five-role audio and handoff/leakage-guard tests.

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
the enforcement point. The public `ICL_uranus_*_tob` entries still use
`seed-tts-2.0`; `seed-icl-2.0` is reserved for account-private trained Voices
and remains outside this snapshot.

Each Voice directory name matches its Tenant `metadata.id`, so catalogs with
different providers, endpoints, or regions remain separate. For example,
`voices/minimax-cn/`, `voices/minimax-global/`, and
`voices/volc-cn-beijing/` correspond to those three Tenant resources.

Workspace instances, real credential values, secrets, private Workflows,
product- or hardware-specific RuntimeProfiles and RegistrationTokens, and other
user or runtime state remain outside this repository.
