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
runtime-profiles/<profile-name>.yaml
registration-tokens/<token-name>.yaml
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

[`runtime-profiles/default.yaml`](runtime-profiles/default.yaml) is the
canonical, applyable public `RuntimeProfile/default`. It selects every public
Workflow in this repository and binds the Model, Voice, and PetDef aliases
needed by that catalog. [`registration-tokens/default.yaml`](registration-tokens/default.yaml)
publishes the matching `RegistrationToken/default-runtime`; its stable public
client value is `default`.

[`runtime-profile.example.yaml`](runtime-profile.example.yaml) remains a
documentation-only composition example with unresolved Voice placeholders. It
is not discovered or applied as a catalog resource.

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

The archive contains one generated top-level directory. Consumers locate the
kind directories relative to that root rather than depending on its generated
name.

## Default runtime bootstrap

The public default bootstrap contract consists of two ordinary Admin resources:

- `RuntimeProfile/default` defines the public product composition.
- `RegistrationToken/default-runtime` exposes the stable client bootstrap value
  `default` and targets that profile.

Each Server owns its own independent copies of these resources. Reusing the
public token string does not share Server data, credentials, identities,
Terraform state, or lifecycle between Desktop, dev, production, or other
installations. The Server endpoint is selected separately by the client.

Consumers apply the catalog in dependency order:

1. Apply Credential and Tenant definitions with deployment-owned values.
2. Apply Models, Voices, PetDefs, and Workflows.
3. Apply `RuntimeProfile/default`.
4. Apply `RegistrationToken/default-runtime`.

Applying the RegistrationToken before the RuntimeProfile fails because the
profile reference is unresolved. Reapplying identical resources is idempotent.
Products may omit or override the public defaults and may install additional
product- or hardware-specific profiles and tokens.

## Scope

This repository contains public Credential, Tenant, Model, PetDef, Voice,
Workflow, RuntimeProfile, and RegistrationToken source resources. It publishes
the default runtime bootstrap contract while leaving every applied resource
instance under the ownership of its Server and deployment tooling.

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

Workspace instances, real credential values, secrets, private Workflows,
product- or hardware-specific RuntimeProfiles and RegistrationTokens, and other
user or runtime state remain outside this repository.
