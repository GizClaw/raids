#!/usr/bin/env python3
"""Offline contract regression; Ruby parses YAML, Python exercises portable scripts.

Only codepoints() is adapted to Python's native Unicode iteration. This is a
behavioral stand-in, not a Starlark compiler. starlark-modules.rb and the Go
module checker validate every script with the real GizClaw Starlark runtime.
"""
import json
from pathlib import Path
import subprocess


def documents(paths):
    return json.loads(subprocess.check_output(
        ['ruby', '-ryaml', '-rjson', '-e',
         'puts JSON.generate(ARGV.map { |p| YAML.load_file(p) })', *map(str, paths)],
        text=True))


def script(doc):
    node = next(n for n in doc['spec']['eino']['graph']['nodes'] if n['id'] == 'route-turn')
    return node['source']


paths = sorted(Path('workflows').glob('*/test.multi-role.yaml'))
assert len(paths) == 31
for path, doc, original, soak in zip(paths, documents(paths),
        documents([p.with_name('test.yaml') for p in paths]),
        [{'steps': [step for doc in documents(sorted(Path('tests/giztest/soak').glob(p.parent.name + '.*.giztest.yaml'))) for step in doc['steps']]} for p in paths]):
    raid = path.parent.name
    ns = {}
    exec(script(doc).replace('.codepoints()', ''), ns)
    old = {}
    exec(script(original).replace('.codepoints()', ''), old)
    if raid == 'murder-mystery':
        assert ns['REQUESTS'] == old['REQUESTS']
        assert ns['CHECKPOINTS'] == old['CHECKPOINTS']
        for current, previous in zip(ns['CHECKS'], old['CHECKS']):
            for field in ('required', 'required_any', 'forbidden'):
                assert current[field] == previous[field], (raid, field)
    else:
        assert not any('进入下一章' in r or '请进入第' in r for r in ns['REQUESTS'])
        ordinary_index = next(i for i, c in enumerate(ns['CHECKS']) if c.get('story_choice'))
        for phrase in ('进入下一章', '要不要继续', '想继续听就说', '这一章的选择完成啦'):
            assert any(f.startswith('forbidden:') for f in ns['deterministic_failures'](ordinary_index, phrase))
        assert any(f.startswith('story_choice:') for f in ns['deterministic_failures'](ordinary_index, '故事停在这里。'))
    for request, current, previous in zip(ns['REQUESTS'], ns['CHECKS'], old['CHECKS']):
        if '只确认' in request:
            assert current['min_runes'] == previous['min_runes'], (raid, request)
            assert current['max_runes'] <= previous['max_runes'], (raid, request)
    ordinary = [i for i, c in enumerate(ns['CHECKS']) if c['min_runes'] == 200]
    assert ordinary
    for index in ordinary:
        assert ns['CHECKS'][index]['max_runes'] == 900
    index = ordinary[0]
    # Isolate counting from the scenario's mandatory content, without mutating files.
    ns['CHECKS'][index] = {'min_runes': 200, 'max_runes': 900, **({'min_words': 100, 'max_words': 450} if raid != 'murder-mystery' else {})}
    for size, failure in [(199, 'min_runes:'), (200, None), (500, None), (900, None), (901, 'max_runes:')]:
        text = '景' * size
        for candidate in (text, '【旁白】' + text if raid != 'murder-mystery' else '【主持人】' + text):
            failures = ns['deterministic_failures'](index, candidate)
            assert (not failures if failure is None else any(f.startswith(failure) for f in failures)), (raid, size, failures)
    if raid != 'murder-mystery':
        for ordinary_index in ordinary:
            assert ns['CHECKS'][ordinary_index]['min_words'] == 100
            assert ns['CHECKS'][ordinary_index]['max_words'] == 450
        assert ns['english_word_count']("Don't re-start; “hello” — ... 42") == 3
        assert not ns['is_english']('当前旅程代号 SUNRISE-42。' + '景' * 300)
        for size, failure in [(99, 'min_words:'), (100, None), (220, None), (450, None), (451, 'max_words:')]:
            # Long words prove the Chinese rune cap no longer applies to English.
            text = ' '.join(['adventure'] * size)
            for candidate in (text, '【旁白】' + text, '【旁白】' + text.replace(' ', '\n')):
                failures = ns['deterministic_failures'](index, candidate)
                assert (not failures if failure is None else failures == [failure + str(size)]), (raid, size, failures)
        # Short English words also report word-bound failures, not rune-bound failures.
        assert ns['deterministic_failures'](index, ' '.join(['I'] * 451)) == ['max_words:451']
        if raid == 'story-wizard-oz':
            for english_index in (0, 1, 3):
                prefix = {
                    0: 'Chapter 1: The Yellow Brick Fork. The yellow brick road splits three ways: courage, wisdom, or helping one another. Which path will you take first?',
                    1: 'Dorothy says: Dorothy continues.',
                    3: 'The journey code is SUNRISE-42.',
                }[english_index]
                for size in (99, 100, 450, 451):
                    reply = prefix.replace('?', '.') + ' adventure' * (size - ns['english_word_count'](prefix)) + '?'
                    if english_index == 0:
                        reply = 'adventure ' * (size - ns['english_word_count'](prefix)) + prefix
                    result = ns['run']({'text': reply, 'messages': [{'role': 'assistant', 'content': ns['ENGLISH_REQUESTS'][english_index]}]})
                    assert (result['det'] == '' if 100 <= size <= 450 else 'words:' in result['det']), (english_index, size, result)
    manifest = json.loads(path.with_name('raid.json').read_text())
    tester = manifest['testers']['multi-role']
    assert tester['workflow_id'] == doc['metadata']['id'] == raid + '-test-multi-role'
    assert tester['file'] == path.name
    assert tester['parameters'] == manifest['tester']['parameters']
    expected = sorted(k for k in manifest['implementations'] if k.endswith('-multi-role'))
    assert tester['implementations'] == expected or sorted(tester['implementations']) == expected
    routed = []
    for step in soak['steps']:
        request = step.get('rpc', {}).get('request', {})
        if step.get('client', '').endswith('_tester') and 'workflow_name' in request:
            multi = 'multi_role' in step['client']
            assert request['workflow_name'] == raid + ('-test-multi-role' if multi else '-test')
            if multi:
                routed.append(step['client'])
    assert len(set(routed)) == len(expected), raid
