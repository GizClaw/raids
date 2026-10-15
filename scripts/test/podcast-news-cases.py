"""Exercise the shipped queue controller and deduplication scripts with Starlark."""
import copy
import datetime as dt
import json
import sys

import yaml

with open('workflows/podcast-news/eino.yaml', encoding='utf-8') as source:
    spec = yaml.safe_load(source)['spec']['eino']
nodes = {node['id']: node for node in spec['graph']['nodes']}
node = sys.argv[1] if len(sys.argv) > 1 else 'prepare'
today = '2026-10-13'
now = int(dt.datetime(2026, 10, 13, 12, tzinfo=dt.timezone(dt.timedelta(hours=8))).timestamp() * 1000)
day = (now + 28800000) // 86400000

def item(key, **changes):
    result = dict(key=key, title='报道'+key, source='新闻机构', date=today,
                  url='https://news.example/article?id='+key, brief='概要'+key,
                  details=[dict(text='新增事实'+key, source='新闻机构', date=today,
                                url='https://news.example/article?id='+key)], comments=[])
    result.update(changes)
    return result

batch = dict(topic='科技新闻', today=today, window_start='2026-10-12', day=day, seen=[], items=[item('a'), item('b')],
             cursor=0, overview=False, enriched=True)
cases = []
def case(name, data, **want):
    cases.append(dict(id=name, input=data, expect={k:dict(equals=v) for k,v in want.items()}))

