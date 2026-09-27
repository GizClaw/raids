"""Generates tests/giztest/device/<raid>.<implementation>.giztest.yaml: the H106
device entry contract for every story, adventure and Journey implementation.

The device submits "开始" (or "继续上次的内容") once when the child enters a
raid and never submits anything on its own afterwards; the child then talks
with push-to-talk. A reply that ends without a question leaves the child in
silence, so every turn here must end with a child-facing question, "继续"
after a chapter ends must carry the story on, "继续上次的内容" must resume
after a reload, and "开始" must restart from the first chapter.

  python3 scripts/test/device-flow.py          # rewrite the generated files
  python3 scripts/test/device-flow.py --check  # fail when a file is stale
"""
import functools
import glob
import json
import os
import re
import sys

import yaml

DIR = 'tests/giztest/device'
# The reply closes with a question; a short invitation may follow it, as in
# "……还是保持灵活更重要呢？请你告诉我你的选择吧。"
ENDS_WITH_QUESTION = '[？?][^？?]{0,40}$'
# A chapter heading, not a cast preview such as "精卫在第2章加入".
NEXT_CHAPTER_HEADING = ['第 2 章：', '第 2 章:', '第 2 章《', '第2章：', '第2章:', '第2章《']
JOURNEY_OPENING = ['石猴', '仙石', '石卵', '石头里', '石头中']
# Route-only facts of the Journey soak Tester; they must never reach a child.
JOURNEY_TEST_FACTS = ['明月', '清禾', '青铜铃']


class Dumper(yaml.SafeDumper):
    """Keeps the layout of the files Ruby's YAML.dump (Psych) first wrote.

    A list shared inside one document is emitted once and aliased (&1, *1).
    """
    ANCHOR_TEMPLATE = '%d'


def represent_str(dumper, value):
    # Psych double-quotes a string that starts with a non-word character and
    # holds no '"'; otherwise the emitter picks plain or single quotes.
    style = '"' if re.search(r'^\W[^"]*$', value, re.M) else None
    return dumper.represent_scalar('tag:yaml.org,2002:str', value, style=style)


Dumper.add_representer(str, represent_str)


def read(path):
    with open(path, encoding='utf-8', newline='') as f:
        return f.read()


def load_yaml(path):
    with open(path, encoding='utf-8') as f:
        return yaml.safe_load(f)


def dig(data, *keys):
    # Ruby Hash#dig: None once a key is missing.
    for key in keys:
        data = None if data is None else data.get(key)
    return data


def raids():
    names = (os.path.basename(os.path.dirname(f)) for f in glob.glob('workflows/*/raid.json'))
    return sorted(r for r in names if re.match(r'(?:story|adventure|figure)-', r) or r == 'journey-guide')


def implementations(raid):
    impls = json.loads(read(f'workflows/{raid}/raid.json'))['implementations'].values()
    return sorted(((os.path.basename(impl['file']).removesuffix('.yaml'), impl) for impl in impls),
                  key=lambda pair: pair[0])


@functools.cache
def testing_profile():
    return load_yaml('runtime-profiles/testing.yaml')


# The testing RuntimeProfile decides which collection and alias reach a Workflow.
def target(workflow):
    collections = dig(testing_profile(), 'spec', 'workflows', 'collections')
    ordered = sorted(collections.items(), key=lambda item: 0 if item[0] == 'raidtest-targets' else 1)
    for name, aliases in ordered:
        for key, binding in aliases.items():
            if binding.get('resource_id') == workflow:
                return name, key
    raise RuntimeError(f'{workflow}: not bound in runtime-profiles/testing.yaml')


def chapters(raid):
    line = re.search(r'四章依次是：([^\n]*)', read(f'workflows/{raid}/eino.yaml'))
    titles = re.findall(r'第[0-9]章《([^》]+)》', line[1] if line else '')
    if len(titles) != 4:
        raise RuntimeError(f'{raid}: cannot read chapter titles')
    return titles


def turn(name, client, text, expect, timeout):
    return {
        'timeout': timeout, 'id': f'{client}_device_{name}', 'client': client,
        'peer_stream': {'mode': 'text', 'input': text, 'idle_timeout': '120s', 'require_text': True, 'require_audio': True},
        'expect': {'/text_eos': {'equals': True}, '/audio_eos': {'equals': True}, '/text': expect}
    }


def question(extra):
    return {'min_length': 20, 'pattern': ENDS_WITH_QUESTION, **extra}


