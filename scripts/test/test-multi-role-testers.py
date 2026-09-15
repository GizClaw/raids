#!/usr/bin/env python3
"""Exercise natural-child relay routing and deterministic contracts offline.

Python covers the schedule exhaustively; the real go.starlark.net harness
executes transcript regressions and verdicts without translating the YAML source.
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

# Execute unmodified YAML in go.starlark.net, including retained Tester history.
# The candidate alone is reloaded in e2e13; its last naming answer is the next
# relay's handoff, completing the Tester's outstanding naming turn exactly once.
import os
import tempfile
real_cases = []
def real_case(name, source, messages, expected):
    real_cases.append({'ID': name, 'Source': source,
                       'Input': {'messages': copy.deepcopy(messages), 'text': messages[-1]['content']},
                       'Expect': expected})
history_doc = documents([Path('workflows/adventure-history/test.multi-role.yaml')])[0]
history_source = script(history_doc)
for fixture in json.loads(Path('scripts/test/fixtures/multi-role-e2e13.json').read_text()):
    messages = fixture['messages']
    assert messages[-3]['content'] == fixture['handoff']
    for history in (messages, messages[-3:]):
        real_case(fixture['id'] + ('-retained' if history == messages else '-fresh'),
                  history_source, history,
                  {'route': 'final', 'message': 'deterministic-recall', 'det': ''})
    broken = copy.deepcopy(messages)
    broken[-1]['content'] = '我们的旅程叫错误名字。'
    real_case(fixture['id'] + '-wrong', history_source, broken,
              {'route': 'final', 'det': 'recall required:星火七号'})

for path, doc in zip(paths, documents(paths)):
    ns = {}
    exec(script(doc).replace('.codepoints()', ''), ns)
    i = next(i for i, k in enumerate(ns['CHECKPOINTS']) if k == 'recall')
    # CONTINUE is deliberately present: the recall bypass must work with a
    # command as well as with a natural candidate handoff.
    messages = [{'role': 'user', 'content': 'CONTINUE ' + str(i)},
                {'role': 'assistant', 'content': ns['REQUESTS'][i]},
                {'role': 'user', 'content': response(ns, i)}]
    # Interior recalls continue playing; terminal recalls yield a verdict.
    if i == ns['N'] - 1:
        real_case(path.parent.name + '-continue', script(doc), messages,
                  {'route': 'final', 'message': 'deterministic-recall', 'det': ''})
    real_case(path.parent.name + '-isolated', script(doc), messages[1:],
              {'route': 'final', 'message': 'deterministic-recall', 'det': ''})
    finalize = next(n['source'] for n in doc['spec']['eino']['graph']['nodes'] if n['id'] == 'finalize')
    for det, answer in [('', 'PASS'), ('recall required:missing', '确定性失败：recall required:missing\nFAIL')]:
        real_cases.append({'ID': path.parent.name + '-verdict-' + det,
                           'Source': finalize,
                           'Input': {'route': 'final', 'message': 'deterministic-recall', 'det': det, 'model_text': 'FAIL'},
                           'Expect': {'answer': answer}})

aesop_doc = documents([Path('workflows/story-aesop/test.multi-role.yaml')])[0]
aesop_source = script(aesop_doc)
ns = {}
exec(aesop_source.replace('.codepoints()', ''), ns)
for fixture in json.loads(Path('scripts/test/fixtures/multi-role-aesop-e2e13.json').read_text()):
    candidate = next(k for k in fixture['turns'] if not k.endswith('_tester'))
    replies = fixture['turns'][candidate]['texts']
    # Exact character-response text and delivered chapter headings.
    assert not ns['deterministic_failures'](3, replies[3])
    assert not ns['progression_failures']([(i, '', r) for i, r in enumerate(replies)], 0)
    real_cases.append({'ID': candidate + '-delivered-arrivals',
                       'Entry': 'check_arrivals',
                       'Source': aesop_source + '\ndef check_arrivals(input):\n    return {"failures": progression_failures(input["rounds"], 0)}\n',
                       'Input': {'rounds': [[i, '', r] for i, r in enumerate(replies)]},
                       'Expect': {'failures': []}})
    # Use the real character turn alone at its actual scheduled index.
    real_case(candidate + '-character', aesop_source,
              [{'role': 'user', 'content': 'CONTINUE 3'},
               {'role': 'assistant', 'content': fixture['turns'][candidate + '_tester']['texts'][3]},
               {'role': 'user', 'content': replies[3]}], {'route': 'player', 'det': ''})

# A checkpoint may still be in chapter one; final evaluation sees both segments.
messages = [{'role': 'user', 'content': 'BEGIN fixture'}]
for i in range(8):
    good = response(ns, i).replace(ns['PROGRESSION'][0], '第一章的草地')
    messages += [{'role': 'assistant', 'content': ns['REQUESTS'][i] or '我选那个办法呀。'},
                 {'role': 'user', 'content': good}]
real_case('aesop-checkpoint-no-arrival-yet', aesop_source, messages, {'route': 'checkpoint', 'det': ''})
messages += [{'role': 'assistant', 'content': 'CHECKPOINT PASS'}, {'role': 'user', 'content': 'CONTINUE 8'}]
for i in range(8, ns['N']):
    good = response(ns, i).replace(ns['PROGRESSION'][0], '第一章的草地')
    messages += [{'role': 'assistant', 'content': ns['REQUESTS'][i] or '我选那个办法呀。'},
                 {'role': 'user', 'content': good}]
real_case('aesop-final-no-arrival', aesop_source, messages,
          {'route': 'final', 'det': 'progression:no new chapter or scene'})
messages[-1]['content'] = ns['PROGRESSION'][0] + messages[-1]['content']
real_case('aesop-final-arrival', aesop_source, copy.deepcopy(messages), {'route': 'final', 'det': ''})
# The quality arrival turn selects a real destination in child language.
for engine in ['eino', 'flowcraft']:
    doc = documents([Path('workflows/adventure-history/' + engine + '.multi-role.yaml')])[0]
    utterance = '我们走到哪里啦？我想去集市看看，听听那里的伙伴怎么说！'
    if engine == 'eino':
        control = next(n['source'] for n in doc['spec']['eino']['graph']['nodes'] if n['id'] == 'control-narration')
        real_cases.append({'ID': 'history-natural-destination', 'Source': control,
                           'Input': {'text': utterance, 'history': [], 'memory': ''},
                           'Expect': {'scene': '2'}})
    else:
        control = next(n['config']['source'] for n in doc['spec']['flowcraft']['graph']['nodes']
                       if 'const scenes =' in n.get('config', {}).get('source', ''))
        subprocess.run(['node', '-e', """
const vm = require('vm'), assert = require('assert/strict');
const c = JSON.parse(require('fs').readFileSync(0, 'utf8'));
const vars = {input: c.text};
vm.runInNewContext(c.source, {board: {getVar: k => vars[k], setVar: (k, v) => {vars[k] = v;}}});
assert.equal(vars.scenario_state.voice_scene, 2);
"""], input=json.dumps({'source': control, 'text': utterance}), text=True, check=True)

with tempfile.NamedTemporaryFile(mode='w', suffix='.json') as payload:
    json.dump(real_cases, payload)
    payload.flush()
    env = dict(os.environ, RAIDS_MULTI_ROLE_CASES=payload.name, GOPROXY='off', GOSUMDB='off', GOTOOLCHAIN='local')
    env.setdefault('GOMODCACHE', '/Volumes/H002-R02T-APFS/Caches/go/pkg/mod')
    subprocess.run(['go', '-C', 'scripts/test/starlark', 'test', '-run', '^TestMultiRoleTranscript$', '-count=1'], env=env, check=True)
print('validated real Starlark e2e13 transcripts, 30 recall finalizers, checkpoints and full-relay progression')
