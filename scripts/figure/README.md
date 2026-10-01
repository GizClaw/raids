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
  with `；`. The whole card is embedded in the prompt as the factual reference, so the
  model follows it for dates, places, people, works and quotes and says it cannot
  remember what the card does not cover. `后人传说` items are `名称——说明`; their
  names are the legends the figure must tell as legend. `身边的人` must describe the
  companion and both guests.
- `workflows/<raid>/figure.json` is the raid's script: titles, summary, premise,
  rating and tags, the four chapters (Chinese title and English README goal), the
  cast, the chapter-one opening and the free-conversation topics. The raid ID is
  `figure-<figure.key>`, and `figure.name` names the card.
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

Runtime profiles stay hand-written: add `eino-<raid>-multi-role` to
`raidtest-targets`, `<raid>-test-multi-role` to bindings tagged `category:raidtest-testers`, `figure.<key>`
(pointing at `eino-<raid>-multi-role`) to bindings tagged `category:figure` of `default.yaml`,
the `eino-<raid>-mr.model` and `<raid>-test.model` aliases, and a distinct Voice for
`eino-<raid>-mr.storyteller` and each role in both profiles. Add the raid ID to
`raids.txt`.
