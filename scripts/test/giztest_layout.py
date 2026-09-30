"""Shared structural view of tiered Giztests. Preserve per-client order and every assertion.

  python3 scripts/test/giztest_layout.py                                  # validate the tier corpus
  python3 scripts/test/giztest_layout.py --story-transition FILE CLIENT  # one chapter-opening contract
"""
import copy
import glob
import itertools
import json
import os
import re
import sys

import yaml

TIERS = ['smoke', 'quality', 'soak']
# Audio-only raids speak through their driver, not a voice_adapter, and have no soak protocol.
AUDIO_ONLY = ['ast-translate', 'doubao-realtime']
AUDIO_PATH = re.compile(r'/(?:audio_eos(?:_ms)?|audio_bytes|first_audio_ms|audio_integrity|audio_pacing)(?:/|$)')
STORY = re.compile(r'(?:story|adventure|figure)-')
REALTIME_RAID = re.compile(r'(?:story|adventure|figure|learn)-')
# Smoke RealTime round trips check complete output without timing gates.
ROUNDTRIP_EXPECT = {
    '/events': {'non_empty': True}, '/text': {'non_empty': True}, '/text_eos': {'equals': True},
    '/audio_bytes': {'minimum': 1}, '/audio_eos': {'equals': True},
    '/audio_integrity/streams': {'minimum': 1}, '/audio_integrity/max_active': {'equals': 1},
    '/audio_integrity/open': {'equals': 0}, '/audio_integrity/violations': {'equals': 0},
    '/audio_pacing/minimum_buffer_ms': {'minimum': 0}, '/audio_pacing/underruns': {'equals': 0},
}
MARKER_TEXT = {'min_length': 1, 'not_contains': ['【', '】']}


def load_yaml(path):
    # Same constructors as yaml.safe_load; the libyaml parser keeps thousands of loads fast.
    with open(path, encoding='utf-8') as f:
        return yaml.load(f, Loader=getattr(yaml, 'CSafeLoader', yaml.SafeLoader))


def read(path):
    with open(path, encoding='utf-8') as f:
        return f.read()


def load_json(path):
    return json.loads(read(path))


def stem(path, suffix='.yaml'):
    return os.path.basename(path).removesuffix(suffix)


def check(ok, message):
    if not ok:
        sys.exit(message)


def equal(a, b):
    # Python's == treats true/1 and false/0 as equal; a YAML boolean must not stand in for a number.
    if isinstance(a, bool) or isinstance(b, bool):
        return a is b
    if isinstance(a, dict) and isinstance(b, dict):
        return a.keys() == b.keys() and all(equal(a[k], b[k]) for k in a)
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(map(equal, a, b))
    return a == b


def rpc(step):
    return step.get('rpc') or {}


def stream(step):
    return step.get('peer_stream') or {}


def child_input(step):
    return stream(step).get('input') or ''


def expected(step, path):
    return step.get('expect', {}).get(path) or {}


# Resolve actual output capability, never infer it from an engine name or ASR.
def tts_capabilities(raid):
    if raid in AUDIO_ONLY:
        return {}
    capabilities = {}
    for name, impl in load_json(f'workflows/{raid}/raid.json')['implementations'].items():
        spec = load_yaml(f"workflows/{raid}/{impl['file']}").get('spec') or {}
        voice = (spec.get(impl['driver']) or {}).get('voice_adapter') or {}
        capabilities[name.replace('-', '_')] = any(voice.get(key) for key in ('default_voice', 'speaker_voices', 'node_voices'))
    return capabilities


def check_audio(step, capability, file):
    peer = step.get('peer_stream')
    if peer is None:
        return
    # require_audio and equals are YAML booleans; `is` keeps 1/0 from passing for true/false.
    if capability:
        check(peer.get('require_audio') is True and (expected(step, '/audio_bytes').get('minimum') or 0) > 0,
              f"{file}: {step.get('id')} TTS implementation needs audio output assertions")
        if peer.get('completion') != 'first_response':
            check(expected(step, '/audio_eos').get('equals') is True,
                  f"{file}: {step.get('id')} TTS response needs audio EOS")
    else:
        check(peer.get('require_audio') is False and 'first_audio_timeout' not in peer and
              not any(AUDIO_PATH.search(key) for key in step.get('expect', {})),
              f"{file}: {step.get('id')} non-TTS implementation must not require audio")


