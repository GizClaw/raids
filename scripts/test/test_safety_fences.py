import copy
import json
import os
import tempfile
import unittest

import safety_fences


class SafetyFencesTest(unittest.TestCase):
    def setUp(self):
        with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fixtures/safety-fences.json'), encoding='utf-8') as f:
            self.fixtures = json.load(f)

    def nodes(self, driver):
        return self.fixtures[driver]['spec'][driver]['graph']['nodes']

    def errors(self, driver):
        return safety_fences.errors(self.fixtures[driver], f'workflows/fixture/{driver}.yaml')

    def test_valid_player_prompts_and_unfenced_internal_nodes(self):
        for driver in ('eino',):
            self.assertEqual([], self.errors(driver))


    def test_internal_fence_does_not_cover_player_reply(self):
        self.nodes('eino')[0]['messages'][0]['template'] = 'Speak.'
        self.nodes('eino')[2].update({**self.nodes('eino')[0], 'id': 'extract-memory', 'outputs': {'messages': 'memory-messages'}})
        self.nodes('eino')[2]['messages'] = [{'role': 'system', 'template': '{safety_fence}\n\nExtract.'}]
        self.assertEqual(1, len(self.errors('eino')))


    def test_eino_requires_binding_and_matching_system_variable(self):
        prompt = self.nodes('eino')[0]
        prompt['inputs'].pop('safety_fence', None)
        self.assertEqual(1, len(self.errors('eino')))
        prompt['inputs']['fence'] = {'from': 'input.safety_fence'}
        self.assertEqual(1, len(self.errors('eino')))
        prompt['messages'][0]['template'] = '{fence}\n\nSpeak.'
        self.assertEqual([], self.errors('eino'))

    def test_eino_wrong_format_escaped_braces_user_message_or_missing_blank_line(self):
        prompt = self.nodes('eino')[0]
        for prefix in ['{{safety_fence}}', '{{.safety_fence}}', '{{ safety_fence }}', 'Safety: {safety_fence}']:
            prompt['messages'][0]['template'] = prefix + '\n\nSpeak.'
            self.assertEqual(1, len(self.errors('eino')))
        prompt['messages'][0]['template'] = '{safety_fence}\nSpeak.'
        self.assertEqual(1, len(self.errors('eino')))
        prompt['messages'][0] = {'role': 'user', 'template': '{safety_fence}\n\nSpeak.'}
        self.assertEqual(1, len(self.errors('eino')))

    def test_template_formats_and_clean_conditional_prefixes(self):
        prompt = self.nodes('eino')[0]
        for format, prefixes in {'go_template': ['{{.safety_fence}}\n\n', '{{if .safety_fence}}{{.safety_fence}}\n\n{{end}}'],
                                 'jinja2': ['{{ safety_fence }}\n\n', '{% if safety_fence %}{{ safety_fence }}\n\n{% endif %}']}.items():
            prompt['format'] = format
            for prefix in prefixes:
                prompt['messages'][0]['template'] = prefix + 'Speak.'
                self.assertEqual([], self.errors('eino'))

    def test_every_published_role_and_prompt_branch_is_checked(self):
        for driver in ('eino',):
            extra = copy.deepcopy(self.nodes(driver)[0])
            extra['id'] = 'another-player-path'
            extra['inputs'].pop('safety_fence', None)
            self.nodes(driver).append(extra)
            self.assertRegex(''.join(self.errors(driver)), 'another-player-path')

    def test_discovery_includes_variants_but_excludes_testers_and_giztests(self):
        with tempfile.TemporaryDirectory(prefix='safety-fence-fixture') as root:
            os.makedirs(f'{root}/raid')
            names = ['eino.yaml', 'eino.multi-role.yaml', 'eino-memory-async.yaml', 'eino-extra.yaml', 'conversation.yaml', 'zh-en.yaml']
            for name in names + ['test.yaml', 'test.multi-role.yaml', 'tester.yaml', 'eino.giztest.yaml']:
                with open(f'{root}/raid/{name}', 'w', encoding='utf-8') as f:
                    f.write('{}')
            self.assertEqual(sorted(names), [os.path.basename(file) for file in safety_fences.files(root)])
        self.assertEqual([], safety_fences.errors({}, 'workflows/fixture/test.multi-role.yaml'))

    def test_realtime_instructions_and_unfenced_drivers(self):
        def realtime(instructions):
            return {'spec': {'driver': 'doubao-realtime', 'doubao_realtime': {'instructions': instructions}}}
        self.assertEqual([], safety_fences.errors(realtime('${input.safety_fence}\n\nSpeak.'), 'workflows/fixture/conversation.yaml'))
        for instructions in ['Speak.', 'Speak.\n\n${input.safety_fence}', '${safety_fence}\n\nSpeak.', 'Safety: ${input.safety_fence}\n\nSpeak.',
                             '${input.safety_fence}\nSpeak.']:
            self.assertEqual(1, len(safety_fences.errors(realtime(instructions), 'workflows/fixture/conversation.yaml')))
        self.assertEqual([], safety_fences.errors({'spec': {'driver': 'ast-translate'}}, 'workflows/fixture/zh-en.yaml'))
        self.assertRegex(''.join(safety_fences.errors({'spec': {'driver': 'other'}}, 'workflows/fixture/x.yaml')), 'unknown driver')

    def test_no_player_path_fails_closed(self):
        for driver in ('eino',):
            self.nodes(driver).clear()
            self.assertRegex(''.join(self.errors(driver)), 'no player reply prompt')


if __name__ == '__main__':
    unittest.main()
