# Learn package generation

Run `python3 scripts/learn/generate.py` from the repository root after editing
knowledge cards or rendering helpers. Pass raid IDs to regenerate a subset;
`--out <directory>` writes to a separate root. `make test-unit-learn` regenerates
all 20 packages offline and compares every generated file with the catalog.

`subject_*.py` owns curriculum rules, card text, routes, and README content.
`shared.py` renders the common structure using the original
`workflows/adventure-science/{flowcraft,eino,test}.yaml` skeletons. The files in
`templates/` are independent Giztest tier templates; they are not agent system
prompt templates.

The Flowcraft and Eino rendering helpers prepend the Workspace safety fence
to the tutor's system prompt, then a blank line and the subject prompt. The
Eino skeleton supplies `inputs.safety_fence.from: input.safety_fence`, alongside
its existing history and memory bindings; `render_eino` preserves those inputs
while replacing the system template with `{safety_fence}` plus subject text.
`render_flowcraft` similarly prefixes `${board.safety_fence}`. Subject prompt
character counts describe the subject text, excluding the dynamic fence.
`implementation_table` supplies the shared README explanation.

Do not add this variable to `render_tester`, the Tester skeleton, or the
Giztest templates. Regenerating those files must leave their bytes unchanged
for a fence-only edit. See the root [Workspace safety fence contract](../../README.md#workspace-safety-fence)
for `off` whitespace, template syntax, and the required GizClaw binding
support. Run both `make test-unit-learn` and the fence-enabled
`GIZCLAW=/absolute/path/to/gizclaw make test-unit-resources test-unit-voices`.
