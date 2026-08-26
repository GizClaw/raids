# GizClaw Raids

[![CI](https://github.com/GizClaw/raids/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/GizClaw/raids/actions/workflows/ci.yml?query=branch%3Amain)

Reusable resource loadouts for [GizClaw](https://github.com/GizClaw/gizclaw)
AI workflows.

**Raids** stands for **Resources for AI Drivers & Scenarios**. Like a raid
loadout in a game, each collection brings together the workflows, models,
voices, credentials, and provider definitions needed for an AI scenario.

## Layout

Resources are grouped by kind. Credential, Tenant, Model, MemoryLayout, and
PetDef resources are flat because their `metadata.id` already provides the
stable identity. Voice catalogs keep one grouping level per Tenant; Workflows are grouped by
scenario (raid), with one file per engine implementation plus the scenario's
Tester, metadata, and README:

```text
credentials/<credential-name>.yaml
tenants/<tenant-name>.yaml
models/<model-name>.yaml
memory-layouts/<layout-name>.yaml
petdefs/<petdef-name>.yaml
voices/<tenant-name>/<voice-id>.yaml
workflows/<raid-name>/<engine>.yaml        # one directory per scenario: flowcraft.yaml, eino.yaml, ...
workflows/<raid-name>/test.yaml            # the scenario's single Tester Workflow (id <raid-name>-test)
workflows/<raid-name>/raid.json            # scenario metadata: rating, category, tags, voices, models, testing
workflows/<raid-name>/README.md            # human-readable play and test route
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
- `chatroom`
- `doubao-realtime`
- `eino`
- `flowcraft`
- `pet`

[`runtime-profiles/default.yaml`](runtime-profiles/default.yaml) is the
canonical, applyable public `RuntimeProfile/default`. It selects every public
Workflow in this repository and binds the Model, Voice, MemoryLayout, and
PetDef aliases needed by that catalog.
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
| `pet-care` | `pet-care.extract` |

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
| `pet-care` | `pet-care.model` |

Voice roles use the same Workflow namespace:

| Workflow `metadata.id` | Voice roles |
| --- | --- |
| `doubao-realtime-conversation` | `assistant` |
| `flowcraft-chat-assistant` | `assistant` |
| each `ast-translate-*` Workflow | `translator` |
| `flowcraft-murder-mystery` | `game-master` |
| `flowcraft-journey-guide` | `narrator` |
| each `flowcraft-story-*` Workflow | `storyteller` plus two title-specific character roles declared by its `raid.json` |
| `flowcraft-adventure-space-rescue` | `adventure-guide` |
| `flowcraft-adventure-monster-maze` | `adventure-guide` |
| `flowcraft-adventure-castle-mystery` | `adventure-guide` |
| `pet-care` | `pet` |

For example, Journey resolves `flowcraft-journey-guide.narrator` exactly, and
Pet Care resolves `pet-care.pet` exactly. Different scoped aliases may bind the
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
- `pet-care` stores qualitative relationship, owner, knowledge, and shared
  event memory without treating Gameplay numbers as long-term memory.

The public story catalog contains 19 titles, each with paired Flowcraft and
Eino implementations. Every title owns an independent four-chapter bible,
player role, character knowledge boundaries, transition and ending conditions,
fact/legend/fiction rules, child-safety rules, correction precedence, durable
clues, unresolved hooks, and anti-repetition policy. A transition happens only
when the current choice satisfies the adjacent chapter condition; entering a
chapter emits its localized title once, while ordinary turns never repeat it.
The Wizard of Oz additionally preserves its explicit English chapter-one
restart and established English opening on both implementations.

Flowcraft reconstructs `story_contract_v1` after reload, selects narrator or
one of two in-scene characters, and routes to exactly one published model node.
The three nodes resolve three distinct Workflow-scoped Voice aliases; chapter
transitions, invalid roles, and fallback use the compatible `storyteller`
alias. Eino implements the same player-visible story and state contract with
one `text/plain` primary output. It remains text-only because GizClaw v0.7.7
selects `node_voices` from fixed Graph output nodes and cannot dynamically
choose a Voice for that single primary output.

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

The `pet-care` resource keeps Pet domain integration in its outer `pet` driver
and declares a complete, replaceable Flowcraft Workflow beneath `spec.pet`.
Its outer `spec.memory` selects `pet-care`; the nested Workflow does not own a
second Memory alias.
The `friend_chatroom` and `group_chatroom` system roles share the same
`chatroom` Workflow; direct and group mode remains Workspace state.
These definitions require a GizClaw build containing the MemoryLayout contract
merged by [GizClaw #590](https://github.com/GizClaw/gizclaw/pull/590).

## Static resource validation

Raids uses the released GizClaw binary as the only authority for declarative
Resource format validation. With GizClaw v0.7.0 or later on `PATH`, validate
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
`test-unit-resources`, `test-unit-voices`, and `test-e2e`. CI runs each
`test-unit-*` target as its own step; there is no aggregate target.

For static schema validation, the target exports a fixed non-secret placeholder
for each empty variable declared by `.env.example`. It never reads or requires
real provider credentials; `.env.example` remains the maintained list of
allowed Credential and Tenant placeholders and validation fails if that file
contains a populated value.

Passing this check means each file conforms to the Resource schema embedded in
that GizClaw release. CI pins the immutable v0.7.0 Linux package and verifies
its published SHA-256 digest before validation. `make test-unit-voices`
separately requires exactly 635 MiniMax Voice files and exactly one
`model: speech-2.6-turbo` field in each. Per-file schema validation alone does
not prove other runtime-only requirements such as cross-resource references or
aliases resolve, PIXA assets exist, provider credentials work, or a live Server
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
`gizclaw.test/v1alpha1` document: 64 paired candidate/Tester relays (every
story, adventure, Journey, and Murder Mystery target on both engines), the
19 Flowcraft story role probes, the Wizard of Oz dual-engine English restart,
the default assistant, Journey, Pet Care,
Doubao realtime, and AST translation routes, the Journey TTFT benchmark, and
the historical 3×/5× qualification repeats. `gizclaw test run tests/giztest --parallel N` isolates each
file and repeat in its own ephemeral Peers and Workspaces and schedules them
through one global worker pool; `make test-e2e` runs them against a provisioned
deployment and `make test-unit-resources` validates the corpus offline. Each scenario's single Tester Workflow (`workflows/<raid>/test.yaml`, id `<raid>-test`, shared by every engine implementation) speaks the
`workspace_relay` text protocol: they drive the scripted route, audit the
deterministic contracts over their own History. Long story routes end bounded
segments in `CHECKPOINT PASS` and the final segment in `PASS`; each role probe
requires text/audio EOS and non-empty synthesized Opus. Provisioning stays outside the runner: `APPLY=1 make test-e2e`
applies the catalog, the Testers, the `testing` RuntimeProfile, and the
`testing-runtime` token with the selected Admin context before running.

The story contract and CI are pinned to GizClaw v0.7.7; the rest of the corpus
requires GizClaw v0.6.0 or later (GizClaw #916, #921, #923). It
replaces the retired `tools/raidtest` Go runner: validating one locally edited
Workflow is now `APPLY=1 make test-e2e RAID=<raid>/<engine>`, which applies that
raid package and the testing closure before running its scenario.

## Catalog behavior notes

Default Pet Care and General Assistant intentionally keep Memory extraction
asynchronous. Same-Workspace turn continuity and reload recall come from the
GizClaw Flowcraft History store; deployments must configure
`services.agent_host.flowcraft.history_store`. Memory supplies longer-lived
semantic recall and must not become a per-turn response barrier.
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
3. Apply Models, Voices, PetDefs, and MemoryLayouts.
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

Raids owns the public PetDef manifests and their stable
`asset://codex/pets/<name>.pixa` references, but it does not distribute the PIXA
bytes. The corresponding bundles are maintained by `GizClaw/pixa` under
`assets/codex-pets/`; GizClaw bootstrap or the consuming deployment resolves
and uploads those assets to the Server for the declared PetDef IDs. A missing
PIXA attachment is therefore a consumer resource-closure failure and must not
be hidden by removing that PetDef from the Raids adoption pool.

The versioned Desktop consumer contract is documented by the
[GizClaw local Server bootstrap guide](https://github.com/GizClaw/gizclaw/blob/ecdb381ea05b629d3a8e5140510ae6e16643f55e/guides/en/developing/apps/wails.md),
which pins the nine bundles from
[`GizClaw/pixa@5fed581`](https://github.com/GizClaw/pixa/tree/5fed581ae87ac3cf4a5a05952d43edebbbed8d9f/assets/codex-pets).
Other consumers must provide an equivalent immutable mapping and upload every
selected PetDef attachment before treating the RuntimeProfile as ready.

## Scope

This repository contains public Credential, Tenant, Model, MemoryLayout,
PetDef, Voice, Workflow, RuntimeProfile, and RegistrationToken source
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

PetDef resources contain only machine-readable character, voice, and visual
configuration. Their localized display names and descriptions belong to the
corresponding `spec.resources.pet_defs.<alias>.i18n` binding in the consuming
RuntimeProfile. A PetDef alias does not make the PetDef eligible for adoption;
the RuntimeProfile pool does that explicitly, while the consuming bootstrap or
deployment owns PIXA attachment closure.

Workspace instances, real credential values, secrets, private Workflows,
product- or hardware-specific RuntimeProfiles and RegistrationTokens, and other
user or runtime state remain outside this repository.
