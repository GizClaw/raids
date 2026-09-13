#!/bin/sh
set -eu

# Offline schema validation of every declarative file: applyable Admin Resources
# through `gizclaw admin validate`, and the Giztest corpus through
# `gizclaw test validate`. It never uses a GizClaw context, contacts a Server,
# or reads a real credential: each empty .env.example variable is exported with
# a fixed non-secret placeholder so Credential and Tenant manifests resolve.
. "$(dirname -- "$0")/../common/repo.sh"
root="$(repo_root)"
: "${GIZCLAW:=gizclaw}"
: "${GIZCLAW_TEST_CLI:=$GIZCLAW}"

resource_dirs='credentials tenants models voices memory-layouts workflows runtime-profiles registration-tokens'

require_command "$GIZCLAW"
require_command "$GIZCLAW_TEST_CLI"
require_command jq
cd "$root"

for dir in $resource_dirs; do
	test -d "$dir" || {
		printf 'missing Resource directory: %s\n' "$dir" >&2
		exit 1
	}
done
test -f .env.example || {
	printf 'missing validation environment template: .env.example\n' >&2
	exit 1
}

while IFS= read -r line; do
	case "$line" in '' | '#'*) continue ;; *=*) ;; *)
		printf 'invalid .env.example entry\n' >&2
		exit 1
		;;
	esac
	name="${line%%=*}"
	value="${line#*=}"
	case "$name" in '' | *[!A-Z0-9_]*)
		printf 'invalid .env.example variable: %s\n' "$name" >&2
		exit 1
		;;
	esac
	test -z "$value" || {
		printf 'non-empty .env.example value: %s\n' "$name" >&2
		exit 1
	}
	export "$name=raids-static-validation"
done <.env.example

files="$(find $resource_dirs -type f -name '*.yaml' -print | LC_ALL=C sort)"
test -n "$files" || {
	printf 'no applyable Resource files found\n' >&2
	exit 1
}
printf '%s\n' "$files" | while IFS= read -r file; do
	printf 'validate %s\n' "$file"
	"$GIZCLAW" admin validate -f "$file" </dev/null
done

test -d tests/giztest || {
	printf 'missing Giztest corpus: tests/giztest\n' >&2
	exit 1
}

require_command ruby
ruby scripts/test/giztest-layout.rb

# Resolve the complete manifest -> branch -> published node -> alias -> Voice
# chain using parsed YAML, not aggregate text counts. Ruby uses only stdlib.
require_command ruby
ruby <<'RUBY'
require 'yaml'
require 'json'
require File.expand_path('scripts/test/giztest-layout', Dir.pwd)
def check(ok, message)
  abort message unless ok
end
profiles = %w[default testing].to_h do |name|
  [name, YAML.load_file("runtime-profiles/#{name}.yaml").fetch('spec').fetch('resources').fetch('voices')]
end
voice_files = Dir['voices/**/*.yaml'].to_h do |file|
  [YAML.load_file(file).fetch('metadata').fetch('id'), file]