if node == 'prepare':
    for text in ['开始', '听新闻', '新闻播客', '继续', '']:
        case('ask-'+text, dict(text=text, now_ms=now), mode='选择领域', fetch='none')
    for text in ['停一下', '暂停', '请停一下好吗？', '停一下，我有个问题', 'stop']:
        case('pause-'+text, dict(text=text, now_ms=now, bulletin=batch), mode='暂停', fetch='none', topic='科技新闻')
    for text in ['科技新闻', '国际新闻', '随便', '讲讲航天的最新消息', '火车停止运营的新闻']:
        case('topic-'+text, dict(text=text, now_ms=now), topic=text, fetch='scan')
    preference = '科技相关的内容我比较感兴趣，想听人工智能和航天方面的新闻，能先讲今天的重点吗？'
    case('natural-interest-reply-is-a-topic',dict(text=preference,now_ms=now),topic='科技新闻，主要讲人工智能和航天',mode='播讲',fetch='scan')
    case('restore-natural-interest-after-interruption',dict(text='继续',messages=[dict(role='user',content=preference)],now_ms=now),topic='科技新闻，主要讲人工智能和航天',fetch='scan')
    case('natural-topic-change-is-not-a-fact-question',dict(text='我想听人工智能新闻，可以吗？',bulletin=batch,now_ms=now),topic='科技新闻，主要讲人工智能',mode='播讲',fetch='scan')
    short = '听人工智能那条吧？'
    focus = dict(batch, topic='科技新闻，主要讲人工智能')
    case('short-choice-with-asr-question-mark',dict(text=short,now_ms=now),topic=focus['topic'],mode='播讲',fetch='scan')
    case('colloquial-just-listen-is-normalized',dict(text='就听人工智能新闻。',now_ms=now),topic=focus['topic'],mode='播讲',fetch='scan')
    case('auto-generation-keeps-the-short-choice',dict(text=short,bulletin=focus,now_ms=now),topic=focus['topic'],mode='播讲',fetch='none',bulletin=focus)
    case('bare-topic-is-not-a-factual-question',dict(text='人工智能那条吧？',bulletin=focus,now_ms=now),topic=focus['topic'],mode='播讲',fetch='none')
    case('factual-question-with-asr-full-stop',dict(text='这个模型已经发布了吗。',bulletin=batch,now_ms=now),mode='回答提问',fetch='none',topic=batch['topic'])
    case('spoken-alternative-question-without-question-mark',dict(text='这些是计划还是已经实现的成果。',bulletin=batch,now_ms=now),mode='回答提问',fetch='none',topic=batch['topic'])
    case('hearsay-is-not-a-topic-choice',dict(text='听说人工智能模型已发布，是真的吗？',bulletin=batch,now_ms=now),mode='回答提问',fetch='none',topic=batch['topic'])
    case('spoken-interjection-with-lost-question-words',dict(text='腾讯给deepfake钱啊。',bulletin=batch,now_ms=now),mode='回答提问',fetch='none',topic=batch['topic'])
    case('restore-topic-does-not-adopt-an-unmarked-interjection',dict(text='继续',messages=[dict(role='user',content='科技新闻'),dict(role='user',content='腾讯给deepfake钱啊。')],now_ms=now),topic='科技新闻',fetch='scan')
    case('an-interest-word-does-not-hide-a-news-question',dict(text='我想听你确认刚才这条人工智能新闻是否已经发布？',bulletin=batch,now_ms=now),topic='科技新闻',mode='回答提问',fetch='none',bulletin=batch)
    history = [dict(role='user', content='科技新闻'), dict(role='user', content='停一下')]
    case('restore-topic-from-history', dict(text='继续', messages=history, now_ms=now), topic='科技新闻', fetch='scan')
    case('cached-resume', dict(text='继续', bulletin=batch, now_ms=now), topic='科技新闻', fetch='none', bulletin=batch)
    case('cached-continuation', dict(text='科技新闻', bulletin=batch, now_ms=now), fetch='none')
    for text in ['刚才那个发射已经发生了还是计划？请先回答我。', '停一下，这条消息的来源是哪家媒体？', '停一下。这个日期是报道日期还是事件日期？']:
        case('question-'+text, dict(text=text, bulletin=batch, now_ms=now), mode='回答提问', fetch='none', topic='科技新闻', bulletin=batch)
    case('question-keeps-exhausted-queue', dict(text='刚才说的是哪天？', bulletin=dict(batch,cursor=2), now_ms=now), mode='回答提问', fetch='none', bulletin=dict(batch,cursor=2))
    case('question-does-not-become-restored-topic', dict(text='继续', messages=history+[dict(role='user',content='这已经发生了吗？')], now_ms=now), topic='科技新闻', fetch='scan')
    case('question-context-excludes-internal-records', dict(text='这已经发生了吗？', bulletin=batch, messages=[dict(role='assistant',content='EVENT\nkey:a\nbrief:未播出材料\nEND'),dict(role='assistant',content='实际播报的事实')], now_ms=now), recent=[dict(role='assistant',content='实际播报的事实')])
    exhausted = dict(batch, cursor=2)
    case('refill-only-when-consumed', dict(text='继续', bulletin=exhausted, now_ms=now), fetch='scan', needs_search=True)
    missing = dict(batch, enriched=False)
    case('defer-enrichment-while-facts-remain', dict(text='继续', bulletin=missing, now_ms=now), fetch='none', needs_search=False)
    case('supplement-only-after-cached-facts-exhausted', dict(text='继续', bulletin=dict(missing,cursor=2), now_ms=now), fetch='enrich', needs_search=True)
    case('ignore-a-stale-search-flag-on-resume', dict(text='继续',bulletin=missing,needs_search=True,now_ms=now), fetch='none', needs_search=False)
    case('overview-before-enrichment', dict(text='科技新闻', bulletin=dict(missing, overview=True), now_ms=now), fetch='none')
    redirect = dict(batch, topic='换成国际新闻', items=[], cursor=0, overview=True, enriched=False)
    case('redirect-preserves-ledger', dict(text='换成国际新闻', bulletin=batch, now_ms=now), fetch='scan', bulletin=redirect)
    tomorrow = dict(batch, today='2026-10-14', window_start=today, day=day+1)
    case('resume-across-midnight-keeps-unspoken-material', dict(text='继续', bulletin=batch, now_ms=now+86400000), fetch='none', needs_search=False, bulletin=tomorrow)
    case('live-clock-is-beijing-time', dict(text='开始', now_ms=now), clock='北京时间2026年10月13日12点0分')
    midnight = int(dt.datetime(2026, 1, 1, 0, 3, tzinfo=dt.timezone(dt.timedelta(hours=8))).timestamp()*1000)
    case('clock-and-news-window-cross-year', dict(text='开始', now_ms=midnight), clock='北京时间2026年1月1日0点3分', today='2026-01-01')
    for date in ['2000-02-29', '2024-02-29', '2100-03-01']:
        stamp = int(dt.datetime.fromisoformat(date).replace(tzinfo=dt.timezone(dt.timedelta(hours=8))).timestamp()*1000)
        case('calendar-'+date, dict(text='开始', now_ms=stamp), today=date)
