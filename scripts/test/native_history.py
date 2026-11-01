"""Retain exact native RPC snapshots; no content truth or fixed-row-count rules."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from datetime import datetime, timezone
import json
import threading
import time


def start(directory: Path, speakers: list[str]):
    prior = []

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_):
            pass

        def do_POST(self):
            nonlocal prior
            if self.path not in ['/snapshot', '/observe']:
                self.send_error(404)
                return
            size = int(self.headers.get('Content-Length', '0'))
            if not 0 < size <= 16 * 1024 * 1024:
                self.send_error(413)
                return
            value = json.loads(self.rfile.read(size))
            target = directory / ('history-' + str(value['round']) + '.json')
            if target.exists():
                self.send_error(409)
                return
            if self.path == '/observe':
                # Retain the immediate read without advancing the accepted
                # prefix. The caller records a fixed post-EOS visibility window;
                # the final snapshot still has every original exact check.
                folder = directory / 'history-observations'
                folder.mkdir(exist_ok=True)
                sample = value.get('sample', 'initial')
                if sample not in ['initial', 'settle1', 'settle2']:
                    self.send_error(400)
                    return
                delay = value.get('settle_delay_ms', 0)
                if type(delay) is not int or not 0 <= delay <= 1000:
                    self.send_error(400)
                    return
                observed = folder / (str(value['round']) + '-' + sample + '.json')
                value['collected_at'] = datetime.now(timezone.utc).isoformat()
                with observed.open('x') as output:
                    json.dump(value, output, ensure_ascii=False, indent=2)
                if delay:
                    time.sleep(delay / 1000)
                encoded = json.dumps({'retained': True}).encode()
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', str(len(encoded)))
                self.end_headers()
                self.wfile.write(encoded)
                return
            snapshot = value['snapshot']
            rows = list(reversed(snapshot.get('items', [])))
            by_name = {r['name']: r for r in prior}
            new = [r for r in rows if r['name'] not in by_name]
            old = [r for r in rows if r['name'] in by_name]
            users = [r for r in new if r['type'] == 'PEER_RUN_HISTORY_ENTRY_TYPE_GEAR']
            replies = [r for r in new if r['type'] == 'PEER_RUN_HISTORY_ENTRY_TYPE_AGENT']
            user_positions = [new.index(r) for r in users]
            reply_positions = [new.index(r) for r in replies]
            canonical = ''.join(r.get('text', '') for r in replies)
            rendered = canonical
            for name in speakers:
                rendered = rendered.replace('【' + name + '】', '')
            # A paginated latest-200 snapshot must overlap the retained prefix.
            # Every snapshot and the complete cumulative record list stay saved.
            visible_prior = prior[-len(old):] if old else []
            expected_prior = visible_prior if snapshot.get('has_next') else prior
            prefix_complete = [r['name'] for r in old] == [r['name'] for r in expected_prior]
            stable_fields = ['name','type','actor_name','text','created_at']
            checks = {
                'has_user_and_reply': bool(users and replies),
                'input_before_replies': bool(users and replies) and max(user_positions) < min(reply_positions),
                'previous_before_current': prefix_complete and rows == old + new,
                'prior_identity_and_body_preserved': all(
                    all(by_name[r['name']].get(key) == r.get(key) for key in stable_fields) for r in old),
                'agent_body_exact': bool(replies) and rendered == value['reply'],
                'transcript_text_exact': bool(users) and ''.join(r.get('text', '') for r in users) == value['heard'],
                'current_records_complete': bool(new) and (not snapshot.get('has_next') or bool(old)),
            }
            value.update(new_records=new, checks=checks, canonical_history=canonical,
                         record_count_policy='Preserve all legitimate records; no fixed per-turn count.')
            target.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
            prior = prior + new
            (directory / 'cumulative-history.json').write_text(json.dumps(prior, ensure_ascii=False, indent=2) + '\n')
            encoded = json.dumps({'checks': checks, 'canonical_history': canonical}, ensure_ascii=False).encode()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)

    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, thread
