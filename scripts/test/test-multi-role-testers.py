#!/usr/bin/env python3
"""Exercise natural-child relay routing and deterministic contracts offline.

Python adapts codepoints only. test-unit-resources additionally compiles and
initializes all actual YAML scripts with GizClaw's real Starlark runtime.
"""
import copy
import json
from pathlib import Path
import subprocess


def documents(paths):
    return json.loads(subprocess.check_output(
        ['ruby', '-ryaml', '-rjson', '-e',
         'puts JSON.generate(ARGV.map { |p| YAML.load_file(p) })', *map(str, paths)], text=True))


def script(doc):
    return next(n['source'] for n in doc['spec']['eino']['graph']['nodes'] if n['id'] == 'route-turn')


def invoke(ns, messages, text):
    return ns['run']({'messages': messages, 'text': text})


def response(ns, i):
    check = ns['CHECKS'][i]
    if not check.get('story_choice'):
        return '不要爬窗台，请找家长帮助。' if ns['CHECKPOINTS'][i] == 'safety' else check['required'][0] + '，记住啦。'
    return ns['PROGRESSION'][0] + '\n' + ('景' * 210) + str(i) + '。原地等还是找伙伴？'


paths = sorted(p for p in Path('workflows').glob('*/test.multi-role.yaml') if p.parent.name != 'murder-mystery')
assert len(paths) == 30
for path, doc in zip(paths, documents(paths)):
    ns = {}
    exec(script(doc).replace('.codepoints()', ''), ns)
    assert ns['N'] == len(ns['REQUESTS']) == len(ns['CHECKS']) == len(ns['INTENTS'])
    assert any(not r for r in ns['REQUESTS']), path
    assert not any(any(word in r for word in ['只确认', '只说', '未解决线索', '不要推进', '知识边界']) for r in ns['REQUESTS'])
    assert not ns['recall_only_rounds']([])
    for i, c in enumerate(ns['CHECKS']):
        short = ns['CHECKPOINTS'][i] in ['remember', 'recall', 'rename', 'recall-new', 'safety']
        assert c['min_runes'] == (4 if short else 200)
        assert c['max_runes'] == (360 if short else 900)
        good = response(ns, i)
        assert not ns['deterministic_failures'](i, good), (path, i)
        for marker in ['【旁白】', '【陌生角色】', '】']:
            assert 'speaker_marker:leaked' in ns['deterministic_failures'](i, marker + good)
        for phrase in ns['CHECKS'][0]['forbidden']:
            assert any(f.startswith('forbidden:') for f in ns['deterministic_failures'](i, good + phrase))
        if short:
            assert any(f.startswith('max_runes:') for f in ns['deterministic_failures'](i, '景' * 361))
            if c.get('required'):
                assert any(f.startswith('required:') for f in ns['deterministic_failures'](i, '忘记名字了。'))
        else:
            assert not ns['recall_only_rounds']([(i, '', good)])
            for size, fails in [(199, True), (200, False), (900, False), (901, True)]:
                f = ns['deterministic_failures'](i, '景' * size)
                assert any(x.startswith(('min_runes:', 'max_runes:')) for x in f) == fails
            for size, fails in [(99, True), (100, False), (450, False), (451, True)]:
                f = ns['deterministic_failures'](i, ' '.join(['adventure'] * size))
                assert any(x.startswith(('min_words:', 'max_words:')) for x in f) == fails
            for ending in ['故事讲完了。', '天亮了吗？', '要不要继续听？']:
                assert any(f.startswith('story_choice:') for f in ns['deterministic_failures'](i, '景' * 210 + ending))
    # Full relay including checkpoints/CONTINUE and the candidate reload handoff.
    messages = [{'role': 'user', 'content': 'BEGIN fixture'}]
    result = invoke(ns, messages, 'BEGIN fixture')
    for i in range(ns['N']):
        assert result['route'] in ['scripted', 'player'], (path, i, result)
        if result['route'] == 'player':
            assert ns['INTENTS'][i] in result['user']
            if i and messages[-1]['content'] != 'CONTINUE ' + str(i):
                assert '故事：' in result['user']
        request = result['message'] if result['route'] == 'scripted' else '我选刚才那个办法呀。'
        messages += [{'role': 'assistant', 'content': request}, {'role': 'user', 'content': response(ns, i)}]
        result = invoke(ns, messages, messages[-1]['content'])
        assert not result['det'], (path, i, result)
        if i in ns['MILESTONES'] and i + 1 < ns['N']:
            assert result['route'] == 'checkpoint'
            messages += [{'role': 'assistant', 'content': 'CHECKPOINT PASS'}, {'role': 'user', 'content': 'CONTINUE ' + str(i + 1)}]
            result = invoke(ns, messages, messages[-1]['content'])
    assert result['route'] == 'final'
    assert ns['progression_failures']([(0, '', '开场。'), (1, '', '没有到达新地方。')], 0)
    assert 'loop:repeated narration' in ns['progression_failures']([(0, '', response(ns, 0)), (1, '', response(ns, 0))], 0)
    # A defective candidate is rejected immediately, before generating another child turn.
    result = invoke(ns, [{'role':'user','content':'BEGIN fixture'}, {'role':'assistant','content':ns['REQUESTS'][0]}], '短答。')
    assert result['route'] == 'final' and result['det']
    final_ns = {}
    exec(next(n['source'] for n in doc['spec']['eino']['graph']['nodes'] if n['id'] == 'finalize'), final_ns)
    for model in ['FAIL', '', 'PASS']:
        assert final_ns['run']({'route':'final','message':'deterministic-recall','det':'','model_text':model})['answer'] == 'PASS'
        assert final_ns['run']({'route':'final','message':'deterministic-recall','det':'missing fact','model_text':model})['answer'].endswith('FAIL')
    assert final_ns['run']({'route':'player','message':'','det':'','model_text':'小鸟为什么那样做呀？'})['answer'] == '小鸟为什么那样做呀？'
    if ns['CHECKPOINTS'][-1] == 'recall':
        result = invoke(ns, [{'role':'assistant','content':ns['REQUESTS'][-1]}], response(ns, ns['N'] - 1))
        assert result['message'] == 'deterministic-recall' and not result['det'], result
    for i, kind in enumerate(ns['CHECKPOINTS']):
        if kind in ['remember', 'recall', 'rename', 'recall-new']:
            result = invoke(ns, [{'role':'assistant','content':ns['REQUESTS'][i]}], response(ns, i))
            assert result['message'] == 'deterministic-recall' and not result['det'], (path, i, result)
    if path.parent.name == 'story-wizard-oz':
        messages = [{'role':'user','content':'BEGIN fixture english-restart'}]
        result = invoke(ns, messages, messages[-1]['content'])
        replies = [ns['PROGRESSION'][3] + ' ' + 'adventure ' * 105 + 'wait or search?',
                   'adventure ' * 110 + 'wait or search?', 'Our journey is SUNRISE-42.', 'We named it SUNRISE-42.']
        for i, reply in enumerate(replies):
            request = result['message'] if result['route'] == 'scripted' else 'I choose the first path!'
            messages += [{'role':'assistant','content':request}, {'role':'user','content':reply}]
            result = invoke(ns, messages, reply)
            assert not result['det'], result
        assert result['route'] == 'final'
    manifest = json.loads(path.with_name('raid.json').read_text())
    assert manifest['testers']['multi-role']['workflow_id'] == doc['metadata']['id']
print('validated 30 natural-child Testers, full relays/reloads, immediate failures, boundaries, progression, loops and recall precedence')

workflow_paths = sorted(p for p in Path('workflows').glob('*/*.multi-role.yaml')
                        if p.name != 'test.multi-role.yaml' and p.parent.name.startswith(('story-', 'adventure-')))
assert len(workflow_paths) == 60
for path in workflow_paths:
    text = path.read_text()
    for required in ('互动规则（普通200至900字）：', '篇幅执行规则：', '有声书连续讲述', '标记格式', '不输出其它【】标记', '音色由段落标记映射', '不要少于 200 字，不要超过 900 字', '目标约220个英文单词'):
        assert required in text, (path, required)
    assert '回合规则表' not in text and '总结/检查点｜' not in text
print('validated 60 simplified continuous narration contracts')

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
