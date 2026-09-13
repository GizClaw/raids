# Shared structural view of tiered Giztests. Preserve ordering and every assertion.
require 'yaml'
require 'json'
module GiztestLayout
  TIERS = %w[smoke quality soak].freeze
  AUDIO_ONLY = %w[ast-translate doubao-realtime].freeze
  def self.check(ok, message)
    abort message unless ok
  end
  # Flatten parallel streams while retaining their parent timeout and assertions.
  def self.steps(doc, section = 'steps')
    doc.fetch(section, []).flat_map do |step|
      next [step] unless step['parallel']
      step.fetch('parallel').map do |child|
        copy = step.reject { |k, _| %w[id parallel expect capture].include?(k) }.merge(child)
        %w[expect capture].each do |key|
          prefix = "/#{child.fetch('id')}"
          entries = step.fetch(key, {}).select { |path, _| path.start_with?(prefix + '/') }
          copy[key] = entries.to_h { |path, value| [path.delete_prefix(prefix), value] } unless entries.empty?
        end
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
        clients = doc.fetch('clients').keys
        implementations = clients.grep(/\A(?:flowcraft|eino)(?:_|$)/).reject { |c| c.end_with?('_tester') }
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
          implementations.drop(1).each do |impl|
            left, right = [baseline, impl].map { |i| sequence(doc, i, section) }
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
          check(full && full.dig('peer_stream','mode') == 'realtime' && full.dig('peer_stream','require_audio') && full.dig('expect','/text_eos','equals') && full.dig('expect','/audio_eos','equals'), "#{file}: #{engine} lacks complete realtime response")
          check(first && first.dig('peer_stream','completion') == 'first_response' && first.dig('peer_stream','first_text_timeout') == '2s' && first.dig('peer_stream','first_audio_timeout') == '3s', "#{file}: #{engine} lacks realtime latency gates")
        end
        eino = YAML.load_file("workflows/#{raid}/eino.yaml").dig('spec','eino')
        check(eino.dig('voice_adapter','asr_model') == 'asr', "#{file}: missing Eino realtime ASR binding")
      end
      m.fetch('tests').each do |t|
        check(t['tier'] == t['file'].split('/')[2] && t['implementations'].sort == m.fetch('implementations').keys.sort, "#{file}: implementation registration mismatch")
      end
    end
    old = Dir['tests/giztest/*/*.giztest.yaml'].reject { |f| (TIERS + %w[h106 reports]).include?(f.split('/')[2]) }
    check(old.empty?, "legacy Giztest files remain: #{old.join(', ')}")
  end
end
GiztestLayout.validate if $PROGRAM_NAME == __FILE__
