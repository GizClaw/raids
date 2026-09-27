import glob
import os
import re
import sys

import yaml

# Check prompt placement, not model compliance. Trace the catalog's published
# models and the Flowcraft draft -> board.getVar -> published script pattern.
FLOWCRAFT_PREFIX = '${board.safety_fence}\n\n'
# Realtime drivers substitute ${input.safety_fence} in instructions and trim
# the result, so an off fence leaves no leading blank line. The dotted name
# is not expanded as an environment variable when manifests are applied.
REALTIME_PREFIX = '${input.safety_fence}\n\n'
REALTIME_DRIVERS = ('doubao-realtime', 'doubao-realtime-duplex', 'dashscope-realtime')
# ASTTranslate has no system prompt entry, so GizClaw provides no fence.
UNFENCED_DRIVERS = ('ast-translate',)


def dig(value, *keys):
    # None once a key is missing; the receiver itself must be a mapping.
    for key in keys:
        value = value.get(key)
        if value is None:
            return None
    return value


def truthy(value):
    # Only a missing value or false is unset; 0 and '' are set.
    return value is not None and value is not False


def text(value):
    return '' if value is None else str(value)


def player_file(file):
    name = os.path.basename(file)
    return not name.startswith('test') and not name.endswith('.giztest.yaml') and name.endswith('.yaml')


def files(root='workflows'):
    return sorted(file for file in glob.glob(f'{root}/*/*.yaml') if player_file(file))


def prompt_prefix(template, format, key):
    key = re.escape(key)
    if format == 'f_string':
        return re.match(rf'\A\{{{key}\}}\n\n', template, re.ASCII) is not None
    if format == 'go_template':
        return (re.match(rf'\A\{{\{{\s*\.{key}\s*\}}\}}\n\n', template, re.ASCII) is not None or
                re.match(rf'\A\{{\{{\s*if\s+\.{key}\s*\}}\}}\{{\{{\s*\.{key}\s*\}}\}}\n\n\{{\{{\s*end\s*\}}\}}', template, re.ASCII) is not None)
    if format == 'jinja2':
        return (re.match(rf'\A\{{\{{\s*{key}\s*\}}\}}\n\n', template, re.ASCII) is not None or
                re.match(rf'\A\{{%\s*if\s+{key}\s*%\}}\{{\{{\s*{key}\s*\}}\}}\n\n\{{%\s*endif\s*%\}}', template, re.ASCII) is not None)
    return False


def fenced_prompt(node):
    system = next((message for message in node.get('messages', []) if message.get('role') == 'system'), None)
    if system is None:
        return False
    return any(binding.get('from') == 'input.safety_fence' and
               prompt_prefix(system.get('template', ''), node.get('format'), key)
               for key, binding in node.get('inputs', {}).items())


def flowcraft_nodes(graph):
    nodes = graph['nodes']
    publishers = [node for node in nodes if node.get('type') == 'script' and node.get('publish') is True]
    selected = []
    for node in nodes:
        if node.get('type') != 'llm' or truthy(node.get('config', {}).get('json_mode')):
            continue
        output = dig(node, 'config', 'output_key')
        if node.get('publish') is True or (truthy(output) and any(
                re.search(rf'''board\.getVar\(\s*["']{re.escape(output)}["']\s*\)''', text(dig(publisher, 'config', 'source')), re.ASCII)
                for publisher in publishers)):
            selected.append(node)
    return selected


def eino_nodes(graph):
    nodes = graph['nodes']
    published = [output.get('node') for output in graph.get('outputs', []) if output.get('mime_type') == 'text/plain']
    message_fields = [dig(node, 'inputs', 'messages', 'from') for node in nodes
                      if node.get('type') == 'chat_model' and node.get('id') in published]
    message_fields = [field for field in message_fields if field is not None]
    return [node for node in nodes if node.get('type') == 'prompt' and dig(node, 'outputs', 'messages') in message_fields]


def errors(document, file):
    if not player_file(file):
        return []
    spec = document['spec']
    driver = spec['driver']
    if driver in UNFENCED_DRIVERS:
        return []
    if driver in REALTIME_DRIVERS:
        if text(dig(spec, driver.replace('-', '_'), 'instructions')).startswith(REALTIME_PREFIX):
            return []
        return [f'{file}: realtime instructions must start with ${{input.safety_fence}} followed by a blank line']
    if driver not in ('eino', 'flowcraft'):
        return [f'{file}: unknown driver {text(driver)}; review safety fence coverage']
    graph = spec[driver]['graph']
    nodes = flowcraft_nodes(graph) if driver == 'flowcraft' else eino_nodes(graph)
    if not nodes:
        return [f'{file}: no player reply prompt found; review the publish path for safety fence coverage']
    found = []
    for node in nodes:
        if driver == 'flowcraft':
            fenced = text(dig(node, 'config', 'system_prompt')).startswith(FLOWCRAFT_PREFIX)
        else:
            fenced = fenced_prompt(node)
        if fenced:
            continue
        binding = '${board.safety_fence}' if driver == 'flowcraft' else 'input.safety_fence with a matching template variable'
        found.append(f"{file}: {node['id']}: player system prompt must start with {binding} followed by a blank line")
    return found


if __name__ == '__main__':
    paths = [file for file in sys.argv[1:] if player_file(file)] if len(sys.argv) > 1 else files()
    if not paths:
        sys.exit('no player workflows found')
    found = []
    for file in paths:
        with open(file, encoding='utf-8') as f:
            found += errors(yaml.safe_load(f), file)
    if found:
        sys.exit('\n'.join(found))
    print(f'validated Workspace safety fences in {len(paths)} player workflows')
