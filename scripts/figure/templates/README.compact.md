# @@TITLE@@

An interactive late-life @@FIGURE@@ sample. The periods @@CHAPTER_CHAIN@@ provide
historical background, not a prescribed route or fixed dialogue.

Only the present late-life figure and the narrator speak; past people are narrated rather than independently recast. The frame does not physically travel back in time or stage multiple ages of the same person. A hidden native-audio intent node selects research or plot and the reply language. Research turns use only the narrator; ordinary recalled-life turns retain the figure's voice. The active policy is selected, not stacked. The figure recalls experiences in ordinary speech; original verse and its attribution belong to the narrator's sourced explanation. Optional `narrator_units` in the scene evidence marks complete source units outside the legend field whose later testimony belongs to the narrator; it adds no gameplay State or historical assertion.

The internal node uses `chat_model.structured_output` in GizClaw v0.35.7 or later,
returning only `mode` and `language`, with no story text or factual answers. Its native
schema is counted in the static context budget. It reuses the existing answer fields;
invalid output fails explicitly, with no quote repair or free-text fallback. Both models
receive the same original audio and ordered History through typed message placeholders.
The internal control is hidden from public text, speech and History. Exactly one of two answer nodes streams each turn: plot has no function Tool capability,
research has Search available. The existing `first_output` mode publishes the selected
route directly and records its History; the hidden intent output is never published. The native
Search tool is available for uncertain factual questions; known material can be spoken
while unresolved facts are checked. The model must wait for evidence before asserting
the uncertain fact. Search and model compliance still require real dialogue review.

Two typed Prompt paths keep the complete conversation and original current audio.
For plot turns, background precedes the conversation. For research turns, the current
source context and narrator task follow it, so earlier character dialogue is not the
last instruction to continue. The validated intent reuses the completed memory-route
field. Each turn makes an internal intent call followed by the selected answer
model; Search may require further research calls. The two Prompt layouts add no
State fields or model calls of their own. This is an input layout, not an output
label filter or a guarantee of factual correctness.

The source card is preserved as complete, attributed units. A function ranks whole units
against the current question and previous context, then injects those that fit. The compact
biographical boundary always includes lifespan, chronology, disputed claims and legends.
It carries source-card IDs and a source SHA; no test answer or prescribed scene is injected.
History and recalled gameplay describe actual progress, not historical proof.
The neighboring lookup topic comes from the latest figure dialogue, so a later
narrator research answer does not silently choose the next plot topic. Complete
observation records already present as the same user/reply pair in ordered History
are omitted from recalled memory; unknown formats and genuinely older memory stay.

Every expanded static model context includes the selected complete facts, instructions,
fixed voice labels, safety fence, native framing and Search metadata within 1,000 characters.
History, remembered progress and returned Search data are measured separately and retained.
No response-length quota, text deduplication, regex repair or fixed story state is used.

The five Graph fields hold the memory query/route, recalled material, input messages and
answer. The `plot` and `research` outputs are exclusive: only the selected answer node
streams each turn. Voice completion and History ordering retain their usual checks.
Unconfigured characters are narrated in the
narrator's voice; later historical events also belong to the narrator.

The narrator and figure each have predeclared Chinese and English speaker names
bound to the same original Voice alias. These are names for two existing roles,
not extra characters or Voices. Other speaker names remain unconfigured. Routing
aliases are TTS configuration and are not appended as more model instructions.

Generate with `python scripts/figure/generate.py @@RAID@@`. Offline checks cover source
integrity, complete-unit selection, static budgets and full History preservation. They do
not certify factual truth or gameplay quality; real native-voice samples and fresh long
conversations are reviewed separately from technical and model-judge outcomes.

The intent and plot bindings use the native-audio Lite Model with Tool calls disabled;
research uses the existing native-audio Lite Model with Tool calls enabled. This makes
plot turns unable to start Search before speaking, without a regex, fixed opening or
new State. Both answer nodes write the same existing answer field on exclusive paths.

Intent instructions prioritize factual constraints and requests about other people’s
later lives over the surface form of a personal-memory question. The plot policy
contains no instruction to use an unavailable Search Tool: factual verification
belongs to the source narrator. The figure’s speech is limited to experiences and
feelings within the figure’s own lifetime; later biographies and modern objects
belong to the narrator. Compliance is still checked in real dialogue.

This native-audio sample accepts text turns and push-to-talk audio, not realtime
duplex input. Each Profile alias selecting this Workflow must set
`ptt_asr_model: asr`; that independent parallel transcription supplies input.text
and stored History, while both Lite nodes still receive the original audio.
