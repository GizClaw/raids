# GizClaw Raids

Reusable resource loadouts for [GizClaw](https://github.com/GizClaw/gizclaw)
AI workflows.

**Raids** stands for **Resources for AI Drivers & Scenarios**. Like a raid
loadout in a game, each collection brings together the workflows, models,
voices, credentials, and provider definitions needed for an AI scenario.

## Layout

Resources are grouped by kind. Credential, Tenant, and Model resources are
flat because their `metadata.name` already provides the stable identity. Voice
catalogs and Workflows keep one grouping level for navigability:

```text
credentials/<credential-name>.yaml
tenants/<tenant-name>.yaml
models/<model-name>.yaml
voices/<tenant-name>/<voice-id>.yaml
workflows/<driver>/<raid-name>.yaml
runtime-profile.example.yaml
```

File names are repository-local. Each resource keeps its stable `metadata.name`
so references continue to resolve after consumers select and assemble the
resources they need.

Current drivers:

- `ast-translate`
- `doubao-realtime`
- `flowcraft`

[`runtime-profile.example.yaml`](runtime-profile.example.yaml) is a valid
`kind: RuntimeProfile` example containing only the Model and Voice aliases
required by these Workflows. Product owners define their own Workflow
collections and the rest of their RuntimeProfile policy.

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

The archive contains one top-level directory. Consumers locate
`runtime-requirement.yaml` and `src/` relative to that directory rather than
depending on the generated directory name.

## Desktop consumption

GizClaw Desktop keeps one local `RuntimeProfile/default`. It does not apply
`runtime-requirement.yaml` as a second persisted RuntimeProfile. Instead, the
file is the package requirement used to select and compose the local runtime
contract:

1. Read the Workflow bindings under `spec.workflows.collections`.
2. Load the referenced `kind: Workflow` resources from `src/` by their stable
   `metadata.name`.
3. Require the Model and Voice aliases declared under `spec.resources` to be
   resolvable by the local runtime resources.
4. Apply the selected Workflows before updating the single local
   `RuntimeProfile/default`.

Credentials, provider tenants, concrete local resource provisioning, gameplay
policy, Workspaces, registration tokens, and secrets remain owned by the local
GizClaw installation. A download or validation failure must leave the last
successfully installed package and RuntimeProfile usable.

## Scope

This repository contains public Credential, Tenant, Model, Voice, and Workflow
source resources. It does not prescribe how downstream Desktop or deployment
tooling selects, orders, or packages them.

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

Workspace instances, registration tokens, secrets, and other user or runtime
state remain outside this repository.
