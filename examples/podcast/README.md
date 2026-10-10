# Continuous podcast example

This example starts a Chinese podcast about everyday science. Say “开始” to
start, specify another topic to redirect it, or say “停一下” to stop. After an
interruption, “继续” resumes from the preceding History. It generates new
content repeatedly without asking the listener to keep saying “继续”.

Playback stays continuous on one output StreamID. Each model generation saves
its own Agent History entry with that section's corresponding text and audio;
entries become available while the podcast is still running. User interruption
cancels the active generation and saves its delivered prefix as the current
entry. Completed entries stay separate. Later requests resume or redirect the
podcast and continue saving one entry per generation.

## Runtime requirement

Use a GizClaw build from commit
[`f9ddb10bef2ed1cf427749d618e62c5f871c942c`](https://github.com/GizClaw/gizclaw/commit/f9ddb10bef2ed1cf427749d618e62c5f871c942c)
or a later version containing that change. It implements
`spec.eino.conversation.continue_from`, backed by the Eino transformer's
`Config.ContinueFrom`. The repository's pinned v0.27.0 release does not support
this property. The example has its own Profile and validation target so it can
be exercised with the accompanying engine change before being selected by the
public catalog.

The Graph generates a short section per execution. The runtime repeats it
within the same turn, preserving the last eight generated sections as model
context. Before generating the next section, it waits for text and TTS audio
delivery to the server consumer. Backpressure keeps provider synthesis and model
generation from accumulating indefinitely ahead of playback. The Graph's
eight-step limit applies to each execution, not to the duration of the podcast.

The Prompt ends with the current real listener request. The controller removes
its duplicate from the bounded history first. This keeps one current request
per model call and prevents a provider from treating the previous assistant
section as an unfinished prefix. Sections target 150–200 Chinese characters.

## Validate and run

From the repository root, select the continuation-enabled binary:

```sh
make test-unit-podcast GIZCLAW=/path/to/gizclaw
```

The example Profile references the catalog's `doubao-seed-2-1-lite`,
`volc-bigasr-sauc`, and Qingxin female Voice resources. Provision their real
Credential, Tenant, Model and Voice dependencies on a development Server
before applying the example:

```sh
gizclaw admin apply -f examples/podcast/eino.yaml
gizclaw admin apply -f examples/podcast/runtime-profile.yaml
```

Use a development RegistrationToken bound to `podcast-demo`. Create a Workspace
with the `podcast` Workflow alias and select it in the client. Text,
push-to-talk and realtime input use the same narration loop; the Profile binds
external ASR separately for the two audio modes.

Try “开始，讲讲为什么天空是蓝的”, leave it running across several model
generations, then interrupt with “停一下”. Inspect Workspace History: the
preceding podcast should already contain several Agent entries, one per model
generation with its matching audio. The new user request and brief pause
acknowledgment follow these sections. “继续” should create a new uninterrupted
narration, and “换个话题，讲太空” should redirect it.

`test-unit-podcast` validates schema, stop commands, the bounded context window
and the safety-fence binding without contacting providers. Runtime continuation
and persisted Workspace History require the accompanying GizClaw engine tests;
real provider audio and physical-device interruption are separate acceptance.
