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
stable identity. Voice catalogs and Workflows keep one grouping level for
navigability:

```text
credentials/<credential-name>.yaml
tenants/<tenant-name>.yaml
models/<model-name>.yaml
memory-layouts/<layout-name>.yaml
petdefs/<petdef-name>.yaml
voices/<tenant-name>/<voice-id>.yaml
workflows/<driver>/<raid-name>.yaml
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
| `pet-care` | `pet-care.model` |

Voice roles use the same Workflow namespace:

| Workflow `metadata.id` | Voice roles |
| --- | --- |
| `doubao-realtime-conversation` | `assistant` |
| `flowcraft-chat-assistant` | `assistant` |
| each `ast-translate-*` Workflow | `translator` |
| `flowcraft-murder-mystery` | `game-master`, `detective` |
| `flowcraft-journey-guide` | `narrator`, `origin-narrator`, `heaven-narrator`, `pilgrimage-narrator`, `trials-narrator`, `kingdoms-narrator`, `arrival-narrator` |
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
language or provider used by the translation Model. The default
Chinese-to-Japanese and Chinese-to-Korean Workflows select the public MiniMax
system Voices `Japanese_CalmLady` and `Korean_CalmLady`, which the
[MiniMax system Voice catalog](https://platform.minimaxi.com/docs/faq/system-voice-id)
classifies for those languages. These bindings add `MiniMaxTenant/minimax-cn`
and its environment-owned Credential to the default dependency closure; Raids
contains no credential value.

The public MemoryLayout catalog is organized by reusable scenario:

- `user-chat-with-assistant` stores durable user conversation context.
- `story-teller` separates Graph-written progress from narrated continuity.
- `adventure` stores Graph-authoritative state, discoveries, choices, and
  progress audit facts.
- `pet-care` stores qualitative relationship, owner, knowledge, and shared
  event memory without treating Gameplay numbers as long-term memory.

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
Japanese and Korean Voices, and fails closed when the default adoption pool has
no distributable PIXA closure. A merged source change is not a published
release; consumers must pin the later canonical tag and validate its archive.

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

The public PetDef manifests currently reference restricted Codex artwork that
is not redistributed by this repository. The `v0.4.2` default adoption pool is
therefore empty: the PetDefs remain available to products authorized to publish
matching objects, but an ordinary Default connection cannot randomly adopt one
and then receive a PIXA 404. Any future Default pool entry must resolve to a
regular, non-symlink `assets/pet-defs/<safe-basename>.pixa` file in the same
versioned Raids archive. Deployment tooling must be authorized to upload that
exact object before applying the profile.

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

Each Voice directory name matches its Tenant `metadata.id`, so catalogs with
different providers, endpoints, or regions remain separate. For example,
`voices/minimax-cn/`, `voices/minimax-global/`, and
`voices/volc-cn-beijing/` correspond to those three Tenant resources.

PetDef resources contain only machine-readable character, voice, and visual
configuration. Their localized display names and descriptions belong to the
corresponding `spec.resources.pet_defs.<alias>.i18n` binding in the consuming
RuntimeProfile. A PetDef alias does not make the PetDef eligible for adoption;
the RuntimeProfile pool and archive-owned asset closure do that explicitly.

Workspace instances, real credential values, secrets, private Workflows,
product- or hardware-specific RuntimeProfiles and RegistrationTokens, and other
user or runtime state remain outside this repository.
