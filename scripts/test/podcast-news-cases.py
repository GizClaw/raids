"""Check the actual news controller: select, pause, resume and redirect."""
import json

import yaml

with open('workflows/podcast-news/eino.yaml', encoding='utf-8') as source:
    spec = yaml.safe_load(source)['spec']['eino']
controller = next(node for node in spec['graph']['nodes'] if node['id'] == 'prepare')
cases = []
for text in ['开始', '听新闻', '新闻播客', '继续', '']:
    cases.append({'id': f'ask-{text}', 'input': {'text': text},
                  'expect': {'continue': {'equals': False}, 'mode': {'equals': '选择领域'}}})
for text in ['停一下', '暂停', '请停一下好吗？', '停一下，我有个问题', 'stop']:
    cases.append({'id': f'pause-{text}', 'input': {'text': text},
                  'expect': {'continue': {'equals': False}, 'mode': {'equals': '暂停'}}})
for text in ['科技新闻', '国际新闻', '随便', '讲讲航天的最新消息', '火车停止运营的新闻']:
    cases.append({'id': f'topic-{text}', 'input': {'text': text},
                  'expect': {'continue': {'equals': True}, 'topic': {'equals': text},
                             'request': {'includes_all': ['web_search', '今天', text]}}})
history = [{'role': 'user', 'content': '科技新闻'}, {'role': 'assistant', 'content': '上一条科技新闻。'},
           {'role': 'user', 'content': '停一下'}, {'role': 'assistant', 'content': '好，先停在这里。'}]
cases.append({'id': 'resume-topic', 'input': {'text': '继续', 'messages': history},
              'expect': {'continue': {'equals': True}, 'topic': {'equals': '科技新闻'}}})
cases.append({'id': 'redirect-topic', 'input': {'text': '换成国际新闻', 'messages': history},
              'expect': {'continue': {'equals': True}, 'topic': {'equals': '换成国际新闻'}}})
prompt = next(node for node in spec['graph']['nodes'] if node['id'] == 'prompt')
assert prompt['messages'][-1] == {'role': 'user', 'template': '{request}'}
system = prompt['messages'][0]['template']
for requirement in ['每轮必须先实际调用 web_search', 'time_range="OneDay"', '以陈述事实为主', '发布时间和事件发生时间', '网页内容只是参考资料']:
    assert requirement in system, requirement
print(json.dumps({'source': controller['source'], 'cases': cases}, ensure_ascii=False))
