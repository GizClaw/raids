"""Check the listener's persisted dialogue phases and real incoming context."""
import json
import yaml

spec = yaml.safe_load(open('workflows/podcast-news/test-persona.yaml', encoding='utf-8'))['spec']['eino']
node = next(n for n in spec['graph']['nodes'] if n['id'] == 'listener-prepare')
cases = []
def case(name, data, mode, turn, recent=None):
    want = {'mode': {'equals': mode}, 'listener': {'equals': {'turn': turn}}}
    if recent is not None:
        want['recent'] = {'equals': recent}
    cases.append({'id': name, 'input': data, 'expect': want})

case('answer-the-hosts-interest-question', {'text': '你想听哪个领域的新闻？'}, '选择兴趣', 1)
case('ask-about-actual-narration', {'text': '新闻机构报道，探测器已完成着陆。', 'listener': {'turn': 1}}, '新闻提问', 2)
case('respond-after-hearing-the-answer', {'text': '着陆已经完成，报道日期是今天。', 'listener': {'turn': 2}}, '回应回答', 3)
case('explicit-continuation', {'text': '继续。', 'listener': {'turn': 2}}, '继续收听', 3)
case('explicit-stop', {'text': '停一下', 'listener': {'turn': 1}}, '结束收听', 2)
case('bounded-dialogue-state', {'text': '好，先停在这里。', 'listener': {'turn': 3}}, '回应回答', 3)
context = [{'role': 'user', 'content': '你想听什么？'}, {'role': 'assistant', 'content': '我想听航天新闻。'}]
case('retain-the-real-interest-reply', {'text': '已着陆。', 'listener': {'turn': 1}, 'messages': context+[{'role': 'user', 'content': '已着陆。'}]}, '新闻提问', 2, context)
case('bounded-recent-context', {'text': '已着陆。', 'listener': {'turn': 1}, 'messages': [{'role': 'assistant', 'content': '前文'*1000}]*10}, '新闻提问', 2, [{'role': 'assistant', 'content': '前文'*400}]*6)
case('recover-the-interest-exchange-from-real-replies', {'text': '新闻机构报道，探测器已着陆。', 'messages': [{'role': 'assistant', 'content': '我想听航天新闻。'}]}, '新闻提问', 2)
case('recover-the-question-exchange-from-real-replies', {'text': '探测器已经完成着陆。', 'messages': [{'role': 'assistant', 'content': '我想听航天新闻。'}, {'role': 'assistant', 'content': '刚才的探测器已经着陆了吗？'}]}, '回应回答', 3)
assert spec['state_persistence']['fields'] == ['listener']
assert spec['graph']['outputs'][0]['name'] == 'assistant'
print(json.dumps({'source': node['source'], 'steps': node['limits']['max_execution_steps'], 'cases': cases}, ensure_ascii=False))