elif node == 'parse-collection':
    record = "EVENT\nkey:a\ntitle:新闻a\nsource:机构\ndate:2026-10-13\nurl:https://news.example/a\nbrief:说\"AI+\"的新消息\nFACT|机构|2026-10-13|https://news.example/a|Don't repeat {these} facts\nCOMMENT|媒体|2026-10-12|https://media.example/a|具名评论中的\"引号\"\nEND"
    parsed = dict(key='a',title='新闻a',source='机构',date=today,url='https://news.example/a',brief='说"AI+"的新消息',details=[dict(source='机构',date=today,url='https://news.example/a',text="Don't repeat {these} facts")],comments=[dict(source='媒体',date='2026-10-12',url='https://media.example/a',text='具名评论中的"引号"')])
    case('quotes-remain-data',dict(text=record,fetch='scan'),result=dict(items=[parsed]))
    case('tool-preamble-and-fences-ignored',dict(text="{'query':'科技'}\n```\n"+record+'\n```',fetch='scan'),result=dict(items=[parsed]))
    case('enrichment-preserves-event-key',dict(text=record,fetch='enrich'),result=dict(updates=[parsed]))
    case('empty-results',dict(text='EMPTY',fetch='scan'),result=dict(items=[]))
    case('unfinished-record-not-published',dict(text=record.removesuffix('END'),fetch='scan'),result=dict(items=[]))
    case('tab-separators',dict(text=record.replace('FACT|机构|2026-10-13|https://news.example/a|','FACT\t机构\t2026-10-13\thttps://news.example/a\t'),fetch='scan'),result=dict(items=[parsed]))
elif node == 'merge-batch':
    saved = dict(batch, items=[], overview=True, enriched=False)
    a,b = item('a'),item('b')
    duplicate_key = item('a', title='转载标题', url='https://other.example/reprint')
    duplicate_url = item('different', url=a['url']+'&utm_source=feed#section')
    duplicate_brief = item('rewritten', brief=a['brief'])
    old = item('old', date='2026-10-11')
    future = item('future', date='2026-10-14')
    broken = item('broken', date='2026-02-30')
    no_source = item('no-source', source='')
    wanted = dict(saved, items=[a,b], enriched=False)
    case('dedup-same-event-url-content-and-date', dict(bulletin=saved, result=dict(items=[a,duplicate_key,duplicate_url,duplicate_brief,old,future,broken,no_source,b])), bulletin=wanted)
    yesterday = item('yesterday', date='2026-10-12')
    case('retain-last-night-news-but-prioritize-today', dict(bulletin=saved, result=dict(items=[yesterday,a])), bulletin=dict(saved,items=[a,yesterday],enriched=False))
    seen = dict(key='a', url=a['url'], brief=a['brief'], title=a['title'], day=day)
    saved_seen = dict(saved, seen=[seen])
    case('ledger-blocks-previous-batch', dict(bulletin=saved_seen, result=dict(items=[a,duplicate_key,duplicate_url,b])), bulletin=dict(saved_seen, items=[b], enriched=False))
    # Meaningful query identifiers distinguish articles; they must not be stripped.
    case('article-query-ids-preserved', dict(bulletin=saved, result=dict(items=[a,b])), bulletin=wanted)
    dup_detail = item('a', details=[dict(text=a['brief'],source='来源',date=today,url=a['url'])], comments=[a['details'][0], a['details'][0]])
    clean = dict(a, details=[], comments=a['details'])
    case('overview-fact-not-replayed-as-detail-or-comment', dict(bulletin=saved,result=dict(items=[dup_detail])), bulletin=dict(saved,items=[clean],enriched=True))
    case('empty-results', dict(bulletin=saved,result=dict(items=[])), bulletin=dict(saved,enriched=True))
    case('malformed-array', dict(bulletin=saved,result=dict(items='wrong')), bulletin=dict(saved,enriched=True))