end
packages = Dir['workflows/story-*'].select { |p| File.directory?(p) }
packages.each do |package|
  manifest = JSON.parse(File.read("#{package}/raid.json"))
  impl = manifest.fetch('implementations').fetch('flowcraft')
  slots = impl.fetch('parameters').fetch('voices')
  test_file = "tests/giztest/smoke/#{manifest.fetch('id')}.giztest.yaml"
  probes = GiztestLayout.probes(test_file, 'flowcraft')
  workflow = YAML.load_file("#{package}/#{impl.fetch('file')}")
  flow = workflow.fetch('spec').fetch('flowcraft')
  graph = flow.fetch('graph')
  nodes = graph.fetch('nodes').to_h { |n| [n.fetch('id'), n] }
  edges = graph.fetch('edges')
  bindings = flow.fetch('voice_adapter').fetch('node_voices')
  check(bindings.values.sort == slots.keys.sort, "#{package}: node Voice aliases differ from manifest")
  check(nodes.values.select { |n| n['publish'] == true }.map { |n| n['id'] }.sort == bindings.keys.sort, "#{package}: every published output needs a Voice")
  routing_file = "#{package}/routing-cases.json"
  routing = File.exist?(routing_file) ? JSON.parse(File.read(routing_file)).fetch('flowcraft') : {}
  control = routing.fetch('node', 'control-story')
  branches = edges.select { |e| e['from'] == control }
  check(branches.last == {'from'=>control, 'to'=>'speak-narrator'}, "#{package}: narrator must be the last fallback")
  roles = slots.values.map { |slot| slot.fetch('role') == 'storyteller' ? 'narrator' : slot.fetch('role') }
  check(roles.uniq.size == roles.size, "#{package}: duplicate role keys")
  source = nodes.fetch(control).fetch('config').fetch('source')
  table_json = source[/const roleTable = (\[.*\]);/, 1]
  if table_json
    table = JSON.parse(table_json)
    check(table.map { |r| r.fetch('key') }.sort == roles.sort, "#{package}: role table differs from manifest")
    table.each do |role|
      check(!role.fetch('aliases').empty? && !role.fetch('chapters').empty?, "#{package}: missing aliases or chapter eligibility")
    end
  end
  check(branches.size == roles.size, "#{package}: unexpected speaker branches")
  check(flow.fetch('voice_adapter').fetch('default_voice') == bindings.fetch('speak-narrator'), "#{package}: wrong narrator default Voice")
  check(probes.select { |p| p['peer_stream'] && p['id'].start_with?('probe_') && !p['id'].end_with?('_first_response') }.size == roles.size, "#{package}: role probe count mismatch")
  slots.each do |name, slot|
    role = slot.fetch('role') == 'storyteller' ? 'narrator' : slot.fetch('role')
    id = "speak-#{role}"
    node = nodes.fetch(id)
    check(bindings[id] == name, "#{package}/#{role}: wrong alias")
    check(node['type'] == 'llm' && node['publish'] == true && node.dig('config', 'output_key') == 'answer', "#{package}/#{role}: invalid output node")
    check(impl.fetch('parameters').fetch('models').key?(node.dig('config', 'model')), "#{package}/#{role}: unknown model alias")
    check(edges.include?({'from'=>id, 'to'=>'persist-story'}), "#{package}/#{role}: missing persistence edge")
    expected = {'from'=>control, 'to'=>id}
    expected['condition'] = "selected_speaker == \"#{role}\"" unless role == 'narrator'
    check(branches.count(expected) == 1, "#{package}/#{role}: missing or duplicated role branch")
    prompt = node.fetch('config').fetch('system_prompt')
    check(prompt.include?('等说话人标签'), "#{package}/#{role}: missing speaker label guard")
    probe = probes.find { |p| p['id'] == "probe_#{role}" }
    check(!probe.nil?, "#{package}/#{role}: missing full role probe")
    labels = probe.dig('expect', '/text', 'not_contains') || []
    spoken = labels.find { |label| label.end_with?('说') }
    check(spoken && labels.include?(spoken.delete_suffix('说') + '：') && prompt.include?(spoken), "#{package}/#{role}: mismatched speaker label assertions")
    check(probe.dig('peer_stream','require_audio') == true && probe.dig('expect','/audio_eos','equals') == true && probe.dig('expect','/text_eos','equals') == true && probe.dig('expect','/audio_bytes','minimum').to_i >= 1, "#{package}/#{role}: missing complete audio/text checks")
    first = probes.find { |p| p['id'] == "probe_#{role}_first_response" }
    check(first && first.dig('peer_stream','completion') == 'first_response' && first.dig('peer_stream','first_text_timeout') == '2s' && first.dig('peer_stream','first_audio_timeout') == '3s', "#{package}/#{role}: missing first response gates")
  end
  profiles.each do |profile_name, profile|
    ids = slots.keys.map { |name| profile.fetch(name).fetch('resource_id') }
    check(ids.uniq.size == ids.size, "#{package}/#{profile_name}: duplicate Voice resource IDs")
    ids.each { |id| check(voice_files.key?(id), "#{package}/#{profile_name}: Voice file missing for #{id}") }
  end
end
# Non-story packages may use different graph/node names. Validate their declared
# published-node -> alias -> manifest -> profiles -> Voice closure structurally.
Dir['workflows/*/routing-cases.json'].sort.each do |fixture|
  package = File.dirname(fixture)
  manifest = JSON.parse(File.read("#{package}/raid.json"))
  impl = manifest.fetch('implementations').fetch('flowcraft')
  slots = impl.fetch('parameters').fetch('voices')
  flow = YAML.load_file("#{package}/flowcraft.yaml").dig('spec', 'flowcraft')
  nodes = flow.fetch('graph').fetch('nodes')
  adapter = flow.fetch('voice_adapter')
  bindings = adapter.fetch('node_voices')
  check(bindings.values.uniq.sort == slots.keys.sort, "#{package}: node Voice aliases differ from manifest")
  check(nodes.select { |n| n['publish'] == true }.map { |n| n['id'] }.sort == bindings.keys.sort, "#{package}: every published output needs a Voice")
  check(bindings.values.include?(adapter.fetch('default_voice')), "#{package}: default Voice missing from slots")
  profiles.each do |name, profile|
    ids = slots.keys.map { |a| profile.fetch(a).fetch('resource_id') }
    check(ids.uniq.size == ids.size, "#{package}/#{name}: duplicate Voice resources")
    ids.each { |id| check(voice_files.key?(id), "#{package}/#{name}: missing Voice #{id}") }
  end