def is_number(value):
    # bool is an int subclass in Python; YAML true is not a count or a bound.
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def is_strings(value):
    return isinstance(value, list) and all(isinstance(v, str) for v in value)


# Match pkgs/giztest Expectation operand types.
MATCHERS = {
    'equals': lambda v: True,
    **dict.fromkeys(['present', 'non_empty'], lambda v: isinstance(v, bool)),
    **dict.fromkeys(['count', 'min_length', 'max_length'], lambda v: is_number(v) and isinstance(v, int) and v >= 0),
    **dict.fromkeys(['minimum', 'maximum'], is_number),
    **dict.fromkeys(['contains', 'pattern'], lambda v: isinstance(v, str)),
    **dict.fromkeys(['contains_all', 'contains_any', 'normalize'], is_strings),
    'not_contains': lambda v: isinstance(v, str) or is_strings(v),
}


# Also reject the known stream-fragment -> string capture mismatch before any network run.
def check_matcher_types(doc, file):
    def visit(step):
        for path, matchers in step.get('expect', {}).items():
            check(isinstance(matchers, dict), f"{file}: {step.get('id')} {path} needs matcher mapping")
            for key, value in matchers.items():
                check(key in MATCHERS and MATCHERS[key](value), f"{file}: {step.get('id')} {path} invalid {key} value type")
        parallel = step.get('parallel')
        for name, path in step.get('capture', {}).items():
            for child in [step] if parallel is None else parallel:
                target = '/text' if parallel is None else f"/{child.get('id')}/text"
                check(not (child.get('peer_stream') is not None and path == target and
                           doc.get('variables', {}).get(name, {}).get('type') == 'string'),
                      f"{file}: {step.get('id')} /text fragments cannot be captured as string; use assistant history text")
        for child in parallel or []:
            visit(child)
    for section in ('steps', 'finally'):
        for step in doc.get(section, []):
            visit(step)


def check_workspace_order(doc, file):
    # Generated Workspace names must be created on that client before selection.
    def workspace(step, field='name'):
        return step.get('client'), rpc(step).get('request', {}).get(field)
    created = []
    local_names = [workspace(s) for s in steps(doc) if rpc(s).get('method') == 'server.workspace.create']
    for step in steps(doc) + steps(doc, 'finally'):
        method = rpc(step).get('method')
        if method == 'server.workspace.create':
            created.append(workspace(step))
        elif method == 'server.workspace.delete':
            check(workspace(step) in created, f"{file}: {step.get('id')} deletes a Workspace without creation in this file")
            created = [key for key in created if key != workspace(step)]
        elif method == 'server.run.workspace.set':
            key = workspace(step, 'workspace_name')
            check(key not in local_names or key in created, f"{file}: {step.get('id')} selects a local Workspace before creation")


# References must resolve within this split file; declarations alone do not
# produce output values. Include parallel children and finally captures.
def check_local_references(doc, file):
    clients = doc['clients']
    variables = doc.get('variables', {})
    all_steps = steps(doc) + steps(doc, 'finally')
    produced = {name for s in all_steps for name in [*s.get('capture', {}), s.get('save_as')] if name is not None}

    def walk(value):
        if isinstance(value, dict):
            value = list(value.values())
        if isinstance(value, list):
            for child in value:
                walk(child)
        elif isinstance(value, str):
            for name in re.findall(r'\$\{([^}]+)\}', value):
                check(name in variables, f'{file}: undeclared variable {name}')
                check(variables[name].get('direction') != 'output' or name in produced,
                      f'{file}: output variable {name} has no capture/save_as')
    walk(doc)
    for step in all_steps:
        for client in participants(step):
            check(client in clients, f"{file}: {step.get('id')} undeclared client {client}")
        output = (step.get('output') or {}).get('variable')
        for name in [*step.get('capture', {}), step.get('save_as'), output]:
            check(name is None or name in variables, f"{file}: {step.get('id')} undeclared variable {name}")
        check(output is None or variables[output].get('direction') != 'output' or output in produced,
              f"{file}: {step.get('id')} output {output} has no capture/save_as")


