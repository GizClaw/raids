# Parse YAML structurally; emit sources and per-raid fixtures for the offline runner.
require 'yaml'
require 'json'
suites = []
Dir['workflows/*'].select { |p| File.directory?(p) }.sort.each do |package|
  manifest_file = "#{package}/raid.json"
  manifest = File.exist?(manifest_file) ? JSON.parse(File.read(manifest_file)) : {}
  flow_file, eino_file = %w[flowcraft eino].map { |e| "#{package}/#{e}.yaml" }
  flow = File.exist?(flow_file) ? YAML.load_file(flow_file).dig('spec', 'flowcraft') : nil
  eino = File.exist?(eino_file) ? YAML.load_file(eino_file).dig('spec', 'eino') : nil
  expanded = (manifest['implementations'] || {}).values.any? { |i| (i.dig('parameters', 'voices') || {}).size > 3 }
  expanded ||= (flow&.dig('voice_adapter', 'node_voices') || {}).size > 3
  expanded ||= !!eino&.dig('voice_adapter', 'state_voices')
  fixture = "#{package}/routing-cases.json"
  abort "#{package}: multi-voice raid requires routing-cases.json" if expanded && !File.exist?(fixture)
  next unless File.exist?(fixture)
  data = JSON.parse(File.read(fixture))
  abort "#{fixture}: unsupported version or empty cases" unless data['version'] == 1 && data['cases'].is_a?(Array) && !data['cases'].empty?
  sources = {}
  {'flowcraft'=>flow, 'eino'=>eino}.each do |engine, spec|
    id = data.fetch(engine).fetch('node', engine == 'flowcraft' ? 'control-story' : 'select-speaker')
    node = spec&.dig('graph', 'nodes')&.find { |n| n['id'] == id }
    abort "#{fixture}: missing #{engine} node #{id}" unless node
    sources[engine] = engine == 'flowcraft' ? node.fetch('config').fetch('source') : node.fetch('source')
  end
  suites << {raid: package, data: data, sources: sources}
end
puts JSON.generate(suites)
