# Stateful Function Chat

[`eino.function-chat.yaml`](eino.function-chat.yaml) is a conversation/intent pair exposed by both public Profiles as `function-assistant`. It carries the active-task routing idea from the earlier `func-chat` experiment into Eino.

Both agents use upstream `doubao-seed-2-1-lite-260915`, with thinking disabled by default:

| Profile Model alias | Model resource | Purpose |
| --- | --- | --- |
| `eino-function-chat.model` | `doubao-seed-2-1-lite-no-tools` | Conversation agent; tools disabled |
| `eino-function-chat.classify` | `doubao-seed-2-1-lite-no-tools` | Internal route/status decisions; tools disabled |
| `eino-function-chat.intent` | `doubao-seed-2-1-lite` | Multi-turn intent agent; native ToolCall enabled |

## Routing and pending state

Without a pending task, conversation drafting and intent routing start in parallel. Pure chat publishes the conversation reply. Intent handling publishes only the intent agent's reply; the unused chat draft never enters Memory or History. The intent agent also handles any ordinary question accompanying an operation in that same reply.

An intent can remain open across several turns. “我要唱歌” does not authorize immediate playback: the agent clarifies the goal, helps choose an available option, and executes only when the request and parameters are clear. Short answers such as “轻松一点” or “第二首” continue the pending task without calling the conversation agent. An explicit pure-chat detour can use the conversation agent while preserving that task. Completion or explicit cancellation clears it; an orphaned option after cancellation does not authorize replay.

`state_persistence` retains `intent-active`, `pending-context` and `intent-cancelled` in the owning Workspace scope. The Server must configure `services.agent_host.persistence.state_store`. Context contains the first request, latest user input and last intent reply as continuity hints; it grants no new authority. True user History and current device results remain authoritative. Workspace reload uses the same owner/Workspace state.

Internal decisions use finite labels. Unknown idle routing never enables the tool executor; unknown routing during an open task stays with intent. Unknown completion retains the pending task. `CHAT_CANCEL` lets an explicit cancellation plus pure-chat transition clear state without executing tools. Branch-local completion fields and `primary_output_mode: first_output` keep the mutually exclusive publication paths at one visible reply.

## Shared context and tools

Both agents consume the same current utterance and `input.messages`. A common recall step reads `user-chat-with-assistant` memory before routing, and both player prompts receive that identical snapshot. Only the selected reply and the real user input are observed once through the same Memory binding. Speculative drafts and metadata labels are excluded. There is one Workspace conversation/History scope, not a namespace per model node.

The Profile selects nine existing native capabilities: screen/status-light reads and brightness writes, playback state/playlist/play/stop, and bound-workflow selection. MHS targets and writable fields are fixed. ClientTool schemas come from the protocol; observed device capabilities filter availability. H106 sample bindings use brightness steps of ten percent. Other hardware needs matching manifests, bindings and descriptions.

Eino's toolkit and optional `verification_model` are workflow-wide. The no-tools resource suppresses tool definitions on conversation and metadata requests; consumers must preserve those bindings. This is a model-configuration boundary, not a new per-node Runtime permission feature. The single-controller verifier is not enabled because it would demand operations from the conversation agent too. Argument schemas, current-Peer authorization and device validation remain in dispatch.

This implementation is experimental. Both public Profiles passed the dedicated 12-turn stateful trajectory, but the additional Workspace-narrowing scenario still fails: after the screen tools are removed, Seed can claim it adjusted the screen without a successful screen operation. The native toolkit boundary still applies; the Workflow cannot inspect current toolkit/receipts or enable the verifier only on its intent node in Runtime 0.35.18. Prompt instructions have not reliably prevented the false acknowledgement. Runtime also accumulates assistant text across tool rounds, so a premature tool preamble can remain in the selected reply alongside a later correction. Preserve the failing scenario when qualifying changes; a stateful-trajectory PASS does not establish reliable completion wording for unavailable tools.

## Tests

`make test-unit-chat-assistant` uses SDK 0.35.18 with scripted models and real native dispatch. It rebuilds the transformer between turns while retaining external State, History and Memory. Tests prove initial overlap, intent-only continuation, pure-chat detours, reload recovery, completion/cancellation cleanup and no duplicate operations. Unpredictable markers prove both agents receive shared facts and History; only the selected reply is observed once. Local HTTP fixtures verify that only the tool-enabled Model declaration sends tool definitions to the same Seed upstream. On macOS the script runs a static Linux test binary in a network-disabled container.

Standard smoke/quality/soak files are under `tests/giztest/{smoke,quality,soak}/chat-assistant.eino.function-chat.giztest.yaml`. Dedicated real-model documents under [`tests/giztest/function-chat/`](../../tests/giztest/function-chat/) cover both public Profiles. They exercise singing clarification, playlist selection, pure-chat interruption, pending-state reload, selecting the second song, stop, cancellation, orphaned choices, a new device request and shared preference recall. Each turn waits for History and captures flat `/reply`, with exactly one response and one user/assistant History pair. Exact native targets, parameters and cumulative call counts detect unintended operations.

Regenerate with `python3 scripts/test/chat-e2e/function_chat.py`; `--check` validates committed output. With a prepared environment, run the Giztest documents directly:

```bash
gizclaw test run tests/giztest/function-chat
```

For a disposable local environment with real providers and simulated device handlers:

```bash
RAIDS_CHAT_E2E_CREDENTIAL_FILE=/path/to/provider.env RAIDS_CHAT_E2E_REPEAT=1 RAIDS_CHAT_E2E_STANDARD=none make test-e2e-function-chat
```

The runner pins Runtime 0.35.18, uses its SQL Workspace History/State configuration, applies the shipped resource closure to its own Docker Server/Edge and Mem0 project, runs the dedicated documents and selected existing device scenarios, and cleans up. `RAIDS_CHAT_E2E_FILTER` selects existing device case IDs; `RAIDS_CHAT_E2E_STANDARD` optionally adds standard tiers. The complete private provider environment instantiates the unchanged Credential manifest. No production context or cloud provisioning is used.

Evidence stays under ignored `tests/giztest/reports/raids-chat-*/`, with provider values redacted. A simulated-device PASS does not establish physical H106 acceptance.