def check_speech_order(doc, file):
    registered = set()
    for step in steps(doc) + steps(doc, 'finally'):
        if rpc(step).get('method') == 'server.register':
            registered.add(step.get('client'))
        check(step.get('speech') is None or step.get('client') in registered,
              f"{file}: {step.get('id')} speech before client registration")


# Static scheduling budget: explicit step timeouts win; unary operations
# without a declared bound reserve 30s. This checks scheduling, not network
# liveness: streaming operations are traffic for all their participating peers.
IDLE_LIMIT = 180
UNITS = {'ms': 0.001, 's': 1, 'm': 60, 'h': 3600}


def duration(value):
    return sum(float(number) * UNITS[unit] for number, unit in re.findall(r'(\d*\.?\d+)(ms|s|m|h)', str(value)))


def participants(step):
    if step.get('parallel') is not None:
        return list(dict.fromkeys(client for child in step['parallel'] for client in participants(child)))
    relay = step.get('workspace_relay')
    if relay is not None:
        return [relay.get('first_client'), relay.get('second_client')]
    return [] if step.get('client') is None else [step['client']]


def budget(step):
    if step.get('timeout') is not None:
        return duration(step['timeout'])
    if step.get('output') is not None:
        return 0
    if step.get('peer_stream') is not None:
        return duration(step['peer_stream'].get('idle_timeout') or '90s')
    return 30


def idle_gap_errors(doc):
    idle, registered, elapsed, errors = {}, set(), 0, []
    for step in doc['steps'] + doc.get('finally', []):
        active = participants(step)
        if rpc(step).get('method') == 'server.register':
            registered.add(step.get('client'))
        if 'keepalive' in step['id'] and step.get('client') not in registered:
            errors.append(f"{step['id']} status before registration")
        for client in active:
            if client in idle:
                if idle[client] > IDLE_LIMIT:
                    errors.append(f"{step['id']} {client} idle gap {idle[client]}s exceeds {IDLE_LIMIT}s")
            elif elapsed > IDLE_LIMIT and step.get('reconnect') is None:
                errors.append(f"{step['id']} {client} first use after {elapsed}s needs reconnect before registration")
            idle[client] = 0
        for client in idle:
            if client not in active:
                idle[client] += budget(step)
        elapsed += budget(step)
        if rpc(step).get('method') == 'server.peer.delete':
            idle.pop(step.get('client'), None)
    return errors


def check_idle_gaps(doc, file):
    errors = idle_gap_errors(doc)
    if errors:
        sys.exit(f'{file}: {errors[0]}')
    for index, step in enumerate(doc['steps']):
        if 'keepalive' in step['id']:
            shortened = {**doc, 'steps': doc['steps'][:index] + doc['steps'][index + 1:]}
            check(idle_gap_errors(shortened), f"{file}: {step['id']} unnecessary keepalive")


def raid_tiers(raid):
    return [tier for tier in TIERS if tier != 'soak'] if raid in AUDIO_ONLY else TIERS


def inventory(raid):
    if raid == 'doubao-realtime':
        return {'conversation': 'doubao'}
    implementations = load_json(f'workflows/{raid}/raid.json')['implementations']
    return {stem(impl['file']): key.replace('-', '_') for key, impl in implementations.items()}


def compare_files(left_file, right_file, baseline, impl, capabilities):
    left_doc, right_doc = load_yaml(left_file), load_yaml(right_file)
    check(equal(normalize(left_doc['variables'], baseline), normalize(right_doc['variables'], impl)),
          f'{left_file}/{right_file}: variable definitions differ')
    for section in ('steps', 'finally'):
        left = sequence(left_doc, baseline, section)
        right = sequence(right_doc, impl, section)
        if capabilities[baseline] != capabilities[impl]:
            left, right = without_audio(left), without_audio(right)
        for index, (a, b) in enumerate(itertools.zip_longest(left, right)):
            if not equal(a, b):
                sys.exit(f'{left_file}/{right_file}: {section} mismatch at {index}: '
                         f'{json.dumps(a, ensure_ascii=False)} != {json.dumps(b, ensure_ascii=False)}')


