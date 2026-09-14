# Shared structural view of tiered Giztests. Preserve ordering and every assertion.
require 'yaml'
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
      [name.tr('-', '_'), %w[default_voice node_voices state_voices speaker_voices].any? { |key| voice[key] && !voice[key].empty? }]
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
  def self.check_workspace_order(doc, file)
    # Generated Workspace names must be created on that client before selection.
    created = []
    local_names = steps(doc).map do |step|
      [step['client'], step.dig('rpc', 'request', 'name')] if step.dig('rpc', 'method') == 'server.workspace.create'
    end.compact
    steps(doc).each do |step|
      method = step.dig('rpc', 'method')
      if method == 'server.workspace.create'
        created << [step['client'], step.dig('rpc', 'request', 'name')]
      elsif method == 'server.run.workspace.set'
        key = [step['client'], step.dig('rpc', 'request', 'workspace_name')]
        check(!local_names.include?(key) || created.include?(key),
              "#{file}: #{step['id']} selects a local Workspace before creation")
      end
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
      s['client'] = implementation if s.key?('speech') # shared input fixture, executed once
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
    raids = (Dir['workflows/*/raid.json'].map { |f| File.basename(File.dirname(f)) } + AUDIO_ONLY).sort
    TIERS.each do |tier|
      expected = tier == 'soak' ? raids - AUDIO_ONLY : raids
      files = Dir["tests/giztest/#{tier}/*.giztest.yaml"].sort
      check(files.map { |f| File.basename(f, '.giztest.yaml') } == expected, "#{tier}: raid inventory mismatch")
      files.each do |file|
        doc = YAML.load_file(file)
        check(File.readlines(file).first(4).map { |s| s.split[0,2].join(' ') } == ['# User', '# As', '# I', '# So'], "#{file}: missing User Story")
        check_workspace_order(doc, file)
        capabilities = tts_capabilities(File.basename(file, '.giztest.yaml'))
        steps(doc).each do |step|
          implementation = step.fetch('client', '').split('__').first
          check_audio(step, capabilities[implementation], file) if capabilities.key?(implementation)
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
              if File.basename(file).match?(/\A(?:story|adventure)-/)
                roundtrip_expect['/text'] = {'non_empty'=>true, 'not_contains'=>['【','】'], 'min_length'=>300, 'max_length'=>600}
                roundtrip_expect['/audio_integrity/streams'] = {'equals'=>1}
              end
              check(expect == roundtrip_expect, "#{file}: #{step['id']} must check complete realtime output without timing gates")
              first = steps(doc).find { |s| s['id'] == "#{step['id']}_first_response" }
              raid = File.basename(file, '.giztest.yaml')
              if raid.match?(/\A(?:story|adventure|learn)-/)
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
          check(doc['timeout'] == (File.basename(file).match?(/\A(?:story|adventure)-/) ? '30m' : '10m'), "#{file}: quality budget must be 10m")
          check(!steps(doc).any? { |s| s['workspace_relay'] }, "#{file}: long dialogue relay belongs in soak")
          check(!steps(doc).any? { |s| s.dig('peer_stream', 'completion') == 'first_response' }, "#{file}: first-response latency probes belong in smoke")
          check(!doc.fetch('clients').keys.any? { |c| c.end_with?('_tester') }, "#{file}: idle Tester client in quality")
          logical = doc['clients'].keys.map { |c| c.split('__').first }.uniq
          if logical.size > 1 && logical.all? { |c| c.match?(/\A(?:flowcraft|eino)/) }
            check(!doc.fetch('steps').any? { |s| s['peer_stream'] }, "#{file}: equivalent quality responses must run in parallel")
            doc.fetch('steps').select { |s| s['parallel'] }.each do |group|
              group['parallel'].group_by { |s| s['client'].split('__', 2).last }.each_value do |children|
                check(children.map { |s| s['client'].split('__').first }.sort == logical.sort, "#{file}: each active Workspace group must exercise every implementation")
              end
            end
          end
          if doc['clients'].keys.any? { |c| c.include?('__') }
            active = []
            doc['steps'].each do |step|
              active << step['client'] if step.dig('rpc', 'method') == 'server.run.status'
              next unless step['parallel'] || step['peer_stream']
              check(active.uniq.sort == doc['clients'].keys.sort, "#{file}: idle Workspace clients need a keepalive before each response group")
              active = []
            end
          end
        end
        clients = doc.fetch('clients').keys
        implementations = clients.grep(/\A(?:flowcraft|eino)(?:_|$)/).reject { |c| c.end_with?('_tester') }.map { |c| c.split('__').first }.uniq
        raid = File.basename(file, '.giztest.yaml')
        manifest_path = "workflows/#{raid}/raid.json"
        if File.exist?(manifest_path)
          manifest = JSON.parse(File.read(manifest_path))
          declared = manifest.fetch('implementations').keys.map { |i| i.tr('-', '_') }.sort
          check(implementations.sort == declared, "#{file}: missing or unexpected implementation clients")
        end
        baseline = implementations.first
        implementations.drop(1).each do |impl|
          vars = [baseline, impl].map do |i|
            normalize(doc.fetch('variables').select { |k, _| k.start_with?(i + '_') }, i)
          end
          check(vars[0] == vars[1], "#{file}: #{baseline}/#{impl} variable definitions differ")
        end
        %w[steps finally].each do |section|
          if implementations.size > 1
            steps(doc, section).each do |step|
              next if step.key?('speech') # one common fixture operation
              owners = implementations.select { |impl| owns?(step, impl) }
              check(owners.size == 1, "#{file}: #{section}/#{step['id']} has ambiguous or missing implementation ownership")
            end
          end
          implementations.combination(2).each do |baseline, impl|
            left, right = [baseline, impl].map { |i| sequence(doc, i, section) }
            if capabilities.fetch(baseline) != capabilities.fetch(impl)
              left, right = [left, right].map { |seq| without_audio(seq) }
            end
            index = (0...[left.size, right.size].max).find { |n| left[n] != right[n] }
            check(index.nil?, "#{file}: #{section} #{baseline}/#{impl} mismatch at #{index}: #{left[index].inspect if index} != #{right[index].inspect if index}")
          end
        end
        if file.end_with?('/murder-mystery.giztest.yaml')
          check(implementations == ['flowcraft'] && !JSON.generate(doc).include?('eino-murder-mystery'), "#{file}: murder-mystery must be Flowcraft only")
        end
      end
      puts "validated #{tier}: #{files.size} files and implementation parity"
    end
    Dir['workflows/*/raid.json'].each do |file|
      m = JSON.parse(File.read(file)); raid = m.fetch('id')
      expected = TIERS.map { |t| "tests/giztest/#{t}/#{raid}.giztest.yaml" }
      check(m.fetch('tests').map { |t| t.fetch('file') }.sort == expected.sort, "#{file}: tier registration mismatch")
      if raid.match?(/\A(?:story|adventure|learn)-/)
        smoke = YAML.load_file("tests/giztest/smoke/#{raid}.giztest.yaml")
        %w[flowcraft eino].each do |engine|
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
        check(t['tier'] == t['file'].split('/')[2] && t['implementations'].sort == m.fetch('implementations').keys.sort, "#{file}: implementation registration mismatch")
      end
    end
    Dir['workflows/{story,adventure}-*/{flowcraft,eino}.yaml'].each do |file|
      source = File.read(file)
      check(source.include?('旁白叙述与角色第一人称台词分段'), "#{file}: missing continuous dialogue contract")
      check(!source.include?('每轮只由一人发声') && !source.include?('state_voices:'), "#{file}: obsolete single-speaker contract")
    end
    %w[flowcraft eino].each do |engine|
      source = File.read("workflows/adventure-history/#{engine}.yaml")
      check(source.include?('情境重现声明不替代角色自述'), "history #{engine}: reenactment boundary missing")
      check(source.include?('正文第一句必须逐字是‘来到'), "history #{engine}: missing explicit scene opening")
    end
    old = Dir['tests/giztest/*/*.giztest.yaml'].reject { |f| (TIERS + %w[h106 reports]).include?(f.split('/')[2]) }
    check(old.empty?, "legacy Giztest files remain: #{old.join(', ')}")
  end
end
GiztestLayout.validate if $PROGRAM_NAME == __FILE__
