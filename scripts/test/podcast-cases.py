"""Execute the podcast's unchanged controller through the existing Starlark harness."""
import json

import yaml


with open('workflows/podcast/eino.yaml', encoding='utf-8') as source:
    workflow = yaml.safe_load(source)['spec']['eino']
controller = next(node for node in workflow['graph']['nodes'] if node['id'] == 'prepare')
prompt = next(node for node in workflow['graph']['nodes'] if node['id'] == 'prompt')
assert prompt['messages'][-1] == {'role': 'user', 'template': '{request}'}, 'the real current request must follow historical assistant messages'
cases = []
for text in ['停一下', '先停一下', '暂停', '停止播客', '别说了', '请停一下。', '停一下好吗？', '请暂停吧', '等一下', '停一下，我有个问题', 'stop', 'PAUSE']:
    cases.append({'id': f'stop-{text}', 'input': {'text': text},
                  'expect': {'continue': {'equals': False}}})
for text in ['开始', '继续', '不要停', '讲讲火车为什么会停止', '说说暂停键的发明', '不停地讲太空', '按原样解释“停止”这个词']:
    cases.append({'id': f'continue-{text}', 'input': {'text': text},
                  'expect': {'continue': {'equals': True}}})
cases.append({'id': 'bounded-long-history',
              'input': {'text': '继续', 'messages': [{'role': 'assistant', 'content': '前文' * 2000 + '末尾'}] * 20},
              'expect': {'recent': {'equals': [{'role': 'assistant', 'content': '前文' * 599 + '末尾'}] * 8}}})
cases.append({'id': 'current-request-is-not-duplicated',
              'input': {'text': '继续', 'messages': [
                  {'role': 'user', 'content': '开始'},
                  {'role': 'assistant', 'content': '前一轮'},
                  {'role': 'user', 'content': '继续'},
                  {'role': 'assistant', 'content': '本轮第一段'}]},
              'expect': {'recent': {'equals': [
                  {'role': 'user', 'content': '开始'},
                  {'role': 'assistant', 'content': '前一轮'},
                  {'role': 'assistant', 'content': '本轮第一段'}]}}})
print(json.dumps({'source': controller['source'], 'cases': cases}, ensure_ascii=False))