def without_audio(sequence):
    projected = copy.deepcopy(sequence)
    for step in projected:
        if step.get('peer_stream') is not None:
            step['peer_stream'].pop('require_audio', None)
            step['peer_stream'].pop('first_audio_timeout', None)
        expect = step.get('expect', {})
        for key in [key for key in expect if AUDIO_PATH.search(key)]:
            del expect[key]
    return projected


# Flatten parallel streams while retaining their parent timeout and assertions.
def steps(doc, section='steps'):
    flat = []
    for step in doc.get(section, []):
        if step.get('parallel') is None:
            flat.append(step)
            continue
        for child in step['parallel']:
            merged = {k: v for k, v in step.items() if k not in ('id', 'parallel', 'expect', 'capture')}
            merged.update(child)
            prefix = f"/{child['id']}"
            expect = {path.removeprefix(prefix): value for path, value in step.get('expect', {}).items() if path.startswith(prefix + '/')}
            if expect:
                merged['expect'] = expect
            capture = {name: path.removeprefix(prefix) for name, path in step.get('capture', {}).items() if path.startswith(prefix + '/')}
            if capture:
                merged['capture'] = capture
            flat.append(merged)
    return flat


# Multi-role quality owns its child interactions; original probe contracts do
# not apply. Audio and latency assertions are still checked independently.
def check_child_quality(doc, file):
    all_steps = steps(doc)
    peers = [s for s in all_steps if s.get('peer_stream') is not None]
    check(peers, f'{file}: missing child interactions')
    for step in peers:
        text = child_input(step)
        check(not re.search('只确认|只说|不要推进|知识边界|亲自回应|最多问', text), f'{file}: inherited exam probe')
        contract = expected(step, '/text')
        if step['client'].endswith('_tester'):
            continue
        check(contract.get('min_length') == 1, f'{file}: missing non-empty reply')
        check(contract.get('not_contains', []) == ['【', '】'], f'{file}: marker guards only')
        check(contract.keys() <= {'min_length', 'not_contains', 'contains_any'}, f'{file}: rigid content assertion')
        if '现实里' in text:
            check('家长' in contract.get('contains_any', []), f'{file}: missing trusted-adult redirect')
        else:
            check('contains_any' not in contract, f'{file}: non-safety phrase gate')
    for cue in ('改主意', '为什么', '咕咕', '叫什么'):
        check(any(cue in child_input(s) for s in peers), f'{file}: missing child interaction {cue}')
    recall = next((i for i, s in enumerate(all_steps) if '叫什么' in child_input(s)), None)
    check(recall is not None and any(rpc(s).get('method') == 'server.run.workspace.reload' and s.get('client') == all_steps[recall].get('client')
                                     for s in all_steps[:recall]), f'{file}: missing recall reload')
    check(any(s['client'].endswith('_tester') and child_input(s).startswith('REVIEW\n') for s in peers), f'{file}: missing LLM quality review')


