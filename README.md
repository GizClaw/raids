# GizClaw Raids

Open source workflow configurations for [GizClaw](https://github.com/GizClaw/gizclaw).

## Layout

Workflow resources are grouped by their `spec.driver` value:

```text
src/<driver>/<raid-name>.yaml
```

The shorter file name is repository-local. Each YAML document keeps its stable
`metadata.name` so existing RuntimeProfile bindings continue to resolve the same
Workflow resource.

Current drivers:

- `ast-translate`
- `doubao-realtime`
- `flowcraft`

[`runtime-requirement.yaml`](runtime-requirement.yaml) is a standard
`kind: RuntimeProfile` resource containing the Workflow, Model, and Voice
bindings required by the bundled Raids.

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

This repository contains public `kind: Workflow` resources and their baseline
RuntimeProfile requirement. Credential, ProviderTenant, Model, Voice,
Workspace, registration tokens, and secrets remain outside this repository.