end
# Eino state-selected aliases must close over manifest and both profiles too.
Dir['workflows/**/eino.yaml'].each do |file|
  eino = YAML.load_file(file).dig('spec', 'eino')
  adapter = eino.fetch('voice_adapter', {})
  selector = adapter['state_voices']
  next unless selector
  manifest = JSON.parse(File.read(File.join(File.dirname(file), 'raid.json')))
  impl = manifest.fetch('implementations').fetch('eino')
  slots = impl.fetch('parameters').fetch('voices')
  aliases = selector.fetch('voices').values
  check(aliases.sort == slots.keys.sort, "#{file}: state Voice aliases differ from manifest")
  check(aliases.include?(adapter.fetch('default_voice')), "#{file}: default Voice missing from slots")
  fields = eino.fetch('graph').fetch('state').fetch('fields')
  check(fields.any? { |f| f['name'] == selector['field'] && f['type'] == 'string' }, "#{file}: selector must reference string State")
  profiles.each do |name, profile|
    ids = aliases.map { |a| profile.fetch(a).fetch('resource_id') }
    check(ids.uniq.size == ids.size, "#{file}/#{name}: duplicate Voice resources")
    ids.each { |id| check(voice_files.key?(id), "#{file}/#{name}: missing Voice #{id}") }
    flow_slots = manifest.fetch('implementations').fetch('flowcraft').fetch('parameters').fetch('voices')
    slots.each do |a, slot|
      counterpart = flow_slots.find { |_, other| other.fetch('role') == slot.fetch('role') }
      check(counterpart && profile.fetch(a)['resource_id'] == profile.fetch(counterpart.first)['resource_id'], "#{file}/#{name}: role Voice differs from Flowcraft")
    end
  end
  steps = GiztestLayout.probes("tests/giztest/smoke/#{manifest.fetch('id')}.giztest.yaml", 'eino')
  selector.fetch('voices').each_key do |role|
    full = steps.find { |p| p['id'] == "probe_#{role}" }
    check(full && full.dig('peer_stream', 'require_audio') && full.dig('expect', '/audio_bytes', 'minimum').to_i > 0 && full.dig('expect', '/text_eos', 'equals') && full.dig('expect', '/audio_eos', 'equals'), "#{file}/#{role}: missing EOS/audio checks")
    first = steps.find { |p| p['id'] == "probe_#{role}_first_response" }
    check(first && first.dig('peer_stream', 'first_text_timeout') == '2s' && first.dig('peer_stream', 'first_audio_timeout') == '3s', "#{file}/#{role}: missing latency gates")
  end
end
puts "validated #{packages.size} multi-voice stories: dynamic role counts, probes and Voice binding closure"
RUBY

# Execute every declared routing suite against both real engine scripts.
require_command node
ruby scripts/test/routing-sources.rb | node scripts/test/test-routing.js

# A chapter heading spoken on its own leaves the child waiting in silence, so
# every story Workflow must continue into the new chapter's opening, and each
# implementation has a live contract that checks the guided opening, the
# "进入下一章" prompt, and story text after the chapter 2 heading.
transition_count=0
for package in workflows/story-*; do
	test -d "$package" || continue
	raid="${package#workflows/}"
	for engine in eino flowcraft; do
		grep -F '并紧接新章开场' "$package/$engine.yaml" >/dev/null || {
			printf 'story Workflow lacks chapter-opening continuation: %s/%s.yaml\n' "$package" "$engine" >&2
			exit 1
		}
		test_file="tests/giztest/quality/$raid.giztest.yaml"
		test -f "$test_file" || {
			printf 'missing story transition Giztest: %s\n' "$test_file" >&2
			exit 1
		}
		for step in opening_with_guidance choice_prompts_next_chapter enter_next_chapter_with_story; do
			grep -F "id: ${engine}_transitions_$step" "$test_file" >/dev/null || {
				printf 'story transition Giztest lacks %s: %s\n' "$step" "$test_file" >&2
				exit 1
			}
		done
        ruby -ryaml -e '
          require File.expand_path("scripts/test/giztest-layout.rb")
          step = GiztestLayout.steps(YAML.load_file(ARGV[0])).find { |s| s["id"] == "#{ARGV[1]}_transitions_enter_next_chapter_with_story" }
          pattern = step && step.dig("expect", "/text", "pattern")
          abort "#{ARGV[0]}: #{ARGV[1]} missing chapter-opening continuation assertion" unless pattern && pattern.include?("第 2 章[：:]") && pattern.include?("{20,}")
        ' "$test_file" "$engine"

		grep -F "\"file\": \"$test_file\"" "$package/raid.json" >/dev/null || {
			printf 'raid manifest lacks story transition Giztest: %s\n' "$test_file" >&2
			exit 1
		}
		transition_count=$((transition_count + 1))
	done
done
printf 'validated %s story transition Giztests\n' "$transition_count"

"$GIZCLAW_TEST_CLI" test validate -f tests/giztest
