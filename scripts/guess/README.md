# Guess package generation

Run `python3 scripts/guess/generate.py` from the repository root after editing a
card in `cards/guess/<subject>/`, a `workflows/guess-*/puzzles.json`, or anything in `templates/`. Pass raid IDs to
regenerate a subset; `--out <directory>` writes to a separate root.
`make test-unit-guess` regenerates every package in a temporary directory,
fails on drift, and runs `cases.py`.
Generation requires `scripts/requirements.txt`, including pinned pypinyin.
It embeds Mandarin character pronunciation equivalents for each raid's
names, so whole-name homophone guesses are resolved by the controller.
Property questions and negations do not use a substring pronunciation match.

`guess-animals` selects `prompt_profile: compact` as a single-workflow sample.
`instructions.compact.star` supplies its turn wording; `instructions.standard.star`
retains the other packages' wording. Both share deck selection and whole-name
matching in `control.star`. The compact game has unlimited questions: it never
counts down or reveals an answer because a quota expires. Before the opening
model call, the controller resolves the deterministic deck position. The existing
`game-route` string field stores only `v1|level|puzzle|phase|hintmask|language`,
and `state_persistence.fields` selects that field, keeping all six declared fields
and one model call. A State store must be configured in GizClaw. A complete
delivered reply commits the cursor; interrupted or failed delivery does not.
Reload and eviction of the opening from bounded History therefore preserve the
same puzzle. Existing conversations without a cursor migrate from their last
available opening once; if both cursor and opening are absent, the game starts
at level 1, puzzle 1. Clearing the Workspace resets the game.

Card nodes retain every factual field while omitting the introductory synopsis.
The compact host can vary its response and lightly tease the guessing strategy,
without mocking the child or adding animal attributes for the joke. A stuck or
discouraged child can receive one prepared hint without explicitly asking; saying
“猜不出来了” is a request for help, not consent to reveal the answer. The controller
supplies only the next unused hint. Numbered Chinese/English markers record a
hint from the delivered reply in the existing three-bit mask; an unused offer
does not consume a hint. Requested and volunteered hints use the same card turn,
so a message asking both an attribute question and for help receives both. The
host can phrase the selected hint naturally, preserving its meaning and marker.
Once all three are used, the
host can recap established clues but cannot invent a fourth. Reply length is diagnostic only for this profile;
fact, secret-keeping, audio and realtime latency assertions remain in place.
Openings, matched wins, give-ups and progress recaps reuse `read-announcement`, which delivers
the controller's decided event without the child's original question. This
prevents an opening or a recap from becoming a fresh guess judgment. Card turns
retain the complete available History. A matched correct guess checkpoints the
next puzzle and higher level in the same turn, congratulates the child, and opens
that puzzle immediately. The highest level remains capped. Equivalent wins
recognized by the model use the same next position, reconciled from the delivered
winning marker on the following turn. Giving up leaves the revealed puzzle open
for discussion until an explicit next/restart command. No state field or model
call is added; the single host model still streams directly.

- `cards/guess/<subject>/<谜底>.txt` (at the repository root; `<subject>` is the raid ID without `guess-`) holds one knowledge card per puzzle: one `字段：值`
  line per field, in the order of `cards/guess/<subject>/_template.txt` (copy the
  template to add a puzzle). The first four fields — 谜底、英文名、别名、简介 —
  feed the control script (guess matching, reveal text); the middle fields go,
  with every name blanked out, into the puzzle's own host prompt node; the last
  field, 小提示, holds three small hints separated by `；` that the script reads
  out one at a time. Values must not contain `{`, `}` or `|`.
- `workflows/<raid>/puzzles.json` owns the subject text, level titles and
  scopes, the card names of each level in selection order, hint guidance, and
  the scripted test route. `tests.first.secret` and `tests.second.secret` must
  name the puzzles that level 1 puzzle 1 and level 2 puzzle 2 select; the
  generator fails if a list edit moves them, and also fails on a listed name
  without a card or a card that no level lists. Optional `tests.first.facts`
  adds yes-or-no fact questions before the correct guess to both quality and
  Tester routes, checking that the answer stays fixed and the host does not
  claim uncertainty about those facts.
  `guess_variants`, `wrong_guess` and `speech_regression` add independent
  quality rounds for natural and homophone guesses, same-answer reveal on
  give-up, and synthesized speech sent through the push-to-talk ASR path.
  Each round uses a fresh Workspace and emits its latest committed reply.
  `english_facts` and `english_wrong_guess` add all-English yes/no, natural
  name-guess and give-up rounds, plus spoken English through the real ASR path.
  Response assertions use `/reply`; `/transcript` is separately retained for
  speech, because Giztest `/text` also contains the child's transcription.
- `templates/control.star` is the Workflow's `control-round` script. The
  generator embeds it, with the puzzle data, into `workflows/<raid>/eino.yaml`;
  GizClaw runs the embedded copy. It rebuilds the game from History, handles
  openings, correct guesses, give-ups and hint requests itself, and otherwise
  activates the current puzzle's card node. Every question turn privately
  supplies that same puzzle's fixed name and aliases to the host. An unmatched
  phrasing can still be an equivalent correct guess; the host must judge it
  against the fixed answer instead of automatically rejecting it. The host
  can answer from established facts absent from the card, and must keep the
  name secret until the round ends. A controller-matched guess uses
  `read-winning-reply`, which receives the decided winning announcement
  without the raw guess or conversation for the model to rejudge.
  Every turn makes one model call.
- `templates/card.txt` wraps a nameless card, `card-node.yaml` is the host
  prompt node that embeds it, and `card-route.yaml` / `card-edge.yaml` connect
  that node from `control-round` to the host model.
- `templates/eino.yaml`, `test.yaml` and the three `*.giztest.yaml` files are
  the Workflow, Tester and tier skeletons.
- `cases.py` replays scripted Histories through the control script with the
  Starlark interpreter GizClaw uses (`scripts/test/test-starlark-routing.sh`),
  and checks that every card node exists and never names its own answer.

Runtime profiles stay hand-written: add `eino-<raid>` to `raidtest-targets` and
bindings tagged `category:guess`, `<raid>-test` to bindings tagged `category:raidtest-testers`, the `.model` and
`-test.model` aliases, and the `.host` Voice in both profiles.
