# Runtime Requirements

Raids contain public Workflow resources, but they do not own a
`RuntimeProfile`. Before installing these workflows, the target RuntimeProfile
must provide the Model and Voice aliases documented below.

Alias names are part of the Workflow contract. Each deployment remains
responsible for binding them to concrete resources, providers, tenants, and
credentials.

## Models

| Alias | Model kind | Used by |
| --- | --- | --- |
| `asr` | `asr` | `flowcraft/chat-assistant`, `flowcraft/journey-guide`, `flowcraft/murder-mystery` |
| `chat` | `llm` | `flowcraft/chat-assistant`, `flowcraft/journey-guide`, `flowcraft/murder-mystery` |
| `extraction` | `llm` | `flowcraft/chat-assistant`, `flowcraft/journey-guide` |
| `realtime` | `realtime` | `doubao-realtime/conversation` |
| `translation` | `translation` | `ast-translate/zh-en-auto`, `ast-translate/zh-es`, `ast-translate/zh-ja`, `ast-translate/zh-ko` |

## Voices

| Alias | Used by |
| --- | --- |
| `assistant-voice` | `flowcraft/chat-assistant` |
| `detective` | `flowcraft/murder-mystery` |
| `doubao-assistant` | `doubao-realtime/conversation` |
| `game-master` | `flowcraft/murder-mystery` |
| `narrator` | `flowcraft/journey-guide` |
| `police-officer` | `flowcraft/murder-mystery` |
| `translator` | `ast-translate/zh-en-auto`, `ast-translate/zh-es`, `ast-translate/zh-ja`, `ast-translate/zh-ko` |

## Deployment Boundary

This repository does not define or distribute:

- RuntimeProfile resources or Collection membership;
- Model and Voice resources or their concrete IDs;
- ProviderTenant or Credential resources;
- registration tokens, Workspace state, or secrets.

Changing a RuntimeProfile binding can select a different compatible Model or
Voice without modifying the Raid Workflow itself.
