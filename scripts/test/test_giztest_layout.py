import copy
import glob
import json
import os
import sys
import tempfile
import unittest

import yaml

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import giztest_layout as layout  # noqa: E402


def text_step():
    return {'id': 'response', 'peer_stream': {'input': '同一输入', 'require_audio': False},
            'expect': {'/text': {'non_empty': True}, '/first_text_ms': {'maximum': 6000}}}


def audio_step():
    step = text_step()
    step['peer_stream']['require_audio'] = True
    step['expect'].update({'/audio_bytes': {'minimum': 1}, '/audio_eos': {'equals': True}})
    return step


def rpc(client, method='register'):
    return {'id': f'{client}_{method}', 'client': client,
            'rpc': {'method': f'server.{method}'}}


def response(client, timeout='2m'):
    return {'id': f'{client}_response', 'client': client, 'timeout': timeout, 'peer_stream': {}}


class GiztestCapabilityTest(unittest.TestCase):
    def rejected(self, check, *args):
        with self.assertRaises(SystemExit):
            check(*args)

    def test_split_references_include_finally_parallel_captures_and_relays(self):
        doc = {'clients': {'a': {}}, 'variables': {'answer': {'direction': 'output'}},
               'steps': [{'id': 'batch', 'parallel': [response('a')], 'capture': {'answer': '/a_response/text'}}],
               'finally': [{'id': 'emit', 'output': {'variable': 'answer'}}]}
        layout.check_local_references(doc, 'fixture')
        bad = copy.deepcopy(doc); del bad['steps'][0]['capture']
        self.rejected(layout.check_local_references, bad, 'fixture')
        bad = copy.deepcopy(doc); bad['finally'].append(rpc('missing'))
        self.rejected(layout.check_local_references, bad, 'fixture')
        bad = copy.deepcopy(doc); bad['finally'][0]['output']['variable'] = 'foreign'
        self.rejected(layout.check_local_references, bad, 'fixture')
        bad = copy.deepcopy(doc); bad['steps'][0]['parallel'][0]['peer_stream']['input'] = '${foreign}'
        self.rejected(layout.check_local_references, bad, 'fixture')
        bad = copy.deepcopy(doc); bad['finally'].append({'id': 'relay', 'workspace_relay': {'first_client': 'a', 'second_client': 'missing'}})
        self.rejected(layout.check_local_references, bad, 'fixture')

    def test_speech_requires_registration_on_its_own_client(self):
        speech = {'id': 'synthesize', 'client': 'a', 'speech': {}}
        layout.check_speech_order({'steps': [rpc('a'), speech]}, 'fixture')
        self.rejected(layout.check_speech_order, {'steps': [speech, rpc('a')]}, 'fixture')
        self.rejected(layout.check_speech_order, {'steps': [rpc('b'), speech]}, 'fixture')

    def test_idle_gap_includes_finally_and_sums_independent_operations(self):
        doc = {'steps': [rpc('a'), rpc('b'), response('b'), response('b')],
               'finally': [rpc('a', 'run.stop')]}
        self.rejected(layout.check_idle_gaps, doc, 'fixture')
        del doc['steps'][3]
        layout.check_idle_gaps(doc, 'fixture')

    def test_idle_boundary_and_reconnect_do_not_hide_existing_gap(self):
        doc = {'steps': [rpc('a'), response('b', '3m'), rpc('a', 'run.stop')]}
        layout.check_idle_gaps(doc, 'fixture')
        doc['steps'][1]['timeout'] = '181s'
        self.rejected(layout.check_idle_gaps, doc, 'fixture')
        doc['steps'][2] = {'id': 'a_reconnect', 'client': 'a', 'reconnect': {}}
        self.rejected(layout.check_idle_gaps, doc, 'fixture')

    def test_parallel_and_relay_count_all_participating_clients(self):
        doc = {'steps': [rpc('a'), rpc('b'),
                         {'id': 'parallel', 'timeout': '4m', 'parallel': [response('a'), response('b')]},
                         {'id': 'relay', 'timeout': '40m', 'workspace_relay': {'first_client': 'a', 'second_client': 'b'}}],
               'finally': [rpc('a', 'run.stop'), rpc('b', 'run.stop')]}
        layout.check_idle_gaps(doc, 'fixture')
        doc['steps'][2]['parallel'].pop()
        self.rejected(layout.check_idle_gaps, doc, 'fixture')

    def test_late_suite_reconnects_before_first_registration(self):
        doc = {'steps': [rpc('a'), response('a', '4m'), rpc('b')]}
        self.rejected(layout.check_idle_gaps, doc, 'fixture')
        doc['steps'].insert(2, {'id': 'b_reconnect', 'client': 'b', 'reconnect': {}})
        layout.check_idle_gaps(doc, 'fixture')

    def test_keepalive_must_be_registered_and_necessary(self):
        status = {**rpc('a', 'run.status'), 'id': 'a_setup_keepalive'}
        doc = {'steps': [rpc('a'), rpc('b'), response('b'), status, response('b')],
               'finally': [rpc('a', 'run.stop')]}
        layout.check_idle_gaps(doc, 'fixture')
        del doc['steps'][4]
        self.rejected(layout.check_idle_gaps, doc, 'fixture')
        doc['steps'] = [status]
        self.rejected(layout.check_idle_gaps, doc, 'fixture')

    def test_cross_file_parity_rejects_input_gate_capture_and_cleanup_drift(self):
        with tempfile.TemporaryDirectory() as tmp:
            left = os.path.join(tmp, 'eino_history.yaml'); right = os.path.join(tmp, 'eino.yaml')
            source = {'variables': {}, 'steps': [{**audio_step(), 'id': 'eino_history_response', 'client': 'eino_history'}],
                      'finally': [rpc('eino_history', 'run.stop')]}
            with open(left, 'w', encoding='utf-8') as f:
                yaml.safe_dump(source, f, allow_unicode=True, sort_keys=False)
            baseline = json.loads(json.dumps(source).replace('eino_history', 'eino'))

            def compare(doc):
                with open(right, 'w', encoding='utf-8') as f:
                    yaml.safe_dump(doc, f, allow_unicode=True, sort_keys=False)
                layout.compare_files(left, right, 'eino_history', 'eino', {'eino_history': True, 'eino': True})
            compare(baseline)
            mutations = [
                lambda d: d['steps'][0]['peer_stream'].update({'input': 'different input'}),
                lambda d: d['steps'][0]['expect']['/first_text_ms'].update({'maximum': 7000}),
                lambda d: d['steps'][0].update({'capture': {'answer': '/text'}}),
                lambda d: d.update({'finally': []}),
            ]
            for mutate in mutations:
                changed = copy.deepcopy(baseline); mutate(changed)
                self.rejected(compare, changed)

    def test_workspace_must_exist_before_selection(self):
        create = {'id': 'create', 'client': 'doubao', 'rpc': {
            'method': 'server.workspace.create', 'request': {'name': '${workspace}'}}}
        select = {'id': 'select', 'client': 'doubao', 'rpc': {
            'method': 'server.run.workspace.set', 'request': {'workspace_name': '${workspace}'}}}
        layout.check_workspace_order({'steps': [create, select]}, 'fixture')
        self.rejected(layout.check_workspace_order, {'steps': [select, create]}, 'fixture')

    def test_workspace_name_and_fence_must_be_bound_in_profile(self):
        profile = {'workflows': {'assistant': {'resource_id': 'canonical-workflow'}},
                   'safety_fences': {'off': {'prompt': 'Follow Workflow rules.'}, 'child': {'prompt': 'Child policy.'}}}
        request = {'name': '${workspace}', 'workflow_name': 'assistant',
                   'parameters': {'eino_workspace_parameters': {'safety_fence_level': 'off'}}}
        doc = {'steps': [{'id': 'create', 'rpc': {'method': 'server.workspace.create', 'request': request}}]}
        layout.check_workspace_contract(doc, 'fixture', profile)
        for change in [
            lambda r: r.update(collection='assistants'),
            lambda r: r.update(workflow_name='canonical-workflow'),
            lambda r: r['parameters']['eino_workspace_parameters'].pop('safety_fence_level'),
            lambda r: r['parameters']['eino_workspace_parameters'].update(safety_fence_level='SAFETY_FENCE_LEVEL_OFF'),
            lambda r: r['parameters']['eino_workspace_parameters'].update(safety_fence_level=False),
        ]:
            bad = copy.deepcopy(doc)
            change(bad['steps'][0]['rpc']['request'])
            self.rejected(layout.check_workspace_contract, bad, 'fixture', profile)
        # A consuming Profile without fences permits an omitted selection.
        del request['parameters']['eino_workspace_parameters']['safety_fence_level']
        layout.check_workspace_contract(doc, 'fixture', {'workflows': profile['workflows']})

    def test_workspace_delete_requires_matching_local_creation(self):
        create = {'id': 'create', 'client': 'a', 'rpc': {
            'method': 'server.workspace.create', 'request': {'name': '${workspace}'}}}
        delete = {'id': 'delete', 'client': 'a', 'rpc': {
            'method': 'server.workspace.delete', 'request': {'name': '${workspace}'}}}
        layout.check_workspace_order({'steps': [create], 'finally': [delete]}, 'fixture')
        self.rejected(layout.check_workspace_order, {'steps': [], 'finally': [delete]}, 'fixture')
        self.rejected(layout.check_workspace_order, {'steps': [delete, create]}, 'fixture')
        self.rejected(layout.check_workspace_order, {'steps': [create], 'finally': [{**delete, 'client': 'b'}]}, 'fixture')
        self.rejected(layout.check_workspace_order, {'steps': [create], 'finally': [delete, delete]}, 'fixture')

    def test_variant_ownership_does_not_overlap(self):
        for engine in ('eino',):
            multi = f'{engine}_multi_role'
            for implementation in (engine, multi):
                peer = {'id': f'{implementation}_response', 'client': f'{implementation}__transitions'}
                verdict = {'id': f'{implementation}_emit_verdict', 'output': {'variable': f'{implementation}_verdict'}}
                for step in (peer, verdict):
                    self.assertTrue(layout.owns(step, implementation))
                    self.assertFalse(layout.owns(step, multi if implementation == engine else engine))

    def test_live_workflow_capabilities(self):
        for file in glob.glob('workflows/learn-*/raid.json'):
            raid = os.path.basename(os.path.dirname(file))
            self.assertEqual({'eino': True}, layout.tts_capabilities(raid))
        self.assertEqual({'eino_history': True, 'eino_memory_async': True,
                          'eino_memory_recall': True}, layout.tts_capabilities('journey-guide'))

    def test_non_tts_rejects_every_audio_assertion_family(self):
        layout.check_audio(text_step(), False, 'fixture')
        for path in ('audio_eos', 'audio_eos_ms', 'audio_bytes', 'first_audio_ms', 'audio_integrity/streams', 'audio_pacing/underruns'):
            step = text_step()
            step['expect'][f'/{path}'] = {'equals': 0}
            self.rejected(layout.check_audio, step, False, 'fixture')
        step = text_step()
        step['peer_stream']['first_audio_timeout'] = '3s'
        self.rejected(layout.check_audio, step, False, 'fixture')
        self.rejected(layout.check_audio, audio_step(), False, 'fixture')

    def test_tts_requires_audio_output_and_completion(self):
        layout.check_audio(audio_step(), True, 'fixture')
        self.rejected(layout.check_audio, text_step(), True, 'fixture')
        step = audio_step()
        del step['expect']['/audio_eos']
        self.rejected(layout.check_audio, step, True, 'fixture')
        step['peer_stream']['completion'] = 'first_response'
        layout.check_audio(step, True, 'fixture')

    def test_projection_preserves_input_and_non_audio_assertions(self):
        self.assertEqual(layout.without_audio([text_step()]), layout.without_audio([audio_step()]))
        for key in ('input', '/text', '/first_text_ms'):
            step = audio_step()
            if key == 'input':
                step['peer_stream'][key] = '不同输入'
            else:
                step['expect'][key] = {'maximum': 1}
            self.assertNotEqual(layout.without_audio([text_step()]), layout.without_audio([step]))
        self.assertNotEqual(text_step(), audio_step())  # Same-capability comparisons keep all audio fields.

    def test_child_quality_rejects_exam_inputs_and_contract_drift(self):
        doc = layout.load_yaml('tests/giztest/quality/story-aesop.eino.multi-role.giztest.yaml')
        layout.check_child_quality(doc, 'fixture')
        changed = copy.deepcopy(doc)
        step = next(s for s in changed['steps'] if s.get('peer_stream') is not None)
        step['peer_stream']['input'] = '请只说这个角色知道的事。'
        self.rejected(layout.check_child_quality, changed, 'fixture')
        changed = copy.deepcopy(doc)
        step = next(s for s in changed['steps'] if s.get('peer_stream') is not None)
        step['expect']['/text']['min_length'] = 120
        self.rejected(layout.check_child_quality, changed, 'fixture')

    def test_multi_role_review_requires_captured_reply_and_safety_redirect(self):
        doc = layout.load_yaml('tests/giztest/quality/story-aesop.eino.multi-role.giztest.yaml')
        layout.check_multi_role_review(doc, 'fixture')
        missing = copy.deepcopy(doc)
        next(s for s in missing['steps'] if s['id'].endswith('_review_history')).pop('capture', None)
        self.rejected(layout.check_multi_role_review, missing, 'fixture')
        missing = copy.deepcopy(doc)
        safety = next(s for s in [c for s in missing['steps'] for c in s.get('parallel', [])]
                      if '现实里' in s.get('peer_stream', {}).get('input', ''))
        parent = next(s for s in missing['steps'] if safety in s.get('parallel', []))
        parent['expect'][f"/{safety['id']}/text"].pop('contains_any', None)
        self.rejected(layout.check_multi_role_review, missing, 'fixture')

    def test_matcher_operand_types_and_stream_capture_types(self):
        valid = {'id': 'reply', 'peer_stream': {}, 'expect': {'/text': {'non_empty': True, 'min_length': 1, 'not_contains': ['【', '】']}}}
        doc = {'steps': [valid], 'variables': {'reply': {'type': 'string'}}}
        layout.check_matcher_types(doc, 'fixture')
        for key, value in {'non_empty': 'true', 'min_length': True, 'contains': [], 'not_contains': [True], 'maximum': '1', 'unknown': 1}.items():
            bad = copy.deepcopy(doc)
            bad['steps'][0]['expect']['/text'][key] = value
            self.rejected(layout.check_matcher_types, bad, 'fixture')
            bad['finally'] = bad.pop('steps')
            self.rejected(layout.check_matcher_types, bad, 'fixture')
            bad['steps'] = [{'id': 'batch', 'parallel': bad.pop('finally')}]
            self.rejected(layout.check_matcher_types, bad, 'fixture')
        valid['capture'] = {'reply': '/text'}
        self.rejected(layout.check_matcher_types, doc, 'fixture')
        doc['steps'] = [{'id': 'batch', 'parallel': [{k: v for k, v in valid.items() if k != 'capture'}], 'capture': {'reply': '/reply/text'}}]
        self.rejected(layout.check_matcher_types, doc, 'fixture')


if __name__ == '__main__':
    unittest.main()
