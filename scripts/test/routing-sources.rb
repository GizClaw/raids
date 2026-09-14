# Parse YAML structurally; emit sources and per-raid fixtures for the offline runner.
require 'yaml'
require 'json'
suites = []
Dir['workflows/*'].select { |p| File.directory?(p) }.sort.each do |package|
  manifest_file = "#{package}/raid.json"
  manifest = File.exist?(manifest_file) ? JSON.parse(File.read(manifest_file)) : {}
  ['', '.multi-role'].each do |variant|
    next if variant != '' && !File.exist?("#{package}/flowcraft#{variant}.yaml")
    flow_file, eino_file = %w[flowcraft eino].map { |e| "#{package}/#{e}#{variant}.yaml" }
    flow = File.exist?(flow_file) ? YAML.load_file(flow_file).dig('spec', 'flowcraft') : nil
    eino = File.exist?(eino_file) ? YAML.load_file(eino_file).dig('spec', 'eino') : nil
    expanded = (manifest['implementations'] || {}).values.any? { |i| (i.dig('parameters', 'voices') || {}).size > 3 }
    expanded ||= (flow&.dig('voice_adapter', 'speaker_voices') || {}).size > 3
    expanded ||= (eino&.dig('voice_adapter', 'speaker_voices') || {}).size > 3
    fixture = "#{package}/routing-cases.json"
    abort "#{package}: multi-voice raid requires routing-cases.json" if expanded && !File.exist?(fixture)
    next unless File.exist?(fixture)
    data = JSON.parse(File.read(fixture))
    abort "#{fixture}: unsupported version or empty cases" unless data['version'] == 1 && data['cases'].is_a?(Array) && !data['cases'].empty?
    if variant.empty?
      nodes = flow.fetch('graph').fetch('nodes')
      if nodes.any? { |n| n['id'] == 'control-story' }
        data = {'version'=>1, 'flowcraft'=>{'node'=>'control-story'}, 'cases'=>[
          {'id'=>'original-opening', 'input'=>'请从第一章开始', 'expect'=>{'speaker'=>'narrator', 'flowcraft'=>{'story_state.chapter'=>{'equals'=>1}}}},
          {'id'=>'original-chapter-gate', 'input'=>'进入第二章', 'expect'=>{'speaker'=>'narrator', 'flowcraft'=>{'transition_blocked'=>{'equals'=>true}, 'story_state.chapter'=>{'equals'=>1}}}},
          {'id'=>'original-choice', 'input'=>'我选择帮助朋友', 'expect'=>{'flowcraft'=>{'story_state.chapter_choice_made'=>{'equals'=>true}}}},
          {'id'=>'original-ready-transition', 'input'=>'进入下一章', 'state'=>{'chapter'=>1,'chapter_choice_made'=>true,'chapter_progress_beats'=>['outcome','perspective']}, 'expect'=>{'speaker'=>'narrator','flowcraft'=>{'story_state.chapter'=>{'equals'=>2}}}}
        ]}
      elsif nodes.any? { |n| n['id'] == 'route-phase' }
        data = {'version'=>1, 'flowcraft'=>{'node'=>'route-phase','state_var'=>'scenario_state'}, 'cases'=>[
          {'id'=>'original-opening', 'input'=>'', 'expect'=>{'flowcraft'=>{'scenario_phase'=>{'equals'=>'opening'}}}},
          {'id'=>'original-correction', 'input'=>'更正，只确认新事实', 'expect'=>{'flowcraft'=>{'scenario_phase'=>{'equals'=>'correction'}}}}
        ]}
      elsif !nodes.any? { |n| n['id'] == data.fetch('flowcraft').fetch('node') }
        # These originals have no character selector; their published node Voice
        # routes are covered by voice-bindings.rb, and live contracts by tier tests.
        next
      end
    end
    sources = {}
    {'flowcraft'=>flow, 'eino'=>eino}.each do |engine, spec|
      next unless manifest.fetch('implementations').key?(engine) && data.key?(engine)
      id = data.fetch(engine).fetch('node', engine == 'flowcraft' ? 'control-story' : 'select-speaker')
      node = spec&.dig('graph', 'nodes')&.find { |n| n['id'] == id }
      next if !node && variant.empty? && engine == 'eino' # Original single-voice Eino has no role-routing script.
      abort "#{fixture}: missing #{engine} node #{id}" unless node
      sources[engine] = engine == 'flowcraft' ? node.fetch('config').fetch('source') : node.fetch('source')
    end
    suites << {raid: package + variant, data: data, sources: sources}
  end
end
puts JSON.generate(suites)
