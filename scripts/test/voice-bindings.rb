# Offline workflow -> manifest -> RuntimeProfile -> Voice closure for both variants.
require 'yaml'
require 'json'
require_relative 'giztest-layout'
require_relative 'testing-voices'
def check(ok, message); abort message unless ok; end
profiles = %w[default testing].to_h { |n| [n, YAML.load_file("runtime-profiles/#{n}.yaml").fetch('spec')] }
check_testing_voices(profiles.fetch('testing'))
voices = Dir['voices/**/*.yaml'].to_h { |f| [YAML.load_file(f).dig('metadata', 'id'), f] }
count = 0
Dir['workflows/*/raid.json'].sort.each do |file|
  manifest = JSON.parse(File.read(file)); raid = manifest.fetch('id')
  speaker_maps = {}
  manifest.fetch('implementations').each do |name, impl|
    workflow = "workflows/#{raid}/#{impl.fetch('file')}"
    doc = YAML.load_file(workflow); engine = impl.fetch('driver'); spec = doc.dig('spec', engine)
    adapter = spec.fetch('voice_adapter', {})
    bindings = adapter.fetch('speaker_voices', {}).merge(adapter.fetch('node_voices', {}))
    aliases = (bindings.values + [adapter['default_voice']]).compact.uniq
    adapter.fetch('node_voices', {}).each_key do |id|
      node = spec.fetch('graph').fetch('nodes').find { |n| n['id'] == id }
      check(node && (engine != 'flowcraft' || node['publish'] == true), "#{workflow}: Voice bound to missing/unpublished node #{id}")
    end
    slots = impl.dig('parameters', 'voices') || {}
    check(aliases.sort == slots.keys.sort, "#{workflow}: Voice aliases differ from manifest slots")
    profiles.each do |profile_name, profile|
      # Each published node / named speaker must have its own audible identity,
      # including original implementations, not just the multi-role variants.
      %w[speaker_voices node_voices].each do |map_name|
        ids = adapter.fetch(map_name, {}).values.map { |a| profile.dig('resources', 'voices', a, 'resource_id') }
        check(ids.uniq.size == ids.size, "#{workflow}: duplicate #{profile_name} #{map_name} Voice resources")
      end
      collections = profile.fetch('workflows').fetch('collections')
      check(collections.values.any? { |c| c.values.any? { |entry| entry['resource_id'] == doc.dig('metadata', 'id') } }, "#{workflow}: missing #{profile_name} collection entry")
      aliases.each do |a|
        id = profile.dig('resources', 'voices', a, 'resource_id')
        check(id && voices.key?(id), "#{workflow}: unresolved #{profile_name} Voice #{a}")
        check(!id.include?('mars'), "#{workflow}: retired mars Voice #{id}")
      end
      (impl.dig('parameters', 'models') || {}).each_key do |a|
        check(profile.dig('resources', 'models', a, 'resource_id'), "#{workflow}: unresolved model #{a}")
      end
    end
    next unless name.end_with?('-multi-role')
    check(doc.dig('metadata', 'id').end_with?('-multi-role'), "#{workflow}: missing variant ID")
    original_id = impl.fetch('workflow_id').delete_suffix('-multi-role')
    profiles.each_value do |p|
      ids = aliases.map { |a| p.dig('resources', 'voices', a, 'resource_id') }
      check(ids.uniq.size == ids.size, "#{workflow}: duplicate multi-role Voice resources")
      aliases.each { |a| check(p.dig('resources','voices',a) == p.dig('resources','voices',a.sub(original_id+'-mr', original_id)), "#{workflow}: changed Voice binding #{a}") }
    end
    if raid.match?(/\A(?:story|adventure)-/)
      speaker_maps[engine] = adapter.fetch('speaker_voices')
      check(adapter.fetch('speaker_voices').fetch('旁白') == adapter.fetch('default_voice'), "#{workflow}: narrator mismatch")
      nodes = spec.fetch('graph').fetch('nodes')
      outputs = nodes.select { |n| engine == 'flowcraft' ? n['publish'] == true : n['type'] == 'chat_model' }
      check(outputs.size == 1, "#{workflow}: expected one narration LLM")
      source = File.read(workflow)
      check(source.include?('200至900') && source.include?('不输出其它【】标记'), "#{workflow}: missing narration contract")
      adapter.fetch('speaker_voices').each_key { |speaker| check(source.include?("【#{speaker}】"), "#{workflow}: missing marker #{speaker}") }
      probe = GiztestLayout.probes("tests/giztest/smoke/#{raid}.#{File.basename(impl.fetch('file'), '.yaml')}.giztest.yaml", name.tr('-', '_')).find { |s| s['id'] == 'continuous_story' }
      check(probe && probe.dig('expect','/text','min_length') == 200 && probe.dig('expect','/text','max_length') == 900, "#{workflow}: missing length gates")
      check((['【','】','进入下一章','要不要继续','想继续听就说'] - probe.dig('expect','/text','not_contains')).empty? && probe.dig('expect','/audio_integrity/streams','equals') == 1 && probe.dig('expect','/audio_pacing/underruns','equals') == 0, "#{workflow}: missing playback/marker gates")
    end
    count += 1
  end
  if speaker_maps.size == 2
    check(speaker_maps['flowcraft'].keys == speaker_maps['eino'].keys, "#{raid}: engine speaker names differ")
    profiles.each_value do |p|
      speaker_maps['flowcraft'].each do |speaker, alias_name|
        check(p.dig('resources','voices',alias_name,'resource_id') == p.dig('resources','voices',speaker_maps['eino'].fetch(speaker),'resource_id'), "#{raid}: engine Voice mismatch for #{speaker}")
      end
    end
  end
end
puts "validated all workflow Voice bindings and #{count} multi-role implementations"