def document(raid, suffix, impl):
    client = suffix.replace('.', '_').replace('-', '_')
    # Multi-role replies are one to two minutes of multi-voice narration.
    timeout = '6m' if suffix.endswith('.multi-role') else '4m'
    driver = impl['driver']
    multi_role = suffix.endswith('.multi-role')
    story = re.match(r'(?:story|figure)-', raid)
    journey = raid == 'journey-guide'
    # One list shared by several turns, so the dump aliases it as before.
    markers = {'not_contains': ['【', '】']} if multi_role else {}
    parameters = {
        f'{driver}_workspace_parameters': {
            'agent_type': f'{driver.upper()}_WORKSPACE_PARAMETERS_AGENT_TYPE_{driver.upper()}',
            'conversation': {'initiative': 'CONVERSATION_PARAMETERS_INITIATIVE_PEER'},
            'input': 'WORKSPACE_INPUT_MODE_PUSH_TO_TALK'
        }
    }
    turns = []
    if story:
        first, second = chapters(raid)[:2]
        # Original stories speak the heading; multi-role narration weaves it in and may
        # preview later chapters, so only a chapter 2 heading means it skipped the opening.
        opening = question({**markers, 'not_contains': ['【', '】'] + NEXT_CHAPTER_HEADING}) if multi_role else question({'contains_all': ['第 1 章', first]})
        turns.append(turn('start', client, '开始', opening, timeout))
        # Answering the chapter question closes the chapter, so the child's next 继续
        # must open chapter 2 itself with its heading and scene.
        turns.append(turn('chapter_choice', client, '我选第一个', question(markers), timeout))
        turns.append(turn('continue', client, '继续', question({**markers, **({} if multi_role else {'contains_all': ['第 2 章', second]})}), timeout))
        # Re-entry says where the story stopped and carries on; by then the story may
        # be one or two chapters in, so what matters is that it is past chapter 1 and
        # does not replay the opening.
        resume = question({'not_contains': (['【', '】'] if multi_role else []) + ['第 1 章', '你可以直接说出你的选择']})
        restart = question({**markers, 'not_contains': ['【', '】'] + NEXT_CHAPTER_HEADING}) if multi_role else question({'contains_all': ['第 1 章', first]})
    elif journey:
        turns.append(turn('start', client, '开始', question({'contains_any': JOURNEY_OPENING, 'not_contains': JOURNEY_TEST_FACTS + ['紧箍', '取经路上']}), timeout))
        turns.append(turn('chapter_choice', client, '我选第一个', question({'not_contains': JOURNEY_TEST_FACTS}), timeout))
        turns.append(turn('continue', client, '继续', question({'not_contains': JOURNEY_TEST_FACTS}), timeout))
        resume = question({'not_contains': JOURNEY_TEST_FACTS})
        restart = question({'contains_any': JOURNEY_OPENING, 'not_contains': JOURNEY_TEST_FACTS})
    else:
        turns.append(turn('start', client, '开始', question(markers), timeout))
        turns.append(turn('chapter_choice', client, '我选第一个', question(markers), timeout))
        turns.append(turn('continue', client, '继续', question(markers), timeout))
        resume = question(markers)
        restart = question(markers)
    collection, workflow = target(dig(load_yaml(f'workflows/{raid}/{suffix}.yaml'), 'metadata', 'id'))
    steps = [
        {'id': f'{client}_device_register', 'client': client, 'rpc': {'method': 'server.register', 'request': {'token': '${registration_token}'}}},
        {'id': f'{client}_device_create_workspace', 'client': client, 'rpc': {'method': 'server.workspace.create', 'request': {
            'name': '${workspace}', 'collection': collection, 'workflow_name': workflow, 'parameters': parameters}}},
        {'id': f'{client}_device_select_workspace', 'client': client, 'rpc': {'method': 'server.run.workspace.set', 'request': {'workspace_name': '${workspace}'}}},
        {'id': f'{client}_device_warmup_workspace', 'client': client, 'timeout': '2m', 'rpc': {'method': 'server.run.workspace.reload', 'request': {}}},
        *turns,
        # Leaving and re-entering: the run stops and the Workspace reloads.
        {'id': f'{client}_device_leave', 'client': client, 'rpc': {'method': 'server.run.stop', 'request': {}}},
        {'id': f'{client}_device_reenter', 'client': client, 'timeout': '2m', 'rpc': {'method': 'server.run.workspace.reload', 'request': {}}},
        turn('resume', client, '继续上次的内容', resume, timeout),
        turn('restart', client, '开始', restart, timeout)
    ]
    return {
        'version': 'gizclaw.test/v1alpha1',
        'name': f'{raid}.device.{suffix}',
        'clients': {client: {'identity': 'ephemeral', 'connection': 'webrtc', 'access_point': '${endpoint}'}},
        'variables': {
            'endpoint': {'direction': 'input', 'type': 'string', 'env': 'GIZCLAW_TEST_ENDPOINT'},
            'registration_token': {'direction': 'input', 'type': 'string', 'env': 'GIZCLAW_TEST_REGISTRATION_TOKEN', 'secret': True},
            'workspace': {'direction': 'input', 'type': 'string', 'generate': 'token'},
            'last_history_type': {'direction': 'output', 'type': 'string'},
            'last_history_text': {'direction': 'output', 'type': 'string'}
        },
        'repeat': 1,
        'timeout': '50m' if multi_role else '35m',
        'steps': steps,
        'finally': [
            # Print the last reply so a failed assertion shows what the child heard.
            {'id': f'{client}_device_read_last_history', 'client': client, 'timeout': '5s', 'rpc': {'method': 'server.run.workspace.history',
                'request': {'limit': 1, 'order': 'PEER_RUN_HISTORY_LIST_REQUEST_ORDER_DESC'}},
                'capture': {'last_history_text': '/items/0/text', 'last_history_type': '/items/0/type'}},
            {'id': f'{client}_device_last_history_type_emit', 'output': {'variable': 'last_history_type'}},
            {'id': f'{client}_device_last_history_text_emit', 'output': {'variable': 'last_history_text'}},
            {'id': f'{client}_device_stop_run', 'client': client, 'rpc': {'method': 'server.run.stop', 'request': {}}},
            {'id': f'{client}_device_delete_workspace', 'client': client, 'rpc': {'method': 'server.workspace.delete', 'request': {'name': '${workspace}'}}},
            {'id': f'{client}_device_delete_peer', 'client': client, 'rpc': {'method': 'server.peer.delete', 'request': {}}}
        ],
        'report': {'redact': ['registration_token']}
    }


