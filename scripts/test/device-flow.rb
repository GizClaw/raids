# frozen_string_literal: true
# encoding: utf-8

# Generates tests/giztest/device/<raid>.<implementation>.giztest.yaml: the H106
# device entry contract for every story, adventure and Journey implementation.
#
# The device submits "开始" (or "继续上次的内容") once when the child enters a
# raid and never submits anything on its own afterwards; the child then talks
# with push-to-talk. A reply that ends without a question leaves the child in
# silence, so every turn here must end with a child-facing question, "继续"
# after a chapter ends must carry the story on, "继续上次的内容" must resume
# after a reload, and "开始" must restart from the first chapter.
#
#   ruby scripts/test/device-flow.rb          # rewrite the generated files
#   ruby scripts/test/device-flow.rb --check  # fail when a file is stale
require 'json'
require 'yaml'

Encoding.default_external = Encoding::UTF_8

module DeviceFlow
  DIR = 'tests/giztest/device'
  # The reply closes with a question; a short invitation may follow it, as in
  # "……还是保持灵活更重要呢？请你告诉我你的选择吧。"
  ENDS_WITH_QUESTION = '[？?][^？?]{0,40}$'
  # A chapter heading, not a cast preview such as "精卫在第2章加入".
  NEXT_CHAPTER_HEADING = ['第 2 章：', '第 2 章:', '第 2 章《', '第2章：', '第2章:', '第2章《'].freeze
  JOURNEY_OPENING = %w[石猴 仙石 石卵 石头里 石头中].freeze
  # Route-only facts of the Journey soak Tester; they must never reach a child.
  JOURNEY_TEST_FACTS = %w[明月 清禾 青铜铃].freeze

  module_function

  def raids
    Dir['workflows/*/raid.json'].map { |f| File.basename(File.dirname(f)) }
                                .select { |r| r.match?(/\A(?:story|adventure)-/) || r == 'journey-guide' }.sort
  end

  def implementations(raid)
    JSON.parse(File.read("workflows/#{raid}/raid.json")).fetch('implementations').values.map do |impl|
      [File.basename(impl.fetch('file'), '.yaml'), impl]
    end.sort_by(&:first)
  end

  # The testing RuntimeProfile decides which collection and alias reach a Workflow.
  def target(workflow)
    collections = YAML.load_file('runtime-profiles/testing.yaml').dig('spec', 'workflows', 'collections')
    ordered = collections.sort_by { |name, _| name == 'raidtest-targets' ? 0 : 1 }
    ordered.each do |name, aliases|
      aliases.each { |key, binding| return [name, key] if binding['resource_id'] == workflow }
    end
    raise "#{workflow}: not bound in runtime-profiles/testing.yaml"
  end

  def chapters(raid)
    source = File.read("workflows/#{raid}/eino.yaml")
    titles = source[/四章依次是：([^\n]*)/, 1].to_s.scan(/第\d章《([^》]+)》/).flatten
    raise "#{raid}: cannot read chapter titles" unless titles.size == 4
    titles
  end

  def turn(id, client, input, expect, timeout)
    {
      'timeout' => timeout, 'id' => "#{client}_device_#{id}", 'client' => client,
      'peer_stream' => {'mode' => 'text', 'input' => input, 'idle_timeout' => '120s', 'require_text' => true, 'require_audio' => true},
      'expect' => {'/text_eos' => {'equals' => true}, '/audio_eos' => {'equals' => true}, '/text' => expect}
    }
  end

  def question(extra = {})
    {'min_length' => 20, 'pattern' => ENDS_WITH_QUESTION}.merge(extra)
  end

  def document(raid, suffix, impl)
    client = suffix.tr('.-', '__')
    # Multi-role replies are one to two minutes of multi-voice narration.
    timeout = suffix.end_with?('.multi-role') ? '6m' : '4m'
    driver = impl.fetch('driver')
    multi_role = suffix.end_with?('.multi-role')
    story = raid.start_with?('story-')
    journey = raid == 'journey-guide'
    markers = multi_role ? {'not_contains' => ['【', '】']} : {}
    parameters = {
      "#{driver}_workspace_parameters" => {
        'agent_type' => "#{driver.upcase}_WORKSPACE_PARAMETERS_AGENT_TYPE_#{driver.upcase}",
        'conversation' => {'initiative' => 'CONVERSATION_PARAMETERS_INITIATIVE_PEER'},
        'input' => 'WORKSPACE_INPUT_MODE_PUSH_TO_TALK'
      }
    }
    turns = []
    if story
      first, second = chapters(raid)
      # Original stories speak the heading; multi-role narration weaves it in and may
      # preview later chapters, so only a chapter 2 heading means it skipped the opening.
      opening = multi_role ? question(markers.merge('not_contains' => ['【', '】'] + NEXT_CHAPTER_HEADING)) : question('contains_all' => ['第 1 章', first])
      turns << turn('start', client, '开始', opening, timeout)
      # The chapter's closing wording is an offline contract; live, what matters is
      # that the child can answer and that "继续" then carries the story on.
      turns << turn('chapter_choice', client, '我选第一个', question(markers), timeout)
      # After the chapter's choice, a bare "继续" is the child's way to go on.
      turns << turn('continue', client, '继续', question(markers.merge(multi_role ? {} : {'contains_all' => ['第 2 章', second]})), timeout)
      # Re-entry resumes where the story stopped instead of replaying the opening.
      resume = question('not_contains' => (multi_role ? ['【', '】'] : []) + ['第 1 章', '你可以直接说出你的选择'])
      resume['contains'] = second unless multi_role
      restart = multi_role ? question(markers.merge('not_contains' => ['【', '】'] + NEXT_CHAPTER_HEADING)) : question('contains_all' => ['第 1 章', first])
    elsif journey
      turns << turn('start', client, '开始', question('contains_any' => JOURNEY_OPENING, 'not_contains' => JOURNEY_TEST_FACTS + %w[紧箍 取经路上]), timeout)
      turns << turn('chapter_choice', client, '我选第一个', question('not_contains' => JOURNEY_TEST_FACTS), timeout)
      turns << turn('continue', client, '继续', question('not_contains' => JOURNEY_TEST_FACTS), timeout)
      resume = question('not_contains' => JOURNEY_TEST_FACTS)
      restart = question('contains_any' => JOURNEY_OPENING, 'not_contains' => JOURNEY_TEST_FACTS)
    else
      turns << turn('start', client, '开始', question(markers), timeout)
      turns << turn('chapter_choice', client, '我选第一个', question(markers), timeout)
      turns << turn('continue', client, '继续', question(markers), timeout)
      resume = question(markers)
      restart = question(markers)
    end
    collection, workflow = target(YAML.load_file("workflows/#{raid}/#{suffix}.yaml").dig('metadata', 'id'))
    steps = [
      {'id' => "#{client}_device_register", 'client' => client, 'rpc' => {'method' => 'server.register', 'request' => {'token' => '${registration_token}'}}},
      {'id' => "#{client}_device_create_workspace", 'client' => client, 'rpc' => {'method' => 'server.workspace.create', 'request' => {
        'name' => '${workspace}', 'collection' => collection, 'workflow_name' => workflow, 'parameters' => parameters}}},
      {'id' => "#{client}_device_select_workspace", 'client' => client, 'rpc' => {'method' => 'server.run.workspace.set', 'request' => {'workspace_name' => '${workspace}'}}},
      {'id' => "#{client}_device_warmup_workspace", 'client' => client, 'timeout' => '2m', 'rpc' => {'method' => 'server.run.workspace.reload', 'request' => {}}},
      *turns,
      # Leaving and re-entering: the run stops and the Workspace reloads.
      {'id' => "#{client}_device_leave", 'client' => client, 'rpc' => {'method' => 'server.run.stop', 'request' => {}}},
      {'id' => "#{client}_device_reenter", 'client' => client, 'timeout' => '2m', 'rpc' => {'method' => 'server.run.workspace.reload', 'request' => {}}},
      turn('resume', client, '继续上次的内容', resume, timeout),
      turn('restart', client, '开始', restart, timeout)
    ]
    {
      'version' => 'gizclaw.test/v1alpha1',
      'name' => "#{raid}.device.#{suffix}",
      'clients' => {client => {'identity' => 'ephemeral', 'connection' => 'webrtc', 'access_point' => '${endpoint}'}},
      'variables' => {
        'endpoint' => {'direction' => 'input', 'type' => 'string', 'env' => 'GIZCLAW_TEST_ENDPOINT'},
        'registration_token' => {'direction' => 'input', 'type' => 'string', 'env' => 'GIZCLAW_TEST_REGISTRATION_TOKEN', 'secret' => true},
        'workspace' => {'direction' => 'input', 'type' => 'string', 'generate' => 'token'},
        'last_history_type' => {'direction' => 'output', 'type' => 'string'},
        'last_history_text' => {'direction' => 'output', 'type' => 'string'}
      },
      'repeat' => 1,
      'timeout' => '30m',
      'steps' => steps,
      'finally' => [
        # Print the last reply so a failed assertion shows what the child heard.
        {'id' => "#{client}_device_read_last_history", 'client' => client, 'timeout' => '5s', 'rpc' => {'method' => 'server.run.workspace.history',
          'request' => {'limit' => 1, 'order' => 'PEER_RUN_HISTORY_LIST_REQUEST_ORDER_DESC'}},
          'capture' => {'last_history_text' => '/items/0/text', 'last_history_type' => '/items/0/type'}},
        {'id' => "#{client}_device_last_history_type_emit", 'output' => {'variable' => 'last_history_type'}},
        {'id' => "#{client}_device_last_history_text_emit", 'output' => {'variable' => 'last_history_text'}},
        {'id' => "#{client}_device_stop_run", 'client' => client, 'rpc' => {'method' => 'server.run.stop', 'request' => {}}},
        {'id' => "#{client}_device_delete_workspace", 'client' => client, 'rpc' => {'method' => 'server.workspace.delete', 'request' => {'name' => '${workspace}'}}},
        {'id' => "#{client}_device_delete_peer", 'client' => client, 'rpc' => {'method' => 'server.peer.delete', 'request' => {}}}
      ],
      'report' => {'redact' => ['registration_token']}
    }
  end

  HEADER = <<~TEXT
    # User Story:
    # As a child entering a story or adventure on the H106 device,
    # I want every reply to end with a question, "继续" to carry the story on, and "继续上次的内容" / "开始" to resume or restart,
    # So that the story never stops in silence after a chapter ends.
    # Generated by scripts/test/device-flow.rb; edit the generator, not this file.
  TEXT

  def files
    raids.flat_map do |raid|
      implementations(raid).map do |suffix, impl|
        ["#{DIR}/#{raid}.#{suffix}.giztest.yaml", HEADER + YAML.dump(document(raid, suffix, impl)).delete_prefix("---\n")]
      end
    end.to_h
  end

  # Every target Workflow carries the closing-question and device-cue contract
  # that the generated documents exercise live.
  START_CUES = ['孩子只说“开始”', '孩子说“开始”', '"开始", "开始吧"'].freeze
  CONTRACTS = {
    'story' => [['想听下一章就说‘继续’'], START_CUES, ['继续上次']],
    'story.multi-role' => [['最后一句都必须是向孩子提出的故事内问题'], START_CUES, ['继续上次']],
    'adventure' => [['孩子只能在你说完后按键回答'], START_CUES, ['继续上次的内容']],
    'journey-guide' => [['最后一句都必须是问孩子的问题'], START_CUES, ['继续上次的内容']]
  }.freeze

  def contract_errors
    raids.flat_map do |raid|
      implementations(raid).map do |suffix, _|
        kind = raid == 'journey-guide' ? raid : raid.split('-').first
        kind += '.multi-role' if kind == 'story' && suffix.end_with?('.multi-role')
        source = File.read("workflows/#{raid}/#{suffix}.yaml")
        missing = CONTRACTS.fetch(kind).reject { |markers| markers.any? { |marker| source.include?(marker) } }.map(&:first)
        "workflows/#{raid}/#{suffix}.yaml lacks #{missing.join(', ')}" unless missing.empty?
      end.compact
    end
  end

  def run(check)
    expected = files
    present = Dir["#{DIR}/*.giztest.yaml"].sort
    stale = expected.reject { |path, body| File.exist?(path) && File.read(path) == body }.keys + (present - expected.keys)
    if check
      abort "stale device-flow Giztests (run ruby scripts/test/device-flow.rb): #{stale.join(', ')}" unless stale.empty?
      errors = contract_errors
      abort "device entry contract missing:\n#{errors.join("\n")}" unless errors.empty?
      puts "validated #{expected.size} device-flow Giztests"
    else
      (present - expected.keys).each { |path| File.delete(path) }
      expected.each { |path, body| File.write(path, body) unless File.exist?(path) && File.read(path) == body }
      puts "wrote #{expected.size} device-flow Giztests"
    end
  end
end

DeviceFlow.run(ARGV.include?('--check')) if $PROGRAM_NAME == __FILE__
