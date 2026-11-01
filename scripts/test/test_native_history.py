"""Behavior checks for raw/committed History acquisition, without model answers."""
import json
from pathlib import Path
import tempfile
import unittest
import urllib.request
from native_history import start


def record(name,kind,text):
    return {'name':name,'type':'PEER_RUN_HISTORY_ENTRY_TYPE_'+kind,'actor_name':'transcript' if kind=='GEAR' else 'assistant','text':text,'created_at':name}


class NativeHistoryTests(unittest.TestCase):
    def setUp(self):
        self.folder=tempfile.TemporaryDirectory();self.path=Path(self.folder.name)
        self.server,self.thread=start(self.path,['旁白','李白'])
        self.url='http://127.0.0.1:'+str(self.server.server_port)
    def tearDown(self):
        self.server.shutdown();self.server.server_close();self.thread.join();self.folder.cleanup()
    def post(self,endpoint,rows,round=0,reply='甲乙',**metadata):
        value={'round':round,'snapshot':{'available':True,'has_next':False,'items':list(reversed(rows))},'intended':'输入','heard':'输入','reply':reply}
        value.update(metadata)
        request=urllib.request.Request(self.url+endpoint,data=json.dumps(value,ensure_ascii=False).encode(),headers={'Content-Type':'application/json'},method='POST')
        with urllib.request.urlopen(request) as response:return json.load(response)
    def test_pending_observation_does_not_advance_committed_prefix(self):
        user=record('01','GEAR','输入')
        self.assertTrue(self.post('/observe',[user])['retained'])
        self.assertFalse((self.path/'history-0.json').exists())
        self.assertEqual(json.loads((self.path/'history-observations/0-initial.json').read_text())['snapshot']['items'],[user])
        rows=[user,record('02','AGENT','【旁白】甲'),record('03','AGENT','【李白】乙')]
        checks=self.post('/snapshot',rows)['checks']
        self.assertTrue(all(checks.values()),checks)
        self.assertEqual(len(json.loads((self.path/'history-0.json').read_text())['new_records']),3)
    def test_each_visibility_sample_is_retained_without_committing(self):
        rows=[record('01','GEAR','输入')]
        self.post('/observe',rows,sample='initial')
        partial=rows+[record('02','AGENT','【旁白】甲')]
        self.post('/observe',partial,sample='settle1')
        complete=partial+[record('03','AGENT','【李白】乙')]
        self.post('/observe',complete,sample='settle2')
        self.assertEqual(len(list((self.path/'history-observations').glob('*.json'))),3)
        self.assertTrue(all(self.post('/snapshot',complete)['checks'].values()))
    def test_immediate_missing_reply_is_still_failure(self):
        checks=self.post('/snapshot',[record('01','GEAR','输入')])['checks']
        self.assertFalse(checks['has_user_and_reply']);self.assertFalse(checks['agent_body_exact'])
    def test_reply_presence_does_not_waive_partial_body(self):
        rows=[record('01','GEAR','输入'),record('02','AGENT','【旁白】甲')]
        checks=self.post('/snapshot',rows)['checks']
        self.assertTrue(checks['has_user_and_reply']);self.assertFalse(checks['agent_body_exact'])
    def test_real_reordering_still_fails(self):
        rows=[record('01','AGENT','【旁白】甲乙'),record('02','GEAR','输入')]
        self.assertFalse(self.post('/snapshot',rows)['checks']['input_before_replies'])
    def test_whitespace_is_not_fuzzy_matched(self):
        rows=[record('01','GEAR','输入'),record('02','AGENT','【旁白】甲 乙')]
        self.assertFalse(self.post('/snapshot',rows)['checks']['agent_body_exact'])
    def test_prior_body_mutation_still_fails(self):
        rows=[record('01','GEAR','输入'),record('02','AGENT','【旁白】甲乙')]
        self.assertTrue(all(self.post('/snapshot',rows)['checks'].values()))
        rows[1]['text']='【旁白】被改写';rows.extend([record('03','GEAR','输入'),record('04','AGENT','【旁白】甲乙')])
        self.assertFalse(self.post('/snapshot',rows,round=1)['checks']['prior_identity_and_body_preserved'])


if __name__=='__main__':unittest.main()
