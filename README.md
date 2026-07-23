# GizClaw Raids

Reusable resource loadouts for [GizClaw](https://github.com/GizClaw/gizclaw)
AI workflows.

**Raids** stands for **Resources for AI Drivers & Scenarios**. Like a raid
loadout in a game, each collection brings together the workflows, models,
voices, credentials, and provider definitions needed for an AI scenario.

## Layout

Resources are grouped by kind. Credential, Tenant, Model, and PetDef resources
are flat because their `metadata.name` already provides the stable identity.
Voice catalogs and Workflows keep one grouping level for navigability:

```text
credentials/<credential-name>.yaml
tenants/<tenant-name>.yaml
models/<model-name>.yaml
petdefs/<petdef-name>.yaml
voices/<tenant-name>/<voice-id>.yaml
workflows/<driver>/<raid-name>.yaml
runtime-profile.example.yaml
```

File names are repository-local. Each resource keeps its stable `metadata.name`
so references continue to resolve after consumers select and assemble the
resources they need.

Current drivers:

- `ast-translate`
- `chatroom`
- `doubao-realtime`
- `flowcraft`
- `pet`

[`runtime-profile.example.yaml`](runtime-profile.example.yaml) shows the
`kind: RuntimeProfile` contract targeted by
[`GizClaw/gizclaw#486`](https://github.com/GizClaw/gizclaw/issues/486),
using one possible set of system Workflow IDs and Model, Voice, and PetDef
aliases. It is documentation, not a RuntimeProfile published or applied by
Raids. Consuming products own their actual RuntimeProfile, selectable Workflow
collections, and every concrete resource binding; the Voice placeholders are
intentionally left unresolved.

The `pet-care` resource keeps Pet domain integration in its outer `pet` driver
and declares a complete, replaceable Flowcraft Workflow beneath `spec.pet`.
The `friend_chatroom` and `group_chatroom` system roles share the same
`chatroom` Workflow; direct and group mode remains Workspace state.
These definitions require a GizClaw build containing the #486 schema and
runtime contract.

## Download

GizClaw Desktop downloads this repository from GitHub as a source archive. The
current development package is always available from:

```text
https://github.com/GizClaw/raids/archive/refs/heads/main.tar.gz
```

Versioned packages use the corresponding Git tag archive, for example:

```text
https://github.com/GizClaw/raids/archive/refs/tags/v0.1.tar.gz
```

Release `v0.2` includes the public `chatroom` and `pet-care` system Workflows
for Desktop consumers.

The archive contains one top-level directory. Consumers locate
`runtime-requirement.yaml` and `src/` relative to that directory rather than
depending on the generated directory name.

## Desktop consumption

GizClaw Desktop keeps one local `RuntimeProfile/default`. It does not apply
`runtime-requirement.yaml` as a second persisted RuntimeProfile. Instead, the
file is the package requirement used to select and compose the local runtime
contract:

1. Read the system Workflow IDs under `spec.workflows.system` together with any
   product-owned bindings under `spec.workflows.collections`.
2. Load the referenced `kind: Workflow` resources from `src/` by their stable
   `metadata.name`.
3. Require the Model, Voice, and PetDef aliases declared under `spec.resources`
   to be resolvable by the local runtime resources.
4. Apply the selected Workflows before updating the single local
   `RuntimeProfile/default`.

Credentials, provider tenants, concrete local resource provisioning, gameplay
policy, Workspaces, registration tokens, and secrets remain owned by the local
GizClaw installation. A download or validation failure must leave the last
successfully installed package and RuntimeProfile usable.

## Scope

This repository contains public Credential, Tenant, Model, PetDef, Voice, and
Workflow source resources. It does not prescribe how downstream Desktop or
deployment tooling selects, orders, or packages them.

Credential resources define stable names, providers, and body shapes, while
their values remain `${ENVIRONMENT_VARIABLE}` examples. The repository never
contains real credential values. Copy [`.env.example`](.env.example) to the
environment configuration managed by the consuming product or deployment and
fill only the credentials it selects.

Voice files are snapshots of provider system catalogs. Purchased, cloned,
generated, trained, and otherwise account-private voices are excluded. Server
timestamps, account status, and raw provider responses are not source
resources and are also excluded.

Each Voice directory name matches its Tenant `metadata.name`, so catalogs with
different providers, endpoints, or regions remain separate. For example,
`voices/minimax-cn/`, `voices/minimax-global/`, and
`voices/volc-cn-beijing/` correspond to those three Tenant resources.

PetDef resources contain only machine-readable character, voice, and visual
configuration. Their localized display names and descriptions belong to the
corresponding `spec.resources.pet_defs.<alias>.i18n` binding in the consuming
RuntimeProfile.

Workspace instances, registration tokens, secrets, and other user or runtime
state remain outside this repository.