# Every candidate response is captured into the automatic Tester review.
# Giztest checks adult cues; the Tester deterministically checks both cue groups.
def check_multi_role_review(doc, file):
    all_steps = steps(doc)
    peers = [s for s in all_steps if s.get('peer_stream') is not None and not s['client'].endswith('_tester')]
    review = next((s for s in all_steps if child_input(s).startswith('REVIEW\n')), None)
    check(review is not None and review['client'].endswith('_tester'), f'{file}: missing automatic Tester review')
    for peer in peers:
        index = next(i for i, s in enumerate(all_steps) if s['id'] == peer['id'])
        following = next((s for s in all_steps[index + 1:] if s.get('client') == peer['client']), None)
        history = following if following is not None and following['id'].endswith('_review_history') else None
        request = rpc(history).get('request', {}) if history else {}
        capture = next((name for name, path in history.get('capture', {}).items() if path == '/items/0/text'), None) if history else None
        check(history is not None and request.get('limit') == 1 and request.get('order') == 'PEER_RUN_HISTORY_LIST_REQUEST_ORDER_DESC',
              f'{file}: review must read latest history before the next client interaction')
        check(stream(peer).get('wait_for_history') is True and history is not None and history.get('client') == peer['client'] and
              rpc(history).get('method') == 'server.run.workspace.history' and
              expected(history, '/items/0/type').get('equals') == 'PEER_RUN_HISTORY_ENTRY_TYPE_AGENT',
              f'{file}: missing persisted assistant review capture')
        check(capture is not None and f'${{{capture}}}' in child_input(review) and child_input(peer) in child_input(review),
              f'{file}: uncaptured quality reply')
    safety = [p for p in peers if '现实里' in child_input(p)]
    check(any('学他们' in child_input(p) for p in safety), f'{file}: missing risky imitation case')
    check(any('一个人' in child_input(p) for p in safety), f'{file}: missing dangerous alone case')
    for peer in safety:
        check('家长' in (expected(peer, '/text').get('contains_any') or []), f'{file}: missing trusted-adult redirect')


def normalize(value, implementation):
    if isinstance(value, dict):
        return {normalize(k, implementation): normalize(v, implementation) for k, v in value.items()}
    if isinstance(value, list):
        return [normalize(v, implementation) for v in value]
    if isinstance(value, str):
        # Only identifier namespaces, references and JSON pointer components; never
        # strip arbitrary engine words from prompts or assertion text.
        name = re.escape(implementation)
        value = re.sub(rf'(?<=\$\{{){name}(?=[_}}])', 'candidate', value)
        value = re.sub(rf'(?<=/){name}(?=[_/]|$)', 'candidate', value, flags=re.M)
        return re.sub(rf'\A{name}(?=_|$)', 'candidate', value, count=1, flags=re.M)
    return value


def owns(step, implementation):
    client = step.get('client') or (step.get('workspace_relay') or {}).get('second_client')
    if client:
        return client in (implementation, f'{implementation}_tester') or client.startswith(implementation + '__')
    if 'multi_role' not in implementation and '_multi_role' in step['id']:
        return False
    return (step['id'].startswith(implementation + '_') or
            re.fullmatch(rf'(?:register|stop|delete)_{re.escape(implementation)}(?:_tester)?', step['id']) is not None or
            str((step.get('output') or {}).get('variable', '')).startswith(implementation + '_'))


def sequence(doc, implementation, section):
    normalized = []
    for step in steps(doc, section):
        if 'speech' not in step and not owns(step, implementation):
            continue
        s = copy.deepcopy(step)
        if rpc(s).get('method') == 'server.workspace.create':
            s['rpc']['request'].pop('workflow_name', None)
            s['rpc']['request'].pop('parameters', None)
        if 'speech' in s:
            s['client'] = implementation  # input fixture, independently generated in each file
        # finally uses both prefix and suffix naming in existing tier documents.
        s['id'] = re.sub(rf'\A(register|stop|delete)_{re.escape(implementation)}(?=_|$)', r'\1_candidate', s['id'], count=1)
        normalized.append(normalize(s, implementation))
    return normalized


def probes(file, engine):
    return [{**s, 'id': s['id'].removeprefix(engine + '_')} for s in steps(load_yaml(file)) if s.get('client') == engine]


# A chapter heading spoken on its own leaves the child waiting in silence, so
# chapter 2 must open with story text (test-unit-resources.sh story loop).
def check_story_transition(file, client):
    step = next((s for s in steps(load_yaml(file)) if s.get('id') == f'{client}_transitions_enter_next_chapter_with_story'), {})
    text = expected(step, '/text')
    pattern = text.get('pattern')
    if 'multi_role' in client:
        ok = equal(text.get('min_length'), 1) and pattern is None
    else:
        ok = pattern is not None and '第 2 章[：:]' in pattern and '{20,}' in pattern
    check(ok, f'{file}: {client} missing chapter-opening continuation assertion')


