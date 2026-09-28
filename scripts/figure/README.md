# Figure package generation

Run `python3 scripts/figure/generate.py` from the repository root after editing a
`workflows/figure-*/figure.json` or anything in `templates/`. Pass raid IDs to
regenerate a subset; `--out <directory>` writes to a separate root.
`make test-unit-figure` regenerates every package in a temporary directory and
fails on drift. The routing suites, device-entry files and Voice chain of the
generated packages are checked with the story raids by `make test-unit-resources`.

- `workflows/<raid>/figure.json` holds everything that belongs to one person:
  titles, summary, premise, rating and tags, the four chapters (Chinese title and
  English README goal), the cast, the legends that must be told as later legend,
  the chapter-one opening and the free-conversation topics. The raid ID is
  `figure-<figure.key>`.
- The cast has a fixed shape: the figure and a companion appear in every chapter
  (they are the only characters of the single-voice implementations), and the
  multi-role implementations add exactly two guests who arrive after chapter 1.
  Every role has one `view` per chapter it appears in — a first-person motive
  (`want`), a temper, and what it does in that chapter (`action`, without a
  leading `第N章` or trailing punctuation) — rendered into the multi-role
  per-chapter role table.
- `opening.intro` must start with `我是<name>` and introduce the companion,
  `opening.guests` announces both guests (multi-role only), `opening.question`
  asks the chapter-one question with two named options, and `opening.choice` is
  one of those options verbatim; the quality Giztest answers with it.
- Chinese text lands inside JS and Starlark string literals and Eino `f_string`
  templates, so it must not contain ASCII quotes, backslashes, braces, backticks
  or line breaks; the generator rejects them.
- `templates/` holds the four Workflows, both Testers, `routing-cases.json`, the
  README and the sixteen Giztests with `@@SLOT@@` placeholders; `generate.py`
  fills them and builds `raid.json` itself. `routing-cases.json` slots that stand
  for a whole value (`@@ROLES_2@@`, `@@GUEST1_FIRST@@`) take the slot's JSON type.

Runtime profiles stay hand-written: add the four implementations and the
multi-role variants to `raidtest-targets`, both Testers to `raidtest-testers`,
`figure.<key>` to the `figure` collection of `default.yaml`, the `.model`,
`-mr.model` and `-test.model` aliases, and a distinct Voice for the storyteller
and each role under both `<engine>-<raid>` and `<engine>-<raid>-mr` in both
profiles. Add the raid ID to `raids.txt`.
