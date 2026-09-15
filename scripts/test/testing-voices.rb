# Testing uses Volcengine TTS 2.0 for concurrency; inspect every resolved alias,
# including YAML anchors and resources not referenced by a workflow manifest.
require_relative 'yaml_compat'

def check_testing_voices(profile)
  voices = profile.fetch('resources').fetch('voices')
  abort 'testing: no Voice bindings' if voices.empty?
  voices.each do |name, binding|
    id = binding.fetch('resource_id')
    unless id.match?(/\Avolc-tenant:volc-cn-beijing:[A-Za-z0-9_-]+_uranus_bigtts\z/)
      abort "testing: #{name} must bind a Volcengine TTS 2.0 (*_uranus_bigtts) Voice, got #{id}"
    end
  end
  puts "validated #{voices.size} testing Voice bindings use Volcengine TTS 2.0"
end

if $PROGRAM_NAME == __FILE__
  check_testing_voices(YAML.load_file('runtime-profiles/testing.yaml').fetch('spec'))
end