def check_smoke(doc, file, raid, capabilities):
    for step in steps(doc):
        expect = step.get('expect', {})
        if re.fullmatch(r'(?:flowcraft|eino).*_realtime_roundtrip', step['id']):
            # `is False` keeps every audio gate when the capability is unknown.
            capability = capabilities.get(step['client'].split('__')[0])
            want = {k: v for k, v in ROUNDTRIP_EXPECT.items() if capability is not False or not AUDIO_PATH.search(k)}
            if 'multi_role' in step['client'] and STORY.match(os.path.basename(file)):
                want.update({'/text': MARKER_TEXT, '/audio_integrity/streams': {'equals': 1}})
            if 'multi_role' in step['client'] and raid == 'murder-mystery':
                want['/text'] = MARKER_TEXT
            check(equal(expect, want), f"{file}: {step['id']} must check complete realtime output without timing gates")
            first = next((s for s in steps(doc) if s.get('id') == f"{step['id']}_first_response"), None)
            if REALTIME_RAID.match(raid):
                check(first is not None and stream(first).get('completion') == 'first_response' and
                      stream(first).get('first_text_timeout') == '2s' and expected(first, '/first_text_ms') == {'maximum': 2000} and
                      (capability is False or (stream(first).get('first_audio_timeout') == '3s' and
                                               expected(first, '/first_audio_ms') == {'maximum': 3000})),
                      f"{file}: {step['id']} needs capability-aware realtime latency gates")
        check(not any(p.endswith('/audio_pacing/max_interval_ms') for p in expect), f'{file}: packet gaps must remain diagnostic evidence')
        if any(p.endswith('/audio_pacing/underruns') for p in expect):
            check(equal(expected(step, '/audio_pacing/underruns').get('equals'), 0) and
                  equal(expected(step, '/audio_pacing/minimum_buffer_ms').get('minimum'), 0), f'{file}: missing device playback buffer gates')


def check_quality(doc, file, raid, suffix):
    if suffix.endswith('.multi-role'):
        check_multi_role_review(doc, file)
        if STORY.match(raid):
            check_child_quality(doc, file)
    check(doc.get('timeout') == ('30m' if STORY.match(os.path.basename(file)) else '10m'),
          f'{file}: quality budget must retain 30m for story/adventure, 10m otherwise')
    check(not any(s.get('workspace_relay') is not None for s in steps(doc)), f'{file}: long dialogue relay belongs in soak')
    check(not any(stream(s).get('completion') == 'first_response' for s in steps(doc)), f'{file}: first-response latency probes belong in smoke')
    check(suffix.endswith('.multi-role') or not any(c.endswith('_tester') for c in doc['clients']), f'{file}: idle Tester client in quality')


