# Shared structural view of tiered Giztests. Preserve per-client order and every assertion.
require_relative 'yaml_compat'
require 'json'
module GiztestLayout
  TIERS = %w[smoke quality soak].freeze
  AUDIO_ONLY = %w[ast-translate doubao-realtime].freeze
  AUDIO_PATH = %r{/(?:audio_eos(?:_ms)?|audio_bytes|first_audio_ms|audio_integrity|audio_pacing)(?:/|$)}.freeze
  # Resolve actual output capability, never infer it from an engine name or ASR.
  def self.tts_capabilities(raid)
    path = "workflows/#{raid}/raid.json"
    return {} unless File.exist?(path)
    JSON.parse(File.read(path)).fetch('implementations').to_h do |name, impl|
      voice = YAML.load_file("workflows/#{raid}/#{impl.fetch('file')}").dig('spec', impl.fetch('driver'), 'voice_adapter') || {}
      [name.tr('-', '_'), %w[default_voice speaker_voices node_voices].any? { |key| voice[key] && !voice[key].empty? }]
    end
  end
  def self.check_audio(step, capability, file)
    peer = step['peer_stream']
    return unless peer
    expect = step.fetch('expect', {})
    if capability
      check(peer['require_audio'] == true && expect.dig('/audio_bytes', 'minimum').to_i > 0,
            "#{file}: #{step['id']} TTS implementation needs audio output assertions")
      unless peer['completion'] == 'first_response'
        check(expect.dig('/audio_eos', 'equals') == true,
              "#{file}: #{step['id']} TTS response needs audio EOS")
      end
    else
      check(peer['require_audio'] == false && !peer.key?('first_audio_timeout') &&
            !expect.keys.any? { |key| key.match?(AUDIO_PATH) },
            "#{file}: #{step['id']} non-TTS implementation must not require audio")
    end
  end
  # Match pkgs/giztest Expectation operand types. Also reject the known
  # stream-fragment -> string capture mismatch before any network run.
  def self.check_matcher_types(doc, file)
    visit = lambda do |step|
      step.fetch('expect', {}).each do |path, matchers|
        check(matchers.is_a?(Hash), "#{file}: #{step['id']} #{path} needs matcher mapping")
        matchers.each do |key, value|
          valid = case key
          when 'equals' then true
          when 'present', 'non_empty' then value == true || value == false
          when 'count', 'min_length', 'max_length' then value.is_a?(Integer) && value >= 0
          when 'minimum', 'maximum' then value.is_a?(Numeric)
          when 'contains', 'pattern' then value.is_a?(String)
          when 'contains_all', 'contains_any', 'normalize' then value.is_a?(Array) && value.all? { |v| v.is_a?(String) }
          when 'not_contains' then value.is_a?(String) || (value.is_a?(Array) && value.all? { |v| v.is_a?(String) })
          else false
          end
          check(valid, "#{file}: #{step['id']} #{path} invalid #{key} value type")
        end
      end
      streams = step['parallel'] || [step]
      step.fetch('capture', {}).each do |name, path|
        streams.each do |child|
          target = step['parallel'] ? "/#{child['id']}/text" : '/text'
          check(!(child['peer_stream'] && path == target && doc.dig('variables', name, 'type') == 'string'),
                "#{file}: #{step['id']} /text fragments cannot be captured as string; use assistant history text")
        end
      end
      step.fetch('parallel', []).each { |child| visit.call(child) }
    end
    %w[steps finally].each { |section| doc.fetch(section, []).each { |step| visit.call(step) } }
  end
  def self.check_workspace_order(doc, file)
    # Generated Workspace names must be created on that client before selection.
    created = []
    local_names = steps(doc).map do |step|
      [step['client'], step.dig('rpc', 'request', 'name')] if step.dig('rpc', 'method') == 'server.workspace.create'
    end.compact
    %w[steps finally].flat_map { |section| steps(doc, section) }.each do |step|
      method = step.dig('rpc', 'method')
      if method == 'server.workspace.create'
        created << [step['client'], step.dig('rpc', 'request', 'name')]
      elsif method == 'server.workspace.delete'
        key = [step['client'], step.dig('rpc', 'request', 'name')]
        check(created.include?(key), "#{file}: #{step['id']} deletes a Workspace without creation in this file")
        created.delete(key)
      elsif method == 'server.run.workspace.set'
        key = [step['client'], step.dig('rpc', 'request', 'workspace_name')]
        check(!local_names.include?(key) || created.include?(key),
              "#{file}: #{step['id']} selects a local Workspace before creation")
      end
    end
  end
  # References must resolve within this split file; declarations alone do not
  # produce output values. Include parallel children and finally captures.
  def self.check_local_references(doc, file)
    clients = doc.fetch('clients').keys
    variables = doc.fetch('variables', {})
    all = %w[steps finally].flat_map { |section| steps(doc, section) }
    produced = all.flat_map { |step| step.fetch('capture', {}).keys + [step['save_as']].compact }
    walk = lambda do |value|
      case value
      when Hash
        value.each_value { |child| walk.call(child) }
      when Array
        value.each { |child| walk.call(child) }
      when String
        value.scan(/\$\{([^}]+)\}/).flatten.each do |name|
          check(variables.key?(name), "#{file}: undeclared variable #{name}")
          check(variables[name]['direction'] != 'output' || produced.include?(name),
                "#{file}: output variable #{name} has no capture/save_as")
        end
      end
    end
    walk.call(doc)
    all.each do |step|
      participants(step).each do |client|
        check(clients.include?(client), "#{file}: #{step['id']} undeclared client #{client}")
      end
      names = step.fetch('capture', {}).keys + [step['save_as'], step.dig('output', 'variable')].compact
      names.each { |name| check(variables.key?(name), "#{file}: #{step['id']} undeclared variable #{name}") }
      output = step.dig('output', 'variable')
      check(!output || variables[output]['direction'] != 'output' || produced.include?(output),
            "#{file}: #{step['id']} output #{output} has no capture/save_as")
    end
  end
  def self.check_speech_order(doc, file)
    registered = []
    %w[steps finally].each do |section|
      steps(doc, section).each do |step|
        registered << step['client'] if step.dig('rpc', 'method') == 'server.register'
        check(!step['speech'] || registered.include?(step['client']),
              "#{file}: #{step['id']} speech before client registration")
      end
    end
  end
  # Static scheduling budget: explicit step timeouts win; unary operations
  # without a declared bound reserve 30s. This checks scheduling, not network
  # liveness: streaming operations are traffic for all their participating peers.
  IDLE_LIMIT = 180
  def self.duration(value)
    value.to_s.scan(/([0-9.]+)(ms|s|m|h)/).sum do |number, unit|
      number.to_f * {'ms' => 0.001, 's' => 1, 'm' => 60, 'h' => 3600}.fetch(unit)
    end
  end
  def self.participants(step)
    return step['parallel'].flat_map { |child| participants(child) }.uniq if step['parallel']
    relay = step['workspace_relay']
    return relay.values_at('first_client', 'second_client') if relay
    [step['client']].compact
  end
  def self.budget(step)
    return duration(step['timeout']) if step['timeout']
    return 0 if step['output']
    return duration(step['peer_stream']['idle_timeout'] || '90s') if step['peer_stream']
    30
  end
  def self.idle_gap_errors(doc)
    idle = {}; registered = []; elapsed = 0; errors = []
    (doc.fetch('steps') + doc.fetch('finally', [])).each do |step|
      active = participants(step)
      registered << step['client'] if step.dig('rpc', 'method') == 'server.register'
      if step['id'].include?('keepalive') && !registered.include?(step['client'])
        errors << "#{step['id']} status before registration"
      end
      active.each do |client|
        if idle.key?(client)
          errors << "#{step['id']} #{client} idle gap #{idle[client]}s exceeds #{IDLE_LIMIT}s" if idle[client] > IDLE_LIMIT
        elsif elapsed > IDLE_LIMIT && !step['reconnect']
          errors << "#{step['id']} #{client} first use after #{elapsed}s needs reconnect before registration"
        end
        idle[client] = 0
      end
      idle.each_key { |client| idle[client] += budget(step) unless active.include?(client) }
      elapsed += budget(step)
      idle.delete(step['client']) if step.dig('rpc', 'method') == 'server.peer.delete'
    end
    errors
  end
  def self.check_idle_gaps(doc, file)
    errors = idle_gap_errors(doc)
    check(errors.empty?, "#{file}: #{errors.first}")
    doc['steps'].each_with_index do |step, index|
      next unless step['id'].include?('keepalive')
      shortened = doc.merge('steps' => doc['steps'].each_with_index.reject { |_, n| n == index }.map(&:first))
      check(!idle_gap_errors(shortened).empty?, "#{file}: #{step['id']} unnecessary keepalive")
    end
  end
  def self.inventory(raid)
    return {'conversation' => 'doubao'} if raid == 'doubao-realtime'
    path = "workflows/#{raid}/raid.json"
    if File.exist?(path)
      JSON.parse(File.read(path)).fetch('implementations').to_h do |key, impl|
        [File.basename(impl.fetch('file'), '.yaml'), key.tr('-', '_')]
      end
    else
      Dir["workflows/#{raid}/*.yaml"].to_h { |f| [File.basename(f, '.yaml'), File.basename(f, '.yaml').tr('-', '_')] }
    end
  end
  def self.compare_files(left_file, right_file, baseline, impl, capabilities)
    left_doc, right_doc = [left_file, right_file].map { |f| YAML.load_file(f) }
    vars = [[left_doc, baseline], [right_doc, impl]].map do |doc, name|
      normalize(doc.fetch('variables'), name)
    end
    check(vars[0] == vars[1], "#{left_file}/#{right_file}: variable definitions differ")
    %w[steps finally].each do |section|
      left = sequence(left_doc, baseline, section)
      right = sequence(right_doc, impl, section)
      if capabilities.fetch(baseline) != capabilities.fetch(impl)
        left, right = [left, right].map { |seq| without_audio(seq) }
      end
      index = (0...[left.size, right.size].max).find { |n| left[n] != right[n] }
      check(index.nil?, "#{left_file}/#{right_file}: #{section} mismatch at #{index}: #{left[index].inspect if index} != #{right[index].inspect if index}")
    end
  end
  def self.without_audio(sequence)
    sequence.map do |step|
      copy = Marshal.load(Marshal.dump(step))
      if copy['peer_stream']
        copy['peer_stream'].delete('require_audio')
        copy['peer_stream'].delete('first_audio_timeout')
      end
      copy.fetch('expect', {}).delete_if { |key, _| key.match?(AUDIO_PATH) }
      copy
    end
  end
  def self.check(ok, message)
    abort message unless ok
  end
  # Flatten parallel streams while retaining their parent timeout and assertions.
  def self.steps(doc, section = 'steps')
    doc.fetch(section, []).flat_map do |step|
      next [step] unless step['parallel']
      step.fetch('parallel').map do |child|
        copy = step.reject { |k, _| %w[id parallel expect capture].include?(k) }.merge(child)
        prefix = "/#{child.fetch('id')}"
        expected = step.fetch('expect', {}).select { |path, _| path.start_with?(prefix + '/') }
        copy['expect'] = expected.to_h { |path, value| [path.delete_prefix(prefix), value] } unless expected.empty?
        captured = step.fetch('capture', {}).select { |_, path| path.start_with?(prefix + '/') }
        copy['capture'] = captured.to_h { |variable, path| [variable, path.delete_prefix(prefix)] } unless captured.empty?
        copy
      end
    end
  end
  # Multi-role quality owns its child interactions; original probe contracts do
  # not apply. Audio and latency assertions are still checked independently.
  def self.check_child_quality(doc, file)
    all = steps(doc)
    peers = all.select { |s| s['peer_stream'] }
    check(!peers.empty?, "#{file}: missing child interactions")
    peers.each do |step|
      input = step.dig('peer_stream', 'input').to_s
      check(!input.match?(/只确认|只说|不要推进|知识边界|亲自回应|最多问/), "#{file}: inherited exam probe")
      contract = step.dig('expect', '/text') || {}
      next if step['client'].end_with?('_tester')
      check(contract['min_length'] == 1, "#{file}: missing non-empty reply")
      check(contract.fetch('not_contains', []) == ['【', '】'], "#{file}: marker guards only")
      check((contract.keys - %w[min_length not_contains contains_any]).empty?, "#{file}: rigid content assertion")
      if input.include?('现实里')
        check(contract.fetch('contains_any', []).include?('家长'), "#{file}: missing trusted-adult redirect")
      else
        check(!contract.key?('contains_any'), "#{file}: non-safety phrase gate")
      end
    end
    %w[改主意 为什么 咕咕 叫什么].each do |cue|
      check(peers.any? { |s| s.dig('peer_stream', 'input').include?(cue) }, "#{file}: missing child interaction #{cue}")
    end
    recall = all.index { |s| s.dig('peer_stream', 'input').to_s.include?('叫什么') }
    check(recall && all[0...recall].any? { |s| s.dig('rpc', 'method') == 'server.run.workspace.reload' && s['client'] == all[recall]['client'] }, "#{file}: missing recall reload")
    check(peers.any? { |s| s['client'].end_with?('_tester') && s.dig('peer_stream', 'input').start_with?("REVIEW\n") }, "#{file}: missing LLM quality review")
  end
  # Every candidate response is captured into the automatic Tester review.
  # Giztest checks adult cues; the Tester deterministically checks both cue groups.
  def self.check_multi_role_review(doc, file)
    peers = steps(doc).select { |s| s['peer_stream'] && !s['client'].end_with?('_tester') }
    review = steps(doc).find { |s| s.dig('peer_stream', 'input').to_s.start_with?("REVIEW\n") }
    check(review && review['client'].end_with?('_tester'), "#{file}: missing automatic Tester review")
    peers.each do |peer|
      all = steps(doc)
      following = all[(all.index { |s| s['id'] == peer['id'] } + 1)..-1].find { |s| s['client'] == peer['client'] }
      history = following if following && following['id'].end_with?('_review_history')
      capture = history && history.fetch('capture', {}).find { |_, path| path == '/items/0/text' }
      check(history && following && following['id'] == history['id'] &&
        history.dig('rpc', 'request', 'limit') == 1 &&
        history.dig('rpc', 'request', 'order') == 'PEER_RUN_HISTORY_LIST_REQUEST_ORDER_DESC',
        "#{file}: review must read latest history before the next client interaction")
      check(peer.dig('peer_stream', 'wait_for_history') == true && history && history['client'] == peer['client'] &&
        history.dig('rpc', 'method') == 'server.run.workspace.history' && history.dig('expect', '/items/0/type', 'equals') == 'PEER_RUN_HISTORY_ENTRY_TYPE_AGENT',
        "#{file}: missing persisted assistant review capture")
      check(capture && review.dig('peer_stream', 'input').include?("${#{capture[0]}}") &&
        review.dig('peer_stream', 'input').include?(peer.dig('peer_stream', 'input').to_s), "#{file}: uncaptured quality reply")
    end
    safety = peers.select { |p| p.dig('peer_stream', 'input').to_s.include?('现实里') }
    check(safety.any? { |p| p.dig('peer_stream', 'input').include?('学他们') }, "#{file}: missing risky imitation case")
    check(safety.any? { |p| p.dig('peer_stream', 'input').include?('一个人') }, "#{file}: missing dangerous alone case")
    safety.each do |peer|
      check(peer.dig('expect', '/text', 'contains_any').to_a.include?('家长'), "#{file}: missing trusted-adult redirect")
    end
  end
  def self.normalize(value, implementation)
    case value
    when Hash
      value.to_h do |key, val|
        [normalize(key, implementation), normalize(val, implementation)]
      end
    when Array then value.map { |v| normalize(v, implementation) }
    when String
      # Only identifier namespaces, references and JSON pointer components; never
      # strip arbitrary engine words from prompts or assertion text.
      value.gsub(/(?<=\$\{)#{Regexp.escape(implementation)}(?=[_}])/, 'candidate')
           .gsub(/(?<=\/)#{Regexp.escape(implementation)}(?=[_\/]|$)/, 'candidate')
           .sub(/\A#{Regexp.escape(implementation)}(?=[_]|$)/, 'candidate')
    else value
    end
  end
  def self.owns?(step, implementation)
    client = step['client'] || step.dig('workspace_relay', 'second_client')
    return client == implementation || client.start_with?(implementation + '__') || client == "#{implementation}_tester" if client
    return false if implementation !~ /multi_role/ && step.fetch('id').include?('_multi_role')
    client == implementation || client == "#{implementation}_tester" ||
      step.fetch('id').start_with?(implementation + '_') ||
      step.fetch('id').match?(/\A(?:register|stop|delete)_#{Regexp.escape(implementation)}(?:_tester)?\z/) ||
      step.dig('output', 'variable').to_s.start_with?(implementation + '_')
  end
  def self.sequence(doc, implementation, section)
    steps(doc, section).select do |step|
      step.key?('speech') || owns?(step, implementation)
    end.map do |step|
      s = Marshal.load(Marshal.dump(step))
      if s.dig('rpc', 'method') == 'server.workspace.create'
        s.fetch('rpc').fetch('request').delete('workflow_name')
        s.fetch('rpc').fetch('request').delete('parameters')
      end
      s['client'] = implementation if s.key?('speech') # input fixture, independently generated in each file
      # finally uses both prefix and suffix naming in existing tier documents.
      s['id'] = s.fetch('id').sub(/\A(register|stop|delete)_#{Regexp.escape(implementation)}(?=_|$)/, '\\1_candidate')
      normalize(s, implementation)
    end
  end
  def self.probes(file, engine)
    steps(YAML.load_file(file)).select { |s| s['client'] == engine }.map do |s|
      s.merge('id' => s.fetch('id').delete_prefix(engine + '_'))
    end
  end
  def self.validate
    workflow_aliases = YAML.load_file('runtime-profiles/testing.yaml').dig('spec', 'workflows', 'collections').values.reduce({}, :merge)
    raids = (Dir['workflows/*/raid.json'].map { |f| File.basename(File.dirname(f)) } + AUDIO_ONLY).sort
    TIERS.each do |tier|
      tier_raids = tier == 'soak' ? raids - AUDIO_ONLY : raids
      expected = tier_raids.flat_map { |raid| inventory(raid).keys.map { |impl| "#{raid}.#{impl}" } }.sort
      files = Dir["tests/giztest/#{tier}/*.giztest.yaml"].sort
      check(files.map { |f| File.basename(f, '.giztest.yaml') } == expected, "#{tier}: raid inventory mismatch")
      files.each do |file|
        doc = YAML.load_file(file)
        check(File.readlines(file).first(4).map { |s| s.split[0,2].join(' ') } == ['# User', '# As', '# I', '# So'], "#{file}: missing User Story")
        check_matcher_types(doc, file)
        check_local_references(doc, file)
        check_speech_order(doc, file)
        check_workspace_order(doc, file)
        check_idle_gaps(doc, file)
        raid, suffix = File.basename(file, '.giztest.yaml').split('.', 2)
        declared_implementation = inventory(raid).fetch(suffix)
        check(doc['name'] == "#{raid}.#{tier}.#{suffix}", "#{file}: document name mismatch")
        capabilities = tts_capabilities(raid)
        target_id = YAML.load_file("workflows/#{raid}/#{suffix}.yaml").dig('metadata', 'id')
        tester_path = "workflows/#{raid}/test#{suffix.end_with?('.multi-role') ? '.multi-role' : ''}.yaml"
        tester_id = File.exist?(tester_path) ? YAML.load_file(tester_path).dig('metadata', 'id') : nil
        creates = steps(doc).select { |step| step.dig('rpc', 'method') == 'server.workspace.create' }
        creates.each do |step|
          expected_workflow = step['client'].end_with?('_tester') ? tester_id : target_id
          workflow_name = step.dig('rpc', 'request', 'workflow_name')
          resolved_workflow = workflow_aliases.fetch(workflow_name, {}).fetch('resource_id', workflow_name)
          check(expected_workflow && resolved_workflow == expected_workflow,
                "#{file}: #{step['id']} targets a foreign Workflow")
        end
        if raid == 'murder-mystery'
          check(inventory(raid).keys.sort == %w[flowcraft flowcraft.multi-role] && !JSON.generate(doc).include?('eino-murder-mystery'),
                "#{file}: murder-mystery must be Flowcraft only")
        end
        steps(doc).each do |step|
          implementation = step.fetch('client', '').split('__').first
          check_audio(step, capabilities[implementation], file) if capabilities.key?(implementation)
        end
        if suffix.end_with?('.multi-role')
          # Peer retirement owns partial-setup cleanup; expect_error requires an
          # error and cannot express success OR not-found for Workspace deletion.
          check(!steps(doc, 'finally').any? { |s| s.dig('rpc', 'method') == 'server.workspace.delete' },
                "#{file}: use ephemeral peer retirement for partial Workspace setup")
          doc.fetch('clients').each do |client, spec|
            check(spec['identity'] == 'ephemeral' && steps(doc, 'finally').any? { |s| s['client'] == client && s.dig('rpc', 'method') == 'server.peer.delete' },
                  "#{file}: missing ephemeral peer cleanup")
          end
        end
        if tier == 'smoke'
          steps(doc).each do |step|
            expect = step.fetch('expect', {})
            if step['id'].match?(/\A(?:flowcraft|eino).*_realtime_roundtrip\z/)
              roundtrip_expect = {
                '/events' => {'non_empty' => true}, '/text' => {'non_empty' => true},
                '/text_eos' => {'equals' => true}, '/audio_bytes' => {'minimum' => 1},
                '/audio_eos' => {'equals' => true},
                '/audio_integrity/streams' => {'minimum' => 1},
                '/audio_integrity/max_active' => {'equals' => 1},
                '/audio_integrity/open' => {'equals' => 0},
                '/audio_integrity/violations' => {'equals' => 0},
                '/audio_pacing/minimum_buffer_ms' => {'minimum' => 0},
                '/audio_pacing/underruns' => {'equals' => 0}
              }
              capability = capabilities[step.fetch('client').split('__').first]
              roundtrip_expect.delete_if { |key, _| key.match?(AUDIO_PATH) } if capability == false
              if step['client'].include?('multi_role') && File.basename(file).match?(/\A(?:story|adventure|figure)-/)
                roundtrip_expect['/text'] = {'min_length'=>1, 'not_contains'=>['【','】']}
                roundtrip_expect['/audio_integrity/streams'] = {'equals'=>1}
              end
              if step['client'].include?('multi_role') && raid == 'murder-mystery'
                roundtrip_expect['/text'] = {'min_length' => 1, 'not_contains' => ['【', '】']}
              end
              check(expect == roundtrip_expect, "#{file}: #{step['id']} must check complete realtime output without timing gates")
              first = steps(doc).find { |s| s['id'] == "#{step['id']}_first_response" }
              if raid.match?(/\A(?:story|adventure|figure|learn)-/)
                check(first && first.dig('peer_stream', 'completion') == 'first_response' &&
                      first.dig('peer_stream', 'first_text_timeout') == '2s' &&
                      first.dig('expect', '/first_text_ms') == {'maximum' => 2000} &&
                      (capability == false || (first.dig('peer_stream', 'first_audio_timeout') == '3s' &&
                       first.dig('expect', '/first_audio_ms') == {'maximum' => 3000})),
                      "#{file}: #{step['id']} needs capability-aware realtime latency gates")
              end
            end
            check(!expect.keys.any? { |p| p.end_with?('/audio_pacing/max_interval_ms') }, "#{file}: packet gaps must remain diagnostic evidence")
            next unless expect.keys.any? { |p| p.end_with?('/audio_pacing/underruns') }
            check(expect.dig('/audio_pacing/underruns', 'equals') == 0 && expect.dig('/audio_pacing/minimum_buffer_ms', 'minimum') == 0, "#{file}: missing device playback buffer gates")
          end
        elsif tier == 'quality'
          check_multi_role_review(doc, file) if suffix.end_with?('.multi-role')
          check_child_quality(doc, file) if suffix.end_with?('.multi-role') && raid.match?(/\A(?:story|adventure|figure)-/)
          check(doc['timeout'] == (File.basename(file).match?(/\A(?:story|adventure|figure)-/) ? '30m' : '10m'), "#{file}: quality budget must retain 30m for story/adventure, 10m otherwise")
          check(!steps(doc).any? { |s| s['workspace_relay'] }, "#{file}: long dialogue relay belongs in soak")
          check(!steps(doc).any? { |s| s.dig('peer_stream', 'completion') == 'first_response' }, "#{file}: first-response latency probes belong in smoke")
          check(suffix.end_with?('.multi-role') || !doc.fetch('clients').keys.any? { |c| c.end_with?('_tester') }, "#{file}: idle Tester client in quality")
        end
        clients = doc.fetch('clients').keys
        check(clients.all? { |c| c == declared_implementation || c.start_with?(declared_implementation + '__') || c == declared_implementation + '_tester' ||
          (AUDIO_ONLY.include?(raid) && c.start_with?(declared_implementation + '_')) || (raid == 'ast-translate' && tier == 'quality' && c == 'ast') }, "#{file}: foreign implementation client")
        %w[steps finally].each do |section|
          steps(doc, section).each do |step|
            check(AUDIO_ONLY.include?(raid) || step['speech'] || owns?(step, declared_implementation),
                  "#{file}: #{section}/#{step['id']} has no implementation owner")
            check(!step['id'].include?('keepalive') || step.dig('rpc', 'method') == 'server.run.status', "#{file}: invalid setup keepalive")
          end
        end
      end
      tier_raids.each do |raid|
        variants = inventory(raid)
        capabilities = tts_capabilities(raid)
        next if capabilities.empty?
        variants.each do |suffix, impl|
          next unless suffix.start_with?('eino')
          peer = suffix.sub(/\Aeino/, 'flowcraft')
          peer = 'flowcraft' if raid == 'journey-guide'
          next unless variants.key?(peer)
          compare_files("tests/giztest/#{tier}/#{raid}.#{peer}.giztest.yaml",
                        "tests/giztest/#{tier}/#{raid}.#{suffix}.giztest.yaml", variants[peer], impl, capabilities)
        end
      end
      puts "validated #{tier}: #{files.size} files and implementation parity"
    end
    realtime_count = 0
    Dir['workflows/*/raid.json'].each do |file|
      m = JSON.parse(File.read(file)); raid = m.fetch('id')
      expected = TIERS.flat_map { |t| inventory(raid).keys.map { |impl| "tests/giztest/#{t}/#{raid}.#{impl}.giztest.yaml" } }
      check(m.fetch('tests').map { |t| t.fetch('file') }.sort == expected.sort, "#{file}: tier registration mismatch")
      if raid.match?(/\A(?:story|adventure|figure|learn)-/)
        %w[flowcraft eino].each do |engine|
          smoke = YAML.load_file("tests/giztest/smoke/#{raid}.#{engine}.giztest.yaml")
          realtime_count += 1
          impl = m.fetch('implementations').fetch(engine)
          check(impl.fetch('input').include?('realtime'), "#{file}: #{engine} lacks realtime capability")
          probes = steps(smoke).select { |s| s['client'] == engine }
          create = probes.any? { |s| s.dig('rpc', 'method') == 'server.workspace.create' && JSON.generate(s.dig('rpc', 'request', 'parameters')).include?('WORKSPACE_INPUT_MODE_REALTIME') }
          check(create, "#{file}: #{engine} lacks realtime Workspace")
          full = probes.find { |s| s['id'] == "#{engine}_realtime_roundtrip" }
          first = probes.find { |s| s['id'] == "#{engine}_realtime_roundtrip_first_response" }
          capability = tts_capabilities(raid).fetch(engine)
          check(full && full.dig('peer_stream','mode') == 'realtime' && full.dig('peer_stream','require_audio') == capability && full.dig('expect','/text_eos','equals') && (!capability || full.dig('expect','/audio_eos','equals')), "#{file}: #{engine} lacks complete realtime response")
          check(first && first.dig('peer_stream','completion') == 'first_response' && first.dig('peer_stream','first_text_timeout') == '2s' && (!capability || first.dig('peer_stream','first_audio_timeout') == '3s'), "#{file}: #{engine} lacks realtime latency gates")
        end
        eino = YAML.load_file("workflows/#{raid}/eino.yaml").dig('spec','eino')
        check(eino.dig('voice_adapter','asr_model') == 'asr', "#{file}: missing Eino realtime ASR binding")
      end
      m.fetch('tests').each do |t|
        check(t['tier'] == t['file'].split('/')[2] && t['implementations'].size == 1 && m.fetch('implementations').key?(t['implementations'].first) &&
          t['file'] == "tests/giztest/#{t['tier']}/#{raid}.#{File.basename(m['implementations'][t['implementations'].first]['file'], '.yaml')}.giztest.yaml", "#{file}: implementation registration mismatch")
      end
    end
    check(realtime_count == 102, "expected 102 original story/adventure/figure/learn RealTime clients, found #{realtime_count}")
    puts "validated #{realtime_count} original RealTime clients with ASR and audio response gates"
    Dir['workflows/{story,adventure,figure}-*/{flowcraft,eino}.multi-role.yaml'].each do |file|
      source = File.read(file)
      check(source.include?('旁白叙述与角色第一人称台词分段'), "#{file}: missing continuous dialogue contract")
      check(!source.include?('每轮只由一人发声'), "#{file}: obsolete single-speaker contract")
    end
    %w[flowcraft eino].each do |engine|
      source = File.read("workflows/adventure-history/#{engine}.multi-role.yaml")
      check(source.include?('情境重现声明不替代角色自述'), "history #{engine}: reenactment boundary missing")
      check(!source.include?('正文第一句必须逐字'), "history #{engine}: rigid scene opening")
    end
    old = Dir['tests/giztest/*/*.giztest.yaml'].reject { |f| (TIERS + %w[device h106 reports]).include?(f.split('/')[2]) }
    check(old.empty?, "legacy Giztest files remain: #{old.join(', ')}")
  end
end
GiztestLayout.validate if $PROGRAM_NAME == __FILE__
