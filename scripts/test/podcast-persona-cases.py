"""Check the listener's persisted dialogue phases and real incoming context."""
import json
import sys
import yaml

spec = yaml.safe_load(open('workflows/podcast-news/test-persona.yaml', encoding='utf-8'))['spec']['eino']
node_id = sys.argv[1] if len(sys.argv) > 1 else 'listener-prepare'
node = next(n for n in spec['graph']['nodes'] if n['id'] == node_id)
if node_id == 'listener-reply':
    cases = [
        {'id': 'continuation-is-not-a-model-acknowledgment', 'input': {'mode': '继续收听', 'answer': '好的。'}, 'expect': {'reply': {'equals': '继续。'}}},
        {'id': 'stop-is-an-actionable-utterance', 'input': {'mode': '结束收听', 'answer': '嗯，明白了。'}, 'expect': {'reply': {'equals': '停一下。'}}},
        {'id': 'preserve-a-natural-question', 'input': {'mode': '新闻提问', 'answer': '  工厂已经建成了吗？  '}, 'expect': {'reply': {'equals': '工厂已经建成了吗？'}}},
        {'id': 'bound-the-observed-long-interest-reply', 'input': {'mode': '选择兴趣', 'answer': '我想听科技领域最近有哪些新消息。'}, 'expect': {'reply': {'equals': '想听科技新闻。'}}},
        {'id': 'preserve-a-short-colloquial-choice', 'input': {'mode': '选择兴趣', 'answer': '就想听人工智能的新闻。'}, 'expect': {'reply': {'equals': '就想听人工智能的新闻。'}}},
        {'id': 'replace-an-overlong-question-with-a-complete-question', 'input': {'mode': '新闻提问', 'answer': '请问上海在工博会公布的智能工厂建设目标是已经全部完成还是计划到2028年完成？'}, 'expect': {'reply': {'equals': '刚才那条消息的来源是哪家？'}}},
        {'id': 'do-not-repeat-the-host-in-an-acknowledgment', 'input': {'mode': '回应回答', 'answer': '好的，我知道这项行动已经启动，目标是到2028年完成。'}, 'expect': {'reply': {'equals': '嗯，明白了。'}}},
    ]
    print(json.dumps({'source': node['source'], 'steps': node['limits']['max_execution_steps'], 'cases': cases}, ensure_ascii=False))
    sys.exit(0)
cases = []
def case(name, data, mode, turn, recent=None, heard=None):
    want = {'mode': {'equals': mode}, 'listener': {'equals': {'turn': turn}}}
    if recent is not None:
        want['recent'] = {'equals': recent}
    if heard is not None:
        want['heard'] = {'equals': heard}
    cases.append({'id': name, 'input': data, 'expect': want})

case('answer-the-hosts-interest-question', {'text': '你想听哪个领域的新闻？'}, '选择兴趣', 1)
case('ask-about-actual-narration', {'text': '新闻机构报道，探测器已完成着陆。', 'listener': {'turn': 1}}, '新闻提问', 2)
case('respond-after-hearing-the-answer', {'text': '着陆已经完成，报道日期是今天。', 'listener': {'turn': 2}}, '回应回答', 3)
case('explicit-continuation', {'text': '继续。', 'listener': {'turn': 2}}, '继续收听', 1)
case('explicit-stop', {'text': '停一下', 'listener': {'turn': 1}}, '结束收听', 2)
case('bounded-dialogue-state', {'text': '好，先停在这里。', 'listener': {'turn': 3}}, '回应回答', 3)
context = [{'role': 'user', 'content': '你想听什么？'}, {'role': 'assistant', 'content': '我想听航天新闻。'}]
case('retain-the-real-interest-reply', {'text': '已着陆。', 'listener': {'turn': 1}, 'messages': context+[{'role': 'user', 'content': '已着陆。'}]}, '新闻提问', 2, context)
case('bounded-recent-context', {'text': '已着陆。', 'listener': {'turn': 1}, 'messages': [{'role': 'assistant', 'content': '前文'*1000}]*10}, '新闻提问', 2, [{'role': 'assistant', 'content': '前文'*400}]*6)
case('recover-the-interest-exchange-from-real-replies', {'text': '新闻机构报道，探测器已着陆。', 'messages': [{'role': 'assistant', 'content': '我想听航天新闻。'}]}, '新闻提问', 2)
case('recover-the-question-exchange-from-real-replies', {'text': '探测器已经完成着陆。', 'messages': [{'role': 'assistant', 'content': '我想听航天新闻。'}, {'role': 'assistant', 'content': '刚才的探测器已经着陆了吗？'}]}, '回应回答', 3)
case('incoming-asr-is-not-a-prior-listener-reply', {'text': '你想听哪个领域的新闻？', 'messages': [{'role': 'assistant', 'content': '你想听哪个领域的新闻？'}]}, '选择兴趣', 1)
case('real-interest-reply-recovers-an-overadvanced-phase', {'text': '报道说模型已经发布。', 'listener': {'turn': 2}, 'messages': [{'role': 'assistant', 'content': '我对人工智能新闻感兴趣。'}]}, '新闻提问', 2)
case('recover-a-short-colloquial-interest-reply', {'text': '报道说模型已经发布。', 'messages': [{'role': 'assistant', 'content': '给我播人工智能新闻就行。'}]}, '新闻提问', 2)
resumed = [{'role': 'assistant', 'content': '我想听人工智能新闻。'}, {'role': 'assistant', 'content': '模型发布了吗？'}, {'role': 'assistant', 'content': '哦，明白。'}, {'role': 'assistant', 'content': '继续。'}]
case('ask-about-the-new-resumed-broadcast', {'text': '另一机构的探测器已经着陆。', 'listener': {'turn': 1}, 'messages': resumed}, '新闻提问', 2)
case('acknowledge-the-second-answer', {'text': '探测器已经完成着陆。', 'listener': {'turn': 2}, 'messages': resumed+[{'role': 'assistant', 'content': '探测器已经着陆了吗？'}]}, '回应回答', 3)
case('acknowledge-a-repeated-live-broadcast', {'text': '好，我再重复一遍刚才的新闻。', 'listener': {'turn': 2}, 'messages': resumed+[{'role': 'assistant', 'content': '请重复一遍。'}]}, '回应回答', 3)
case('recover-a-clarification-without-a-checkpoint', {'text': '好，再说一下这条消息。', 'messages': [{'role': 'assistant', 'content': '请重复一遍。'}]}, '回应回答', 3)
case('recover-a-punctuation-free-followup-after-resume', {'text': '报道说的是下个月才发售。', 'listener': {'turn': 2}, 'messages': resumed+[{'role': 'assistant', 'content': '这是已经发售了吧。'}]}, '回应回答', 3)
case('use-the-recent-broadcast-tail', {'text': '早先的报道。'*150+'刚收到的新闻，探测器已着陆。', 'listener': {'turn': 1}}, '新闻提问', 2, heard=('早先的报道。'*150+'刚收到的新闻，探测器已着陆。')[-600:].split('。',1)[1])
assert spec['state_persistence']['fields'] == ['listener']
assert spec['graph']['outputs'][0]['name'] == 'assistant'
print(json.dumps({'source': node['source'], 'steps': node['limits']['max_execution_steps'], 'cases': cases}, ensure_ascii=False))
