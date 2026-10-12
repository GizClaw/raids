"""Render the two Workflow replies from a native Giztest replay as one dialogue.

The native index.html/report.json/replay.json remain unchanged. Forwarded input
and parallel first-response probes stay in those receipts, not in this player.
"""
import argparse
import html
import json
from pathlib import Path


def dialogue(record):
    replies = {}
    abandoned = set()
    for event in record['events']:
        if event.get('direction') != 'received' or event.get('role') != 'assistant':
            continue
        if event.get('step', '').startswith('start_'):
            continue  # parallel listener already recorded this output
        key = (event.get('step'), event.get('client'), event.get('stream'))
        if event.get('kind') == 'control' and 'interrupted' in str(event.get('error', '')):
            abandoned.add(key)
        if event.get('kind') not in ('text', 'audio'):
            continue
        message = replies.setdefault(key, {'step': event.get('step'), 'client': event.get('client'),
                                          'at': event['offset_ms'], 'text': '', 'audio': []})
        message['at'] = min(message['at'], event['offset_ms'])
        if event['kind'] == 'text':
            message['text'] += event.get('text', '')
        elif event.get('audio_data'):
            message['audio'].append(event['audio_data'])
    ordered = sorted((message for key, message in replies.items() if key not in abandoned),
                     key=lambda message: message['at'])
    # A relay also observes the host finishing the old narration before the
    # listener's first question. Preserve that prefix in the narration bubble.
    merged = []
    for message in ordered:
        if (merged and message['client'] == merged[-1]['client'] == 'podcast'
                and message['step'] == 'listener_and_host_followup'):
            merged[-1]['text'] += message['text']
            merged[-1]['audio'].extend(message['audio'])
        elif message['text'].strip() or message['audio']:
            merged.append(message)
    return merged


def render(folder):
    record = json.loads((folder/'replay.json').read_text())
    report = json.loads((folder/'report.json').read_text())
    messages = dialogue(record)
    data = json.dumps(messages, ensure_ascii=False).replace('</', '<\\/')
    status = '对话测试通过' if report['status'] == 'passed' else '对话测试未通过'
    page = TEMPLATE.replace('__STATUS__', html.escape(status)).replace('__DATA__', data)
    output = folder/'news-podcast-dialogue.html'
    output.write_text(page, encoding='utf-8')
    return output, messages


TEMPLATE = '''<!doctype html>
<html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>陆沉与米雅 · 新闻播客对话</title>
<style>
:root{color-scheme:light;--ink:#18283b;--muted:#63758b;--line:#dae3ed}*{box-sizing:border-box}body{margin:0;background:#f3f6fa;color:var(--ink);font:16px/1.7 system-ui,-apple-system,sans-serif}main{max-width:920px;margin:auto;padding:32px 24px 72px}h1{font-size:30px;line-height:1.35;margin:8px 0}.subtitle{color:var(--muted);margin:4px 0 20px}.badge{display:inline-block;border-radius:20px;padding:3px 12px;font-size:13px;background:#e4f2eb;color:#206747}.player{display:flex;flex-wrap:wrap;align-items:center;gap:12px;position:sticky;top:0;padding:16px 0;background:#f3f6faee;backdrop-filter:blur(12px);z-index:1}button{font:inherit;border:1px solid var(--line);border-radius:10px;padding:9px 16px;background:white;color:var(--ink);cursor:pointer}#play{background:#1d426a;color:white;border-color:#1d426a}#now{color:var(--muted);font-size:14px}.messages{display:flex;flex-direction:column;gap:18px}.message{width:88%;padding:19px 22px;background:white;border:1px solid var(--line);border-radius:16px;box-shadow:0 2px 7px #18283b04}.persona{align-self:flex-end;background:#eef8f4;border-color:#cee6dc}.who{font-size:14px;font-weight:650;color:#315a81;margin-bottom:8px}.persona .who{color:#2a755c}.words{white-space:pre-wrap}.active{outline:3px solid #81aacb;outline-offset:3px}audio{width:100%;height:36px;margin-top:14px}.note{font-size:13px;color:var(--muted);margin-top:30px}a{color:#315a81}
</style>
<main><span class="badge">__STATUS__</span><h1>新闻播客，先聊聊你想听什么</h1>
<p class="subtitle">主持人 · 陆沉（旁白声）　听众 · 米雅</p>
<div class="player"><button id="play">播放完整对话</button><button id="reset">从头开始</button><span id="now">主持人问兴趣 → 听众回答 → 新闻播报 → 听众提问</span></div>
<div id="messages" class="messages"></div>
<p class="note">文字与音频来自两个真实 Workflow 的 Giztest 接收记录。完整播放按双方回复的先后顺序进行，语音转发记录保留在原始报告中。<a href="index.html">查看原始 Giztest 报告</a>。本次验证开场问答、新闻提问和听众回应；连续恢复未包含在本次通过结论中。</p>
</main><script type="application/json" id="dialogue-data">__DATA__</script>
<script>
const data=JSON.parse(document.getElementById('dialogue-data').textContent);const queue=[];const root=document.getElementById('messages');const button=document.getElementById('play');const now=document.getElementById('now');let index=0,running=false;
for(const item of data){const box=document.createElement('article');box.className='message '+item.client;const who=document.createElement('div');who.className='who';who.textContent=item.client==='persona'?'听众 · 米雅':'主持人 · 陆沉';const text=document.createElement('div');text.className='words';text.textContent=item.text;box.append(who,text);root.append(box);for(const source of item.audio){const audio=document.createElement('audio');audio.controls=true;audio.preload='metadata';audio.src=source;audio.setAttribute('aria-label',who.textContent+'语音');box.append(audio);queue.push({audio,box,who:who.textContent});audio.addEventListener('ended',()=>{if(running&&queue[index]?.audio===audio){box.classList.remove('active');index++;advance();}});}}
function pause(){running=false;queue.forEach(q=>q.audio.pause());button.textContent='继续播放';}
for(const q of queue){q.audio.addEventListener('play',()=>{for(const other of queue){if(other.audio!==q.audio)other.audio.pause();other.box.classList.remove('active');}q.box.classList.add('active');index=queue.indexOf(q);now.textContent=q.who+'正在说话';});}
function advance(){if(index>=queue.length){running=false;index=0;button.textContent='再次播放完整对话';now.textContent='本段对话播放完毕';return;}const q=queue[index];q.box.classList.add('active');now.textContent=q.who+'正在说话';q.box.scrollIntoView({behavior:'smooth',block:'center'});q.audio.play().catch(()=>{pause();now.textContent='请点击对应语音的播放按钮';});}
button.addEventListener('click',()=>{if(running){pause();return;}running=true;button.textContent='暂停';advance();});
document.getElementById('reset').addEventListener('click',()=>{pause();index=0;queue.forEach(q=>{q.audio.currentTime=0;q.box.classList.remove('active');});button.textContent='播放完整对话';now.textContent='从主持人的开场问题开始';window.scrollTo({top:0,behavior:'smooth'});});
</script></html>'''


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('report_directory', type=Path)
    args = parser.parse_args()
    output, messages = render(args.report_directory)
    print(json.dumps({'html': str(output), 'speakers': [message['client'] for message in messages],
                      'messages': len(messages), 'audio_clips': sum(len(message['audio']) for message in messages)}, ensure_ascii=False))
