# Parse YAML structurally; emit sources and per-raid fixtures for the offline runner.
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


def dig(value, *keys):
    # None once a key is missing; the receiver itself must be a mapping.
    for key in keys:
        value = value.get(key)
        if value is None:
            return None
    return value


suites = []
for package in sorted(p for p in glob.glob('workflows/*') if os.path.isdir(p)):
    manifest_file = f'{package}/raid.json'
    manifest = load_json(manifest_file) if os.path.exists(manifest_file) else {}
    for variant in ('', '.multi-role'):
        if variant != '' and not os.path.exists(f'{package}/flowcraft{variant}.yaml'):
            continue
        flow_file, eino_file = (f'{package}/{e}{variant}.yaml' for e in ('flowcraft', 'eino'))
        flow = dig(load_yaml(flow_file), 'spec', 'flowcraft') if os.path.exists(flow_file) else None
        eino = dig(load_yaml(eino_file), 'spec', 'eino') if os.path.exists(eino_file) else None
        expanded = any(len(dig(i, 'parameters', 'voices') or {}) > 3 for i in (manifest.get('implementations') or {}).values())
        expanded = expanded or len((None if flow is None else dig(flow, 'voice_adapter', 'speaker_voices')) or {}) > 3
        expanded = expanded or len((None if eino is None else dig(eino, 'voice_adapter', 'speaker_voices')) or {}) > 3
        fixture = f'{package}/routing-cases.json'
        if expanded and not os.path.exists(fixture):
            sys.exit(f'{package}: multi-voice raid requires routing-cases.json')
        if not os.path.exists(fixture):
            continue
        data = load_json(fixture)
        # JSON true is not version 1.
        if not (data.get('version') == 1 and not isinstance(data.get('version'), bool)
                and isinstance(data.get('cases'), list) and data['cases']):
            sys.exit(f'{fixture}: unsupported version or empty cases')
        if variant:
            # Multi-role narration is guidance; shared original fixtures still check
            # routing/state, but no longer prescribe when narration changes chapter.
            for c in data['cases']:
                expect = dig(c, 'expect', 'flowcraft')
                if expect is not None:
                    expect.pop('next_chapter_instruction', None)
                checks = dig(c, 'expect', 'eino', 'direction', 'includes_all')
                if checks is not None:
                    checks[:] = [check for check in checks if check != '同一回复自然进入紧邻下一章']
        if not variant:
            nodes = flow['graph']['nodes']
            if any(n.get('id') == 'control-story' for n in nodes):
                data = {'version': 1, 'flowcraft': {'node': 'control-story'}, 'cases': [
                    {'id': 'original-opening', 'input': '请从第一章开始', 'expect': {'speaker': 'narrator', 'flowcraft': {'story_state.chapter': {'equals': 1}}}},
                    {'id': 'original-chapter-gate', 'input': '进入第二章', 'expect': {'speaker': 'narrator', 'flowcraft': {'transition_blocked': {'equals': True}, 'story_state.chapter': {'equals': 1}}}},
                    {'id': 'original-choice', 'input': '我选择帮助朋友', 'expect': {'flowcraft': {'story_state.chapter_choice_made': {'equals': True}}}},
                    {'id': 'original-ready-transition', 'input': '进入下一章', 'state': {'chapter': 1, 'chapter_choice_made': True, 'chapter_progress_beats': ['outcome', 'perspective']}, 'expect': {'speaker': 'narrator', 'flowcraft': {'story_state.chapter': {'equals': 2}}}},
                ]}
            elif any(n.get('id') == 'route-phase' for n in nodes):
                data = {'version': 1, 'flowcraft': {'node': 'route-phase', 'state_var': 'scenario_state'}, 'cases': [
                    {'id': 'original-opening', 'input': '', 'expect': {'flowcraft': {'scenario_phase': {'equals': 'opening'}}}},
                    {'id': 'original-correction', 'input': '更正，只确认新事实', 'expect': {'flowcraft': {'scenario_phase': {'equals': 'correction'}}}},
                ]}
            elif not any(n.get('id') == data['flowcraft']['node'] for n in nodes):
                # These originals have no character selector; their published node Voice
                # routes are covered by voice-bindings.py, and live contracts by tier tests.
                continue
        sources = {}
        for engine, spec in (('flowcraft', flow), ('eino', eino)):
            if not (engine in manifest['implementations'] and engine in data):
                continue
            node_id = data[engine].get('node', 'control-story' if engine == 'flowcraft' else 'select-speaker')
            nodes = None if spec is None else dig(spec, 'graph', 'nodes')
            node = None if nodes is None else next((n for n in nodes if n.get('id') == node_id), None)
            if node is None and not variant and engine == 'eino':
                continue  # Original single-voice Eino has no role-routing script.
            if node is None:
                sys.exit(f'{fixture}: missing {engine} node {node_id}')
            sources[engine] = node['config']['source'] if engine == 'flowcraft' else node['source']
        suites.append({'raid': package + variant, 'data': data, 'sources': sources})
print(json.dumps(suites, ensure_ascii=False, separators=(',', ':')))