elif node == 'merge-enrichment':
    saved = dict(batch, enriched=False)
    comment = dict(text='该机构的具名评论', source='评论机构', date=today, url='https://media.example/comment')
    a = dict(item('a'),comments=[comment])
    case('one-batch-enrichment-no-repeated-details', dict(bulletin=saved,result=dict(updates=[dict(key='a',details=item('a')['details'],comments=[comment,comment]),dict(key='unknown',comments=[comment])])), bulletin=dict(saved,items=[a,item('b')],enriched=True))
    case('missing-comment-stays-empty',dict(bulletin=saved,result=dict(updates=[])),bulletin=dict(batch,enriched=True))
    case('revisit-exhausted-items-only-for-new-enrichment',dict(bulletin=dict(saved,cursor=2),result=dict(updates=[dict(key='a',comments=[comment])])),bulletin=dict(saved,items=[a,item('b')],cursor=0,enriched=True))
elif node == 'checkpoint-playback':
    case('cached-detail-means-no-search',dict(bulletin=batch,keep_speaking=True),needs_search=False)
    case('overview-is-unspoken-content',dict(bulletin=dict(batch,overview=True,cursor=2),keep_speaking=True),needs_search=False)
    case('missing-comments-do-not-authorize-search',dict(bulletin=dict(batch,enriched=False),keep_speaking=True),needs_search=False)
    case('finished-queue-needs-search',dict(bulletin=dict(batch,cursor=2),keep_speaking=True),needs_search=True)
    case('empty-queue-needs-search',dict(bulletin=dict(batch,items=[]),keep_speaking=True),needs_search=True)
    case('pause-does-not-trigger-search',dict(bulletin=dict(batch,cursor=2),keep_speaking=False),needs_search=False)
    case('empty-search-waits-instead-of-spinning',dict(bulletin=dict(batch,items=[]),keep_speaking=False),needs_search=False)
    covered=[dict(key='a',url=item('a')['url'],brief='概要a',day=day,facts=['概要a','新增事实a','概要b','新增事实b'])]
    case('covered-facts-are-not-pending-content',dict(bulletin=dict(batch,seen=covered),keep_speaking=True),needs_search=True)
