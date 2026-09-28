# Offline workflow -> manifest -> RuntimeProfile -> Voice closure for both variants.
import glob
import json
import os
import sys

import yaml

import giztest_layout
from testing_voices import check_testing_voices

# Audio-only drivers name their one Voice in driver settings, not a voice_adapter.
DRIVER_VOICES = {'ast-translate': ('voice', 'tts_voice'), 'doubao-realtime': ('audio', 'output', 'voice')}


def load_yaml(path):
    with open(path, encoding='utf-8') as f:
        return yaml.safe_load(f)


def read(path):
    with open(path, encoding='utf-8') as f:
        return f.read()


def dig(value, *keys):
    # None once a key is missing; the receiver itself must be a mapping.
    for key in keys:
        value = value.get(key)
        if value is None:
            return None
    return value


def num_eq(value, expected):
    # JSON/YAML true is not 1 and false is not 0.
    return not isinstance(value, bool) and value == expected


def check(ok, message):
    if not ok:
        sys.exit(message)


profiles = {n: load_yaml(f'runtime-profiles/{n}.yaml')['spec'] for n in ('default', 'testing')}
check_testing_voices(profiles['testing'])
voices = {dig(load_yaml(f), 'metadata', 'id'): f for f in glob.glob('voices/**/*.yaml', recursive=True)}
count = 0
for file in sorted(glob.glob('workflows/*/raid.json')):
    manifest = json.loads(read(file))
    raid = manifest['id']
    speaker_maps = {}
    for name, impl in manifest['implementations'].items():
        workflow = f"workflows/{raid}/{impl['file']}"
        doc = load_yaml(workflow)
        engine = impl['driver']
        spec = dig(doc, 'spec', engine.replace('-', '_'))
        adapter = spec.get('voice_adapter', {})
        bindings = {**adapter.get('speaker_voices', {}), **adapter.get('node_voices', {})}
        driver_voice = dig(spec, *DRIVER_VOICES[engine]) if engine in DRIVER_VOICES else None
        aliases = list(dict.fromkeys(a for a in [*bindings.values(), adapter.get('default_voice'), driver_voice] if a is not None))
        for node_id in adapter.get('node_voices', {}).keys():
            node = next((n for n in spec['graph']['nodes'] if n.get('id') == node_id), None)
            check(node is not None and (engine != 'flowcraft' or node.get('publish') is True), f'{workflow}: Voice bound to missing/unpublished node {node_id}')
        slots = dig(impl, 'parameters', 'voices') or {}
        check(sorted(aliases) == sorted(slots.keys()), f'{workflow}: Voice aliases differ from manifest slots')
        for profile_name, profile in profiles.items():
            # Each published node / named speaker must have its own audible identity,
            # including original implementations, not just the multi-role variants.
            for map_name in ('speaker_voices', 'node_voices'):
                ids = [dig(profile, 'resources', 'voices', a, 'resource_id') for a in adapter.get(map_name, {}).values()]
                check(len(set(ids)) == len(ids), f'{workflow}: duplicate {profile_name} {map_name} Voice resources')
            collections = profile['workflows']['collections']
            check(any(any(entry.get('resource_id') == dig(doc, 'metadata', 'id') for entry in c.values()) for c in collections.values()), f'{workflow}: missing {profile_name} collection entry')
            for a in aliases:
                voice_id = dig(profile, 'resources', 'voices', a, 'resource_id')
                check(voice_id is not None and voice_id in voices, f'{workflow}: unresolved {profile_name} Voice {a}')
                check('mars' not in voice_id, f'{workflow}: retired mars Voice {voice_id}')
            for a in (dig(impl, 'parameters', 'models') or {}).keys():
                model_id = dig(profile, 'resources', 'models', a, 'resource_id')
                check(model_id is not None and model_id is not False, f'{workflow}: unresolved model {a}')
        if not name.endswith('-multi-role'):
            continue
        check(dig(doc, 'metadata', 'id').endswith('-multi-role'), f'{workflow}: missing variant ID')
        original_id = impl['workflow_id'].removesuffix('-multi-role')
        for p in profiles.values():
            ids = [dig(p, 'resources', 'voices', a, 'resource_id') for a in aliases]
            check(len(set(ids)) == len(ids), f'{workflow}: duplicate multi-role Voice resources')
            # A variant keeps its original's Voices; figure raids have no original to match.
            if any(i['workflow_id'] == original_id for i in manifest['implementations'].values()):
                for a in aliases:
                    check(dig(p, 'resources', 'voices', a) == dig(p, 'resources', 'voices', a.replace(original_id + '-mr', original_id, 1)), f'{workflow}: changed Voice binding {a}')
        if raid.startswith(('story-', 'adventure-', 'figure-')):
            speaker_maps[engine] = adapter['speaker_voices']
            check(adapter['speaker_voices']['旁白'] == adapter['default_voice'], f'{workflow}: narrator mismatch')
            nodes = spec['graph']['nodes']
            outputs = [n for n in nodes if (n.get('publish') is True if engine == 'flowcraft' else n.get('type') == 'chat_model')]
            check(len(outputs) == 1, f'{workflow}: expected one narration LLM')
            source = read(workflow)
            check('约1至2分钟' in source and '不输出其它【】标记' in source, f'{workflow}: missing narration contract')
            for speaker in adapter['speaker_voices'].keys():
                check(f'【{speaker}】' in source, f'{workflow}: missing marker {speaker}')
            giztest = f"tests/giztest/smoke/{raid}.{os.path.basename(impl['file']).removesuffix('.yaml')}.giztest.yaml"
            probe = next((s for s in giztest_layout.probes(giztest, name.replace('-', '_')) if s.get('id') == 'continuous_story'), None)
            check(probe is not None and num_eq(dig(probe, 'expect', '/text', 'min_length'), 1) and 'non_empty' not in dig(probe, 'expect', '/text'), f'{workflow}: missing non-empty gate')
            check(all(m in dig(probe, 'expect', '/text', 'not_contains') for m in ('【', '】')) and num_eq(dig(probe, 'expect', '/audio_integrity/streams', 'equals'), 1) and num_eq(dig(probe, 'expect', '/audio_pacing/underruns', 'equals'), 0), f'{workflow}: missing playback/marker gates')
        count += 1
    if len(speaker_maps) == 2:
        check(list(speaker_maps['flowcraft'].keys()) == list(speaker_maps['eino'].keys()), f'{raid}: engine speaker names differ')
        for p in profiles.values():
            for speaker, alias_name in speaker_maps['flowcraft'].items():
                check(dig(p, 'resources', 'voices', alias_name, 'resource_id') == dig(p, 'resources', 'voices', speaker_maps['eino'][speaker], 'resource_id'), f'{raid}: engine Voice mismatch for {speaker}')
print(f'validated all workflow Voice bindings and {count} multi-role implementations')