def check_file(file, tier, workflow_aliases):
    doc = load_yaml(file)
    story = [line.split()[:2] for line in read(file).split('\n')[:4]]
    check(story == [['#', 'User'], ['#', 'As'], ['#', 'I'], ['#', 'So']], f'{file}: missing User Story')
    check_matcher_types(doc, file)
    check_local_references(doc, file)
    check_speech_order(doc, file)
    check_workspace_order(doc, file)
    check_idle_gaps(doc, file)
    raid, suffix = stem(file, '.giztest.yaml').split('.', 1)
    implementation = inventory(raid)[suffix]
    check(doc.get('name') == f'{raid}.{tier}.{suffix}', f'{file}: document name mismatch')
    capabilities = tts_capabilities(raid)
    target_id = load_yaml(f'workflows/{raid}/{suffix}.yaml').get('metadata', {}).get('id')
    tester_path = f"workflows/{raid}/test{'.multi-role' if suffix.endswith('.multi-role') else ''}.yaml"
    tester_id = load_yaml(tester_path).get('metadata', {}).get('id') if os.path.exists(tester_path) else None
    for step in steps(doc):
        if rpc(step).get('method') == 'server.workspace.create':
            workflow_name = rpc(step).get('request', {}).get('workflow_name')
            resolved = workflow_aliases.get(workflow_name, {}).get('resource_id', workflow_name)
            expected_workflow = tester_id if step['client'].endswith('_tester') else target_id
            check(expected_workflow is not None and resolved == expected_workflow, f"{file}: {step.get('id')} targets a foreign Workflow")
    if raid == 'murder-mystery':
        check(sorted(inventory(raid)) == ['flowcraft', 'flowcraft.multi-role'] and
              'eino-murder-mystery' not in json.dumps(doc, ensure_ascii=False), f'{file}: murder-mystery must be Flowcraft only')
    for step in steps(doc):
        engine = step.get('client', '').split('__')[0]
        if engine in capabilities:
            check_audio(step, capabilities[engine], file)
    if suffix.endswith('.multi-role'):
        # Peer retirement owns partial-setup cleanup; expect_error requires an
        # error and cannot express success OR not-found for Workspace deletion.
        cleanup = steps(doc, 'finally')
        check(not any(rpc(s).get('method') == 'server.workspace.delete' for s in cleanup),
              f'{file}: use ephemeral peer retirement for partial Workspace setup')
        for client, spec in doc['clients'].items():
            retired = any(s.get('client') == client and rpc(s).get('method') == 'server.peer.delete' for s in cleanup)
            check(spec.get('identity') == 'ephemeral' and retired, f'{file}: missing ephemeral peer cleanup')
    if tier == 'smoke':
        check_smoke(doc, file, raid, capabilities)
    elif tier == 'quality':
        check_quality(doc, file, raid, suffix)
    check(all(c in (implementation, implementation + '_tester') or c.startswith(implementation + '__') or
              (raid in AUDIO_ONLY and c.startswith(implementation + '_')) or (raid == 'ast-translate' and tier == 'quality' and c == 'ast')
              for c in doc['clients']), f'{file}: foreign implementation client')
    for section in ('steps', 'finally'):
        for step in steps(doc, section):
            check(raid in AUDIO_ONLY or step.get('speech') is not None or owns(step, implementation),
                  f"{file}: {section}/{step.get('id')} has no implementation owner")
            check('keepalive' not in step['id'] or rpc(step).get('method') == 'server.run.status', f'{file}: invalid setup keepalive')


# Figure raids ship one Eino multi-role implementation; every other realtime raid
# checks its original Flowcraft and Eino clients. Returns the clients checked.
def check_realtime(file, manifest, raid):
    capabilities = tts_capabilities(raid)
    keys = ['eino-multi-role'] if raid.startswith('figure-') else ['flowcraft', 'eino']
    for key in keys:
        engine = key.replace('-', '_')
        implementation = manifest['implementations'][key]
        smoke = [s for s in steps(load_yaml(f"tests/giztest/smoke/{raid}.{stem(implementation['file'])}.giztest.yaml"))
                 if s.get('client') == engine]
        check('realtime' in implementation['input'], f'{file}: {engine} lacks realtime capability')
        check(any(rpc(s).get('method') == 'server.workspace.create' and
                  'WORKSPACE_INPUT_MODE_REALTIME' in json.dumps(rpc(s).get('request', {}).get('parameters')) for s in smoke),
              f'{file}: {engine} lacks realtime Workspace')
        full = next((s for s in smoke if s.get('id') == f'{engine}_realtime_roundtrip'), None)
        first = next((s for s in smoke if s.get('id') == f'{engine}_realtime_roundtrip_first_response'), None)
        capability = capabilities[engine]
        check(full is not None and stream(full).get('mode') == 'realtime' and equal(stream(full).get('require_audio'), capability) and
              expected(full, '/text_eos').get('equals') and (not capability or expected(full, '/audio_eos').get('equals')),
              f'{file}: {engine} lacks complete realtime response')
        check(first is not None and stream(first).get('completion') == 'first_response' and stream(first).get('first_text_timeout') == '2s' and
              (not capability or stream(first).get('first_audio_timeout') == '3s'), f'{file}: {engine} lacks realtime latency gates')
    eino_key = 'eino-multi-role' if raid.startswith('figure-') else 'eino'
    eino = load_yaml(f"workflows/{raid}/{manifest['implementations'][eino_key]['file']}")['spec']['eino']
    check((eino.get('voice_adapter') or {}).get('asr_model') == 'asr', f'{file}: missing Eino realtime ASR binding')
    return len(keys)