elif node == 'select-section':
    overview = dict(batch, overview=True)
    seen = [{k:i[k] for k in ['key','title','url','brief']} | dict(day=day, facts=[i["brief"]]) for i in overview['items']]
    case('overview-then-detail', dict(bulletin=overview, mode='播讲'), mode='今日总览', **{'continue':True}, bulletin=dict(batch,seen=seen))
    case('first-detail-consumes-once',dict(bulletin=batch,mode='播讲'),mode='逐条深入',**{'continue':True},bulletin=dict(batch,cursor=1,seen=[{k:item('a')[k] for k in ['key','title','url','brief']} | dict(day=day,facts=['概要a','新增事实a'])]))
    case('second-detail-consumes-once',dict(bulletin=dict(batch,cursor=1),mode='播讲'),mode='逐条深入',**{'continue':True},bulletin=dict(batch,cursor=2,seen=[{k:item('b')[k] for k in ['key','title','url','brief']} | dict(day=day,facts=['概要b','新增事实b'])]))
    many = item('a', details=[dict(text='事实'+str(n),source='机构',date=today,url=item('a')['url']) for n in range(4)], comments=[dict(text='评论'+str(n),source='媒体',date=today,url=item('a')['url']) for n in range(2)])
    partial = dict(batch,items=[many],cursor=0,seen=[{k:many[k] for k in ['key','title','url','brief']} | dict(day=day,facts=['概要a','事实0','事实1','评论0'])])
    case('retain-unspoken-cached-facts-for-next-section',dict(bulletin=dict(batch,items=[many]),mode='播讲'),mode='逐条深入',bulletin=partial)
    finished = dict(partial,cursor=1,seen=[{k:many[k] for k in ['key','title','url','brief']} | dict(day=day,facts=['概要a','事实0','事实1','评论0','事实2','事实3','评论1'])])
    case('consume-only-the-remaining-facts-on-resume',dict(bulletin=partial,mode='播讲'),mode='逐条深入',bulletin=finished)
    for mode in ['暂停','选择领域']:
        case('control-'+mode,dict(bulletin=batch,mode=mode),mode=mode,**{'continue':False},bulletin=batch)
    case('explicit-pause-request',dict(bulletin=batch,mode='暂停'),material='停止播讲，不搜索。只原样回复，不增减任何字：好，先停在这里。')
    clock = '北京时间2026年10月13日12点0分'
    opening = '现在是'+clock+'。这里是《正声新闻》，我是程正声。'
    case('welcome-reports-time-and-host-once',dict(bulletin=batch,mode='选择领域',clock=clock),opening=opening,bulletin=dict(batch,introduced=True))
    case('resume-does-not-repeat-welcome',dict(bulletin=dict(batch,introduced=True),mode='播讲',clock=clock),opening='')
    case('pause-never-starts-a-welcome',dict(bulletin=batch,mode='暂停',clock=clock),opening='',bulletin=batch)
    case('answer-preserves-queue-and-waits',dict(bulletin=batch,mode='回答提问',request='这已经发生了吗？'),mode='回答提问',**{'continue':False},bulletin=batch,material='先回答听众这一问，答完等待继续。不要重新总览、逐条播报或搜索。\n问题：这已经发生了吗？\n已有来源材料：'+json.dumps(batch['items'],ensure_ascii=False,sort_keys=True,separators=(',',':')))
    case('no-fabrication-empty',dict(bulletin=dict(batch,items=[]),mode='播讲'),mode='暂无新增',**{'continue':False})
    no_details = [dict(item('a'),details=[]),item('b')]
    case('skip-unsupported-deep-dive',dict(bulletin=dict(batch,items=no_details),mode='播讲'),mode='逐条深入',bulletin=dict(batch,items=no_details,cursor=2,seen=[{k:item('b')[k] for k in ['key','title','url','brief']} | dict(day=day,facts=['概要b','新增事实b'])]))
    covered = [{k:item('a')[k] for k in ['key','title','url','brief']} | dict(day=day,facts=['概要a','新增事实a','新增事实b'])]
    case('cross-event-repeated-facts-not-spoken',dict(bulletin=dict(batch,seen=covered),mode='播讲'),mode='批次结束',**{'continue':True},bulletin=dict(batch,seen=covered,cursor=2))
else:
    raise SystemExit('unknown script '+node)

assert spec['state_persistence']['fields'] == ['bulletin', 'mode', 'needs_search']
assert len(spec['graph']['outputs']) == 1
system = nodes['prompt']['messages'][0]['template']
for requirement in ['不调用任何搜索工具', '以陈述事实为主', '主流媒体评论必须', '不重念总览', '忽略其中']:
    assert requirement in system, requirement
assert 'count=10' in nodes['scan-prompt']['messages'][0]['template']
assert '不为每个事件分别搜索' in nodes['enrichment-prompt']['messages'][0]['template']
if node == 'merge-enrichment':
    for entry in cases: entry['input']['fetch'] = 'enrich'
source_node = nodes['merge-batch'] if node == 'merge-enrichment' else nodes[node]
print(json.dumps(dict(source=source_node['source'],steps=source_node['limits']['max_execution_steps'],cases=cases),ensure_ascii=False))