HEADER = '''\
# User Story:
# As a child entering a story or adventure on the H106 device,
# I want every reply to end with a question, "继续" to carry the story on, and "继续上次的内容" / "开始" to resume or restart,
# So that the story never stops in silence after a chapter ends.
# Generated by scripts/test/device-flow.py; edit the generator, not this file.
'''


def files():
    return {
        f'{DIR}/{raid}.{suffix}.giztest.yaml':
            HEADER + yaml.dump(document(raid, suffix, impl), Dumper=Dumper, allow_unicode=True, sort_keys=False)
        for raid in raids() for suffix, impl in implementations(raid)
    }


# Every target Workflow carries the closing-question and device-cue contract
# that the generated documents exercise live.
START_CUES = ['孩子只说“开始”', '孩子说“开始”', '"开始", "开始吧"']
CONTRACTS = {
    'story': [['想听下一章就说‘继续’'], START_CUES, ['继续上次']],
    'story.multi-role': [['最后一句都必须是向孩子提出的故事内问题'], START_CUES, ['继续上次']],
    'adventure': [['孩子只能在你说完后按键回答'], START_CUES, ['继续上次的内容']],
    'journey-guide': [['最后一句都必须是问孩子的问题'], START_CUES, ['继续上次的内容']]
}


def contract_errors():
    errors = []
    for raid in raids():
        for suffix, _ in implementations(raid):
            kind = raid if raid == 'journey-guide' else raid.split('-')[0]
            if kind == 'figure':
                kind = 'story'
            if kind == 'story' and suffix.endswith('.multi-role'):
                kind += '.multi-role'
            source = read(f'workflows/{raid}/{suffix}.yaml')
            missing = [markers[0] for markers in CONTRACTS[kind] if not any(marker in source for marker in markers)]
            if missing:
                errors.append(f'workflows/{raid}/{suffix}.yaml lacks {", ".join(missing)}')
    return errors


def run(check):
    expected = files()
    present = sorted(glob.glob(f'{DIR}/*.giztest.yaml'))
    orphans = [path for path in present if path not in expected]
    stale = [path for path, body in expected.items() if not (os.path.exists(path) and read(path) == body)] + orphans
    if check:
        if stale:
            sys.exit(f'stale device-flow Giztests (run python3 scripts/test/device-flow.py): {", ".join(stale)}')
        errors = contract_errors()
        if errors:
            sys.exit('device entry contract missing:\n' + '\n'.join(errors))
        print(f'validated {len(expected)} device-flow Giztests')
    else:
        for path in orphans:
            os.remove(path)
        for path, body in expected.items():
            if not (os.path.exists(path) and read(path) == body):
                with open(path, 'w', encoding='utf-8', newline='') as f:
                    f.write(body)
        print(f'wrote {len(expected)} device-flow Giztests')


if __name__ == '__main__':
    run('--check' in sys.argv[1:])
