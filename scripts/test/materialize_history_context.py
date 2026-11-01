"""Embed the shared input helper in Alice's existing recalled-memory channel."""
from pathlib import Path
import yaml

R = Path(__file__).resolve().parents[2]
P = R / 'workflows/story-alice/eino.multi-role.yaml'
helper = (R / 'scripts/common/history_context.star').read_text()
source = helper + '\ndef run(input):\n    return {"memory": deduplicate_memory(input["memory"], input["history"])}\n'
document = yaml.safe_load(P.read_text())
graph = document['spec']['eino']['graph']
existing = any(n['id'] == 'filter-recalled-memory' for n in graph['nodes'])
node = {'id': 'filter-recalled-memory', 'type': 'script',
        'inputs': {'memory': {'from': 'recalled'}, 'history': {'from': 'input.messages'}},
        'outputs': {'memory': 'recalled'}, 'language': 'starlark', 'entrypoint': 'run', 'source': source,
        'limits': {'max_execution_steps': 200000, 'timeout': '250ms',
                   'max_input_bytes': 4194304, 'max_output_bytes': 4194304}}
# Keep the surrounding hand-authored workflow stable and the Script readable.
node_without_source = {k: v for k, v in node.items() if k not in ('source', 'limits')}
head = yaml.safe_dump([node_without_source], allow_unicode=True, sort_keys=False).rstrip()
head = '\n'.join('      ' + line for line in head.splitlines()) + '\n'
body = '        source: |\n' + ''.join(('          ' + line if line else '') + '\n' for line in source.splitlines())
tail = '        limits: {max_execution_steps: 200000, timeout: 250ms, max_input_bytes: 4194304, max_output_bytes: 4194304}\n'
workflow = P.read_text()
if existing:
    start = workflow.index('      - id: filter-recalled-memory\n')
    end = workflow.index('      - id: build-prompt\n', start)
    workflow = workflow[:start] + head + body + tail + workflow[end:]
else:
    workflow = workflow.replace('      - id: build-prompt\n', head + body + tail + '      - id: build-prompt\n', 1)
    workflow = workflow.replace('      - from: recall-memory\n        to: build-prompt\n',
                                '      - from: recall-memory\n        to: filter-recalled-memory\n      - from: filter-recalled-memory\n        to: build-prompt\n', 1)
yaml.safe_load(workflow)
P.write_text(workflow)
print('Shared exact-history memory filter embedded; existing recalled field reused.')
