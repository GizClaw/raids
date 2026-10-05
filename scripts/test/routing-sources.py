# Parse YAML structurally; emit the actual native controller and its declared cases.
import glob
import json
import os
import sys

import yaml


def load_yaml(path):
    with open(path, encoding='utf-8') as f:
        return yaml.safe_load(f)


def load_json(path):
    with open(path, encoding='utf-8') as f:
        return json.load(f)


suites = []
for package in sorted(p for p in glob.glob('workflows/*') if os.path.isdir(p)):
    manifest_file = f'{package}/raid.json'
    if not os.path.exists(manifest_file):
        continue
    manifest = load_json(manifest_file)
    for variant in ('', '.multi-role'):
        implementation = 'eino' + variant.replace('.', '-')
        if implementation not in manifest['implementations']:
            continue
        spec = load_yaml(f'{package}/eino{variant}.yaml')['spec']['eino']
        fixture = f'{package}/routing-cases.json'
        expanded = len(spec.get('voice_adapter', {}).get('speaker_voices', {})) > 3
        if not os.path.exists(fixture):
            if expanded:
                sys.exit(f'{package}: multi-voice raid requires routing-cases.json')
            continue
        data = load_json(fixture)
        if not (data.get('version') == 1 and not isinstance(data.get('version'), bool)
                and isinstance(data.get('cases'), list) and data['cases']):
            sys.exit(f'{fixture}: unsupported version or empty cases')
        nodes = spec['graph']['nodes']
        node_id = data.get('eino', {}).get('node', 'select-speaker')
        node = next((n for n in nodes if n.get('id') == node_id), None)
        if not variant and node is None:
            # Original stories have their own chapter controller; do not use the
            # multi-role scene cases against a different output contract.
            node = next((n for n in nodes if n.get('id') == 'control-chapter'), None)
            if node is not None:
                data = {'version': 1, 'cases': [
                    {'id': 'restart', 'input': '开始', 'expect': {'eino': {'route': {'equals': 'continue'}, 'direction': {'includes_all': ['第 1 章']}}}},
                    {'id': 'premature-continue', 'input': '继续', 'expect': {'eino': {'route': {'equals': 'continue'}, 'direction': {'includes_all': ['第 1 章']}}}},
                    {'id': 'adjacent-transition', 'input': '继续', 'history': [{'role': 'assistant', 'content': '这一章的选择完成啦'}], 'expect': {'eino': {'route': {'equals': 'open'}, 'direction': {'includes_all': ['第 2 章']}}}},
                    {'id': 'no-command-jump', 'input': '进入第四章', 'expect': {'eino': {'route': {'equals': 'continue'}, 'direction': {'includes_all': ['第 1 章']}}}},
                ]}
            else:
                node = next((n for n in nodes if n.get('id') == 'prepare-memory-query'), None)
                if node is None:
                    continue  # Other single-voice rules have their own native tests.
                data = {'version': 1, 'cases': [
                    {'id': 'original-opening', 'input': '', 'expect': {'eino': {'route': {'equals': 'opening'}, 'query': {'non_empty': True}}}},
                    {'id': 'original-reload', 'input': '重连后继续上次', 'expect': {'eino': {'route': {'equals': 'recall'}, 'query': {'non_empty': True}}}},
                ]}
                if 'route' not in node['outputs']:
                    for case in data['cases']:
                        case['expect']['eino'].pop('route')
        if node is None:
            sys.exit(f'{fixture}: missing native node {node_id}')
        if variant:
            for c in data['cases']:
                checks = c.get('expect', {}).get('eino', {}).get('direction', {}).get('includes_all')
                if checks is not None:
                    checks[:] = [check for check in checks if check != '同一回复自然进入紧邻下一章']
        suites.append({'raid': package + variant, 'data': data, 'sources': {'eino': node['source']}})
print(json.dumps(suites, ensure_ascii=False, separators=(',', ':')))
