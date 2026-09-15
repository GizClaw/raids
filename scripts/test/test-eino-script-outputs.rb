require 'minitest/autorun'
require_relative 'eino-script-outputs'

class EinoScriptOutputsTest < Minitest::Test
  def test_original_story_regression
    node = {'id' => 'control-narration', 'type' => 'script', 'language' => 'starlark',
            'outputs' => {'direction' => 'narration-context'},
            'source' => 'return {"chapter": str(chapter), "safety": safety_request, "choice_completed": choice_completed, "direction": direction}'}
    doc = {'spec' => {'eino' => {'graph' => {'nodes' => [node]}}}}
    assert_equal 3, EinoScriptOutputs.errors(doc, 'fixture').size
    node['source'] = 'return {"direction": direction}'
    assert_empty EinoScriptOutputs.errors(doc, 'fixture')
    node['source'] = 'return {"direction": direction, "chapter": str(chapter)}'
    node['outputs']['chapter'] = 'chapter-state'
    assert_empty EinoScriptOutputs.errors(doc, 'fixture')
  end

  def test_multiline_branches_nested_values_comments_and_strings
    source = <<~'SOURCE'
      # return {"comment": 0}
      message = "return {'string': 0}"
      if condition:
          return {
              'direction': fn(1, 2),
              "extra": {"nested": [1, 2]},
          }
      return {"other": "commas, braces } and escaped \"quotes\""}
    SOURCE
    assert_equal %w[direction extra other], EinoScriptOutputs.return_keys(source)
  end

  def test_other_script_languages
    source = <<~'SOURCE'
      // return {comment: 1}
      /* return {comment: 2} */
      function main() { return ({direction: `hello`, extra: call({nested: 1})}); }
    SOURCE
    assert_equal %w[direction extra], EinoScriptOutputs.return_keys(source)
  end
end
