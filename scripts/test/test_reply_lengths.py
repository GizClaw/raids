"""Exercise shipped Tester gates with native Starlark, without a live Model."""
import json
from pathlib import Path
import subprocess

import yaml


for raid in ('chat-assistant', 'journey-guide'):
    doc = yaml.safe_load(Path(f'workflows/{raid}/test.yaml').read_text())
    source = next(n['source'] for n in doc['spec']['eino']['graph']['nodes'] if n['id'] == 'route-turn')
    # Adapt only the entrypoint: execute the actual shipped deterministic gate.
    source = source.replace('def run(input):', 'def relay_run(input):') + '''
def run(input):
    return {"failures": ";".join(deterministic_failures(input["index"], input["text"]))}
'''
    cases = []

    def case(name, index, text, expected):
        cases.append({'id': name, 'input': {'index': index, 'text': text},
                      'expect': {'failures': expected}})

    if raid == 'journey-guide':
        case('ordinary-long-narration', 13, '你和明月来到水帘后，发现可以侧身进入的洞缝。' * 60,
             {'equals': ''})
        case('long-reply-still-rejects-stale-guide', 6, '明月熟悉黑风岭。清禾。' * 60,
             {'includes_all': ['forbidden:清禾']})
        short = '你藏好青铜铃，观察守卫和商队位置。'
        case('brief-content', 11, short, {'equals': ''})
        case('brevity-hint-is-not-a-counter', 11, short + '暂不营救。', {'equals': ''})
        case('short-complete-fact', 6, '明月熟悉黑风岭。', {'equals': ''})
    else:
        case('ordinary-long-correction', 5, '你当前去苏州，坐G7105。' * 60, {'equals': ''})
        case('long-reply-still-rejects-stale-trip', 5, '苏州、G7105。仍去杭州。' * 60,
             {'includes_all': ['forbidden:仍去杭州']})
        for index, limit in ((3, 10), (8, 8), (9, 35), (10, 20)):
            facts = {3: '', 8: '', 9: '下周四苏州周宁G7105三点青桥', 10: '苏州周宁G7105'}[index]
            case(f'brief-content-{index}', index, facts or '加油', {'equals': ''})
            case(f'brevity-hint-is-not-a-counter-{index}', index, facts + '好' * (limit + 1), {'equals': ''})
        for index, exact in ((4, '收到'), (11, '行程已更新')):
            case(f'exact-answer-{index}', index, exact, {'equals': ''})
            case(f'exact-answer-extra-text-{index}', index, exact + '。',
                 {'includes_all': ['exact_text:']})
            for suffix, padded in (('spaces', ' ' + exact + ' '), ('newline', exact + '\n')):
                case(f'exact-answer-{suffix}-{index}', index, padded,
                     {'includes_all': ['exact_text:']})

    case('empty-reply-still-fails', 0, '  ', {'includes_all': ['reply:empty']})

    subprocess.run(['scripts/test/test-starlark-routing.sh'],
                   input=json.dumps({'Source': source, 'Steps': 2_000_000, 'Cases': cases}, ensure_ascii=False),
                   text=True, check=True)
print('validated reply content without character counting, exact answers and retained fact checks')
