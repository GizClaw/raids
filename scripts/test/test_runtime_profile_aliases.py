import unittest

import runtime_profile_aliases


class RuntimeProfileAliasesTest(unittest.TestCase):
    def test_alias_syntax(self):
        for name in ['story.animal-kingdom', 'learn.chinese-poetry-grade1-eino', 'asr', 'a']:
            self.assertTrue(runtime_profile_aliases.valid(name), name)
        for name in ['story.animal_kingdom', 'Story.alice', 'story..alice', '.story', 'story.', 'story-', '-story',
                     'story.a--b', '', ' story', 'a' * 64]:
            self.assertFalse(runtime_profile_aliases.valid(name), name)
        self.assertTrue(runtime_profile_aliases.valid('a' * 63))

    def test_every_alias_map_is_checked(self):
        binding = {'resource_id': 'x'}
        spec = {
            'workflows': {'learn.math_grade1': binding, 'ok': {**binding, 'tags': ['opaque tag with spaces']}},
            'resources': {'models': {'a_b.model': binding}, 'voices': {'ok.voice': binding},
                          'memories': {'Mem': binding}},
            'app_config': {'bad_key': 'v'},
        }
        names = [name for _, name in runtime_profile_aliases.errors(spec)]
        self.assertEqual(['learn.math_grade1', 'a_b.model', 'Mem', 'bad_key'], names)


if __name__ == '__main__':
    unittest.main()