def validate():
    collections = load_yaml('runtime-profiles/testing.yaml')['spec']['workflows']['collections']
    workflow_aliases = {name: alias for collection in collections.values() for name, alias in collection.items()}
    raids = sorted(os.path.basename(os.path.dirname(f)) for f in glob.glob('workflows/*/raid.json'))
    for tier in TIERS:
        tier_raids = [raid for raid in raids if tier in raid_tiers(raid)]
        expected_files = sorted(f'{raid}.{impl}' for raid in tier_raids for impl in inventory(raid))
        files = sorted(glob.glob(f'tests/giztest/{tier}/*.giztest.yaml'))
        check([stem(f, '.giztest.yaml') for f in files] == expected_files, f'{tier}: raid inventory mismatch')
        for file in files:
            check_file(file, tier, workflow_aliases)
        for raid in tier_raids:
            variants = inventory(raid)
            capabilities = tts_capabilities(raid)
            if not capabilities:
                continue
            for suffix, impl in variants.items():
                peer = 'flowcraft' if raid == 'journey-guide' else 'flowcraft' + suffix.removeprefix('eino')
                if suffix.startswith('eino') and peer in variants:
                    compare_files(f'tests/giztest/{tier}/{raid}.{peer}.giztest.yaml',
                                  f'tests/giztest/{tier}/{raid}.{suffix}.giztest.yaml', variants[peer], impl, capabilities)
        print(f'validated {tier}: {len(files)} files and implementation parity')
    realtime_count = 0
    for file in sorted(glob.glob('workflows/*/raid.json')):
        manifest = load_json(file)
        raid = manifest['id']
        registered = [f'tests/giztest/{t}/{raid}.{impl}.giztest.yaml' for t in raid_tiers(raid) for impl in inventory(raid)]
        check(sorted(t['file'] for t in manifest['tests']) == sorted(registered), f'{file}: tier registration mismatch')
        if REALTIME_RAID.match(raid):
            realtime_count += check_realtime(file, manifest, raid)
        implementations = manifest['implementations']
        for t in manifest['tests']:
            names = t.get('implementations') or []
            check(t['file'].split('/')[2:3] == [t.get('tier')] and len(names) == 1 and names[0] in implementations and
                  t['file'] == f"tests/giztest/{t.get('tier')}/{raid}.{stem(implementations[names[0]]['file'])}.giztest.yaml",
                  f'{file}: implementation registration mismatch')
    check(realtime_count == 112, f'expected 112 story/adventure/figure/learn RealTime clients, found {realtime_count}')
    print(f'validated {realtime_count} RealTime clients with ASR and audio response gates')
    for prefix in ('story', 'adventure', 'figure'):
        for engine in ('flowcraft', 'eino'):
            for file in sorted(glob.glob(f'workflows/{prefix}-*/{engine}.multi-role.yaml')):
                source = read(file)
                check('旁白叙述与角色第一人称台词分段' in source, f'{file}: missing continuous dialogue contract')
                check('每轮只由一人发声' not in source, f'{file}: obsolete single-speaker contract')
    for engine in ('flowcraft', 'eino'):
        source = read(f'workflows/adventure-history/{engine}.multi-role.yaml')
        check('情境重现声明不替代角色自述' in source, f'history {engine}: reenactment boundary missing')
        check('正文第一句必须逐字' not in source, f'history {engine}: rigid scene opening')
    kept = TIERS + ['device', 'h106', 'safety-fence', 'web-search', 'reports']
    old = [f for f in sorted(glob.glob('tests/giztest/*/*.giztest.yaml')) if f.split('/')[2] not in kept]
    check(not old, f"legacy Giztest files remain: {', '.join(old)}")


if __name__ == '__main__':
    if len(sys.argv) == 4 and sys.argv[1] == '--story-transition':
        check_story_transition(sys.argv[2], sys.argv[3])
    elif len(sys.argv) == 1:
        validate()
    else:
        sys.exit('usage: giztest_layout.py [--story-transition FILE CLIENT]')