print('validated 31 multi-role Tester contracts, Chinese rune and English word boundaries, marker stripping and soak routing')

# Every actual narration prompt must retain its surrounding instructions.
workflow_paths = sorted(p for p in Path('workflows').glob('*/*.multi-role.yaml')
                        if p.name != 'test.multi-role.yaml' and p.parent.name.startswith(('story-', 'adventure-')))
assert len(workflow_paths) == 60

def strings(value):
    if isinstance(value, dict):
        for item in value.values():
            yield from strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from strings(item)
    elif isinstance(value, str):
        yield value

for path, doc in zip(workflow_paths, documents(workflow_paths)):
    assert '回复最后一句必须逐字是：这一章' not in path.read_text(), path
    assert '只有用户明确要求进入紧邻的下一章' not in path.read_text(), path
    current_prompts = [s for s in strings(doc) if '篇幅执行规则：' in s]
    assert current_prompts, path
    for current in current_prompts:
        assert '每段约100字' in current and '目标约220个英文单词' in current, path
        assert '不要少于 200 字，不要超过 900 字' in current, path
        assert '300至600' not in current and '150至300' not in current, path
        assert '英文按字符' not in current and '400至500' not in current, path
        for required in ('仅用户明确要求只确认', '有声书连续讲述', '标记格式', '不输出其它【】标记', '音色由段落标记映射'):
            assert required in current, (path, required)
print('validated 60 multi-role workflows and preserved surrounding prompt instructions')

# Exercise post-response persistence as well as pre-response routing. An automatic
# arrival must survive recall before another user turn supplies a chapter command.
import re
persistence_cases = []
for path, doc in zip(workflow_paths, documents(workflow_paths)):
    story = path.parent.name.startswith('story-')
    if path.name.startswith('flowcraft'):
        nodes = doc['spec']['flowcraft']['graph']['nodes']
        control = next(n['config']['source'] for n in nodes
                       if 'const ' + ('chapters' if story else 'scenes') + ' =' in n.get('config', {}).get('source', ''))
        names = json.loads(re.search(r'const (?:chapters|scenes) = (\[.*?\]);', control)[1])
        source = next(n['config']['source'] for n in nodes
                      if 'state.last_answer =' in n.get('config', {}).get('source', '') or 'next.last_answer =' in n.get('config', {}).get('source', ''))
        answer = ('【旁白】第 2 章：' if story else '【旁白】来到') + names[1] + '\n角色行动的后果。'
        persistence_cases.append({'source': source, 'answer': answer,
                                  'story': story, 'raid': path.parent.name})
    else:
        nodes = doc['spec']['eino']['graph']['nodes']
        source = next(n['source'] for n in nodes if n['id'] in ('capture-observation', 'commit-progress'))
        ns = {}
        exec(source, ns)
        if story:
            fact = ns['run']({'text': '我选第一个办法。', 'answer': '【旁白】第 2 章：新行动\n故事后果。'})['fact']
            assert '\n【旁白】第 2 章：' in fact, path
        else:
            control = next(n['source'] for n in nodes if n['id'] == 'control-narration')
            names = json.loads(re.search(r'scenes = (\[.*?\])', control)[1])
            fact = ns['run']({'text': '我选第一个办法。', 'answer': '【旁白】来到' + names[1] + '。',
                              'scene': '1', 'voice_revision': '2', 'phase': 'explore', 'route': '', 'side': ''})
            fact = fact.get('fact', fact.get('progress'))
            assert '"voice_scene":2' in fact, path
subprocess.run(['node', '-e', r'''
const vm = require('vm'), assert = require('assert/strict');
for (const c of JSON.parse(require('fs').readFileSync(0, 'utf8'))) {
  const key = c.story ? 'story_state' : 'scenario_state';
  const vars = {[key]: {chapter: 1, voice_scene: 1, revision: 1}, answer: c.answer, tmp_answer: c.answer, input: '我选第一个办法。'};
  vm.runInNewContext(c.source, {board: {getVar: k => vars[k], setVar: (k, v) => {vars[k] = v;}}});
  const saved = JSON.parse(vars[key + '_fact']);
  assert.equal(c.story ? saved.chapter : saved.voice_scene, 2, c.raid);
  assert(saved.active_roles.length > 0, c.raid);
}
'''], input=json.dumps(persistence_cases), text=True, check=True)
print('validated 60 multi-role post-response observations and automatic arrival persistence')
