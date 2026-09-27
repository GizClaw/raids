import textwrap
import unittest

import eino_script_outputs


class EinoScriptOutputsTest(unittest.TestCase):
    def test_original_story_regression(self):
        node = {'id': 'control-narration', 'type': 'script', 'language': 'starlark',
                'outputs': {'direction': 'narration-context'},
                'source': 'return {"chapter": str(chapter), "safety": safety_request, "choice_completed": choice_completed, "direction": direction}'}
        doc = {'spec': {'eino': {'graph': {'nodes': [node]}}}}
        self.assertEqual(3, len(eino_script_outputs.errors(doc, 'fixture')))
        node['source'] = 'return {"direction": direction}'
        self.assertEqual([], eino_script_outputs.errors(doc, 'fixture'))
        node['source'] = 'return {"direction": direction, "chapter": str(chapter)}'
        node['outputs']['chapter'] = 'chapter-state'
        self.assertEqual([], eino_script_outputs.errors(doc, 'fixture'))

    def test_multiline_branches_nested_values_comments_and_strings(self):
        source = textwrap.dedent(r'''
            # return {"comment": 0}
            message = "return {'string': 0}"
            if condition:
                return {
                    'direction': fn(1, 2),
                    "extra": {"nested": [1, 2]},
                }
            return {"other": "commas, braces } and escaped \"quotes\""}
        ''').lstrip('\n')
        self.assertEqual(['direction', 'extra', 'other'], eino_script_outputs.return_keys(source))

    def test_other_script_languages(self):
        source = textwrap.dedent(r'''
            // return {comment: 1}
            /* return {comment: 2} */
            function main() { return ({direction: `hello`, extra: call({nested: 1})}); }
        ''').lstrip('\n')
        self.assertEqual(['direction', 'extra'], eino_script_outputs.return_keys(source))


if __name__ == '__main__':
    unittest.main()
