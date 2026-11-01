# Figure package generation

Run `python3 scripts/figure/generate.py` from the repository root after editing a
`workflows/figure-*/figure.json`, a card in `cards/figure/`, or anything in
`templates/`. Pass raid IDs to regenerate a subset; `--out <directory>` writes to a
separate root. `make test-unit-figure` regenerates every package in a temporary
directory and fails on drift. The routing suite, device-entry file and Voice chain of
the generated packages are checked with the story raids by `make test-unit-resources`.

Each figure raid ships one implementation, Eino multi-role (`eino.multi-role.yaml`),
with its multi-role Tester, `raid.json`, `routing-cases.json`, README and one
smoke, quality, soak and device Giztest.

- `cards/figure/<人物>.txt` is the knowledge card: facts about the real person, not
  the raid. One `字段：值` line per field, exactly in the order of
  `cards/figure/_template.txt` (copy it to add a person); list fields separate items
  with `；`. In standard mode the whole card is embedded in the prompt as the factual reference, so the
  model follows it for dates, places, people, works and quotes and says it cannot
  remember what the card does not cover. `后人传说` items are `名称——说明`; their
  names are the legends the figure must tell as legend. `身边的人` must describe the
  companion and both guests.
- `workflows/<raid>/figure.json` is the raid's script: titles, summary, premise,
  rating and tags, the four chapters (Chinese title and English README goal), the
  cast, the chapter-one opening and the free-conversation topics. The raid ID is
  `figure-<figure.key>`, and `figure.name` names the card.
- A package may explicitly opt into `narration: {mode: compact}`.
  Its prompt script selects complete typed units from the original card; line and
  item provenance stay in the generated source index. Selected units are static,
  sharing each phase's 1,000-character static budget with its instructions,
  labels, largest fence, deployed metadata and fixed roles/JSON envelopes.
  There is no manually
  shortened reference, source truncation, model answer replacement or extra state.
  Chinese bigrams, ASCII words, generic English field terms and cast aliases rank
  the source; History only supplies retrieval context and is preserved in full.
  This limited lexical lookup does not guarantee factual model compliance.
  Compact mode uses History/Memory for progress instead of the standard
  chapter controller, and omits mechanical chapter, heading and fixed-closing gates.
  It keeps one public streaming reply. An internal native-audio intent call
  selects plot/research and the reply language; it emits no scene or story text.
  Existing legacy routing
  fixtures remain visible and are not used as factual string-matching judges.
- The cast has a fixed shape: the figure and a companion appear in every chapter, and
  exactly two guests arrive after chapter 1. Every role has one `view` per chapter it
  appears in — a first-person motive (`want`), a temper, and what it does in that
  chapter (`action`, without a leading `第N章` or trailing punctuation) — rendered
  into the per-chapter role table.
- `opening.intro` must start with `我是<name>` and introduce the companion,
  `opening.guests` announces both guests, `opening.question` asks the chapter-one
  question with two named options, and `opening.choice` is one of those options
  verbatim.
- Card and script text lands inside Starlark string literals and Eino `f_string`
  templates, so it must not contain ASCII quotes, backslashes, braces, backticks or
  line breaks; the generator rejects them.
- `templates/` holds the Workflow, the Tester, `routing-cases.json`, the README and
  the four Giztests with `@@SLOT@@` placeholders; `generate.py` fills them and builds
  `raid.json` itself. `routing-cases.json` slots that stand for a whole value
  (`@@ROLES_2@@`, `@@GUEST1_FIRST@@`) take the slot's JSON type.
  `control-narration.yaml`, `instructions.standard.txt` and
  `build-prompt.standard.yaml` preserve standard behavior. The opt-in
  `eino.compact.yaml` uses `structured.compact.star` to select whole source units
  and build a bounded source-grounded context after the internal intent call.
  The selected plot or research model streams the public reply; only research
  can use Search for uncertain facts.
  There is no paragraph JSON, output deduplication or second response stream.
  Fixed speaker tags, complete source units, native metadata and framing share the
  1,000-character static budget. History, progress memory and returned Search data
  remain runtime input. Five transient fields replace the previous six; there
  is no additional scene state or prescribed action sequence. `evidence.py` creates
  lossless source units and lexical indexes, never historical claims.

Runtime profiles stay hand-written: add `eino-<raid>-multi-role` to
`raidtest-targets`, `<raid>-test-multi-role` to bindings tagged `category:raidtest-testers`, `figure.<key>`
(pointing at `eino-<raid>-multi-role`) to bindings tagged `category:figure` of `default.yaml`,
the `eino-<raid>-mr.model` and `<raid>-test.model` aliases, and a distinct Voice for
`eino-<raid>-mr.storyteller` and each role in both profiles. Add the raid ID to
`raids.txt`.
