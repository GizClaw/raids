require 'minitest/autorun'
require 'json'
require 'tmpdir'
require 'fileutils'
require_relative 'safety-fences'

class SafetyFencesTest < Minitest::Test
  def setup
    @fixtures = JSON.parse(File.read(File.join(__dir__, 'fixtures/safety-fences.json')))
  end

  def nodes(driver)
    @fixtures.fetch(driver).dig('spec', driver, 'graph', 'nodes')
  end

  def errors(driver)
    SafetyFences.errors(@fixtures.fetch(driver), "workflows/fixture/#{driver}.yaml")
  end

  def test_valid_player_prompts_and_unfenced_internal_nodes
    %w[flowcraft eino].each { |driver| assert_empty errors(driver) }
  end

  def test_flowcraft_missing_misplaced_or_labelled_fence
    ['', 'Safety: ', "Original instructions\n\n"].each do |prefix|
      nodes('flowcraft')[0]['config']['system_prompt'] = prefix + (prefix.empty? ? 'Speak.' : "${board.safety_fence}\n\nSpeak.")
      assert_equal 1, errors('flowcraft').size
    end
  end

  def test_internal_fence_does_not_cover_player_reply
    nodes('flowcraft')[0]['config']['system_prompt'] = 'Speak.'
    nodes('flowcraft')[1]['config']['system_prompt'] = "${board.safety_fence}\n\nReturn JSON."
    assert_equal 1, errors('flowcraft').size
    nodes('eino')[0]['messages'][0]['template'] = 'Speak.'
    nodes('eino')[2].merge!(nodes('eino')[0].merge('id' => 'extract-memory', 'outputs' => {'messages' => 'memory-messages'}))
    nodes('eino')[2]['messages'] = [{'role' => 'system', 'template' => "{safety_fence}\n\nExtract."}]
    assert_equal 1, errors('eino').size
  end

  def test_draft_forwarded_by_published_script
    draft = nodes('flowcraft')[0]
    draft['publish'] = false
    draft['config']['output_key'] = 'draft'
    nodes('flowcraft') << {'id' => 'publish', 'type' => 'script', 'publish' => true,
                           'config' => {'source' => 'host.emit("token", {content: board.getVar("draft")});'}}
    assert_empty errors('flowcraft')
    draft['config']['system_prompt'] = 'Speak.'
    assert_equal 1, errors('flowcraft').size
  end

  def test_eino_requires_binding_and_matching_system_variable
    prompt = nodes('eino')[0]
    prompt['inputs'].delete('safety_fence')
    assert_equal 1, errors('eino').size
    prompt['inputs']['fence'] = {'from' => 'input.safety_fence'}
    assert_equal 1, errors('eino').size
    prompt['messages'][0]['template'] = "{fence}\n\nSpeak."
    assert_empty errors('eino')
  end

  def test_eino_wrong_format_escaped_braces_user_message_or_missing_blank_line
    prompt = nodes('eino')[0]
    ['{{safety_fence}}', '{{.safety_fence}}', '{{ safety_fence }}', 'Safety: {safety_fence}'].each do |prefix|
      prompt['messages'][0]['template'] = prefix + "\n\nSpeak."
      assert_equal 1, errors('eino').size
    end
    prompt['messages'][0]['template'] = "{safety_fence}\nSpeak."
    assert_equal 1, errors('eino').size
    prompt['messages'][0] = {'role' => 'user', 'template' => "{safety_fence}\n\nSpeak."}
    assert_equal 1, errors('eino').size
  end

  def test_template_formats_and_clean_conditional_prefixes
    prompt = nodes('eino')[0]
    {'go_template' => ["{{.safety_fence}}\n\n", "{{if .safety_fence}}{{.safety_fence}}\n\n{{end}}"],
     'jinja2' => ["{{ safety_fence }}\n\n", "{% if safety_fence %}{{ safety_fence }}\n\n{% endif %}"]}.each do |format, prefixes|
      prompt['format'] = format
      prefixes.each do |prefix|
        prompt['messages'][0]['template'] = prefix + 'Speak.'
        assert_empty errors('eino')
      end
    end
  end

  def test_every_published_role_and_prompt_branch_is_checked
    %w[flowcraft eino].each do |driver|
      extra = Marshal.load(Marshal.dump(nodes(driver)[0]))
      extra['id'] = 'another-player-path'
      if driver == 'flowcraft'
        extra['config']['system_prompt'] = 'Speak.'
      else
        extra['inputs'].delete('safety_fence')
      end
      nodes(driver) << extra
      assert_match(/another-player-path/, errors(driver).join)
    end
  end

  def test_discovery_includes_variants_but_excludes_testers_and_giztests
    Dir.mktmpdir('safety-fence-fixture') do |root|
      FileUtils.mkdir_p("#{root}/raid")
      names = %w[flowcraft.yaml flowcraft.multi-role.yaml eino.yaml eino.multi-role.yaml eino-memory-async.yaml flowcraft-extra.yaml conversation.yaml zh-en.yaml]
      (names + %w[test.yaml test.multi-role.yaml tester.yaml eino.giztest.yaml flowcraft.giztest.yaml]).each do |name|
        File.write("#{root}/raid/#{name}", '{}')
      end
      assert_equal names.sort, SafetyFences.files(root).map { |file| File.basename(file) }
    end
    assert_empty SafetyFences.errors({}, 'workflows/fixture/test.multi-role.yaml')
  end

  def test_unfenced_drivers_are_exempt_and_unknown_drivers_fail
    %w[ast-translate doubao-realtime].each do |driver|
      assert_empty SafetyFences.errors({'spec' => {'driver' => driver}}, 'workflows/fixture/conversation.yaml')
    end
    assert_match(/unknown driver/, SafetyFences.errors({'spec' => {'driver' => 'other'}}, 'workflows/fixture/x.yaml').join)
  end

  def test_no_player_path_fails_closed
    %w[flowcraft eino].each do |driver|
      nodes(driver).clear
      assert_match(/no player reply prompt/, errors(driver).join)
    end
  end
end
