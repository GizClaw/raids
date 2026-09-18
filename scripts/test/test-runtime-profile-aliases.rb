require 'minitest/autorun'
require_relative 'runtime-profile-aliases'

class RuntimeProfileAliasesTest < Minitest::Test
  def test_alias_syntax
    %w[story.animal-kingdom learn.chinese-poetry-grade1-eino asr a].each do |name|
      assert RuntimeProfileAliases.valid?(name), name
    end
    ['story.animal_kingdom', 'Story.alice', 'story..alice', '.story', 'story.', 'story-', '-story',
     'story.a--b', '', ' story', 'a' * 64].each do |name|
      refute RuntimeProfileAliases.valid?(name), name
    end
    assert RuntimeProfileAliases.valid?('a' * 63)
  end

  def test_every_alias_map_is_checked
    binding = {'resource_id' => 'x'}
    spec = {
      'workflows' => {'collections' => {
        'learn_x' => {'learn.math_grade1' => binding, 'shared' => binding},
        'story' => {'shared' => binding},
      }},
      'resources' => {'models' => {'a_b.model' => binding}, 'voices' => {'ok.voice' => binding},
                      'memories' => {'Mem' => binding}},
      'app_config' => {'bad_key' => 'v'},
    }
    names = RuntimeProfileAliases.errors(spec).map(&:last)
    assert_equal %w[learn_x learn.math_grade1 shared a_b.model Mem bad_key], names
  end
end
