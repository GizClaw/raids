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

[`runtime-requirement.yaml`](runtime-requirement.yaml) lists the Model and
Voice aliases these workflows require from a RuntimeProfile. It intentionally
does not select concrete resources or providers.

## Scope

This repository contains public `kind: Workflow` resources. RuntimeProfile,
Credential, ProviderTenant, Model, Voice, Workspace, registration tokens, and
secrets remain outside this repository.
