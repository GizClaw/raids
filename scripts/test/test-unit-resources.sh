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
ruby scripts/test/test-giztest-layout.rb
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
packages = Dir['workflows/{story,adventure}-*'].select { |p| File.directory?(p) }
packages.each do |package|
  manifest = JSON.parse(File.read("#{package}/raid.json"))
  maps = {}
  %w[flowcraft eino].each do |engine|
    impl = manifest.fetch('implementations').fetch(engine)
    spec = YAML.load_file("#{package}/#{engine}.yaml").dig('spec', engine)
    adapter = spec.fetch('voice_adapter')
    bindings = adapter.fetch('speaker_voices')
    maps[engine] = bindings
    slots = impl.fetch('parameters').fetch('voices')
    check(bindings.values.sort == slots.keys.sort, "#{package}/#{engine}: speaker aliases differ from slots")
    check(bindings.fetch('旁白') == adapter.fetch('default_voice'), "#{package}/#{engine}: narrator default mismatch")
    check((adapter.keys - %w[asr_model default_voice speaker_voices]).empty?, "#{package}/#{engine}: obsolete selection adapter")
    nodes = spec.fetch('graph').fetch('nodes')
    outputs = nodes.select { |n| engine == 'flowcraft' ? n['publish'] == true : n['type'] == 'chat_model' }
    check(outputs.size == 1, "#{package}/#{engine}: expected one narration LLM")
    check(nodes.none? { |n| n['id'].start_with?('speak-') || n['id'] == 'select-speaker' }, "#{package}/#{engine}: obsolete speaker node")
    prompt = engine == 'flowcraft' ? outputs.first.dig('config','system_prompt') : nodes.find { |n| n['type'] == 'prompt' }.fetch('messages').select { |m| m['role'] == 'system' }.map { |m| m.fetch('template') }.join("\n")
    check(prompt.include?('300至600') && prompt.include?('不输出其它【】标记'), "#{package}/#{engine}: missing narration contract")
    bindings.each_key { |speaker| check(prompt.include?("【#{speaker}】"), "#{package}/#{engine}: missing configured marker #{speaker}") }
    profiles.each do |name, profile|
      ids = slots.keys.map { |a| profile.fetch(a).fetch('resource_id') }
      check(ids.uniq.size == ids.size, "#{package}/#{name}: duplicate role Voices")
      ids.each { |id| check(voice_files.key?(id), "#{package}/#{name}: missing Voice #{id}") }
    end
    steps = GiztestLayout.probes("tests/giztest/smoke/#{manifest.fetch('id')}.giztest.yaml", engine)
    full = steps.find { |p| p['id'] == 'continuous_story' }
    check(full && full.dig('expect','/text','min_length') == 300 && full.dig('expect','/text','max_length') == 600, "#{package}/#{engine}: missing continuous story length gates")
    check(full.dig('expect','/text','not_contains').include?('【') && full.dig('expect','/text','not_contains').include?('】'), "#{package}/#{engine}: missing marker stripping gates")
    check(full.dig('expect','/audio_integrity/streams','equals') == 1 && full.dig('expect','/audio_pacing/underruns','equals') == 0, "#{package}/#{engine}: missing serial playback gates")
  end
  check(maps['flowcraft'].keys == maps['eino'].keys, "#{package}: engine speaker names differ")
  profiles.each_value do |profile|
    maps['flowcraft'].each { |name, a| check(profile.fetch(a)['resource_id'] == profile.fetch(maps['eino'].fetch(name))['resource_id'], "#{package}/#{name}: engine Voice mismatch") }
  end
end
# Non-story packages may use different graph/node names. Validate their declared
# published-node -> alias -> manifest -> profiles -> Voice closure structurally.
Dir['workflows/*/routing-cases.json'].sort.each do |fixture|
  package = File.dirname(fixture)
  next if packages.include?(package)
  manifest = JSON.parse(File.read("#{package}/raid.json"))
  impl = manifest.fetch('implementations').fetch('flowcraft')
  slots = impl.fetch('parameters').fetch('voices')
  flow = YAML.load_file("#{package}/flowcraft.yaml").dig('spec', 'flowcraft')
  nodes = flow.fetch('graph').fetch('nodes')
  adapter = flow.fetch('voice_adapter')
  bindings = adapter.fetch('speaker_voices')
  check(bindings.values.uniq.sort == slots.keys.sort, "#{package}: speaker Voice aliases differ from manifest")
  outputs = nodes.select { |n| n['publish'] == true }
  check(outputs.size == bindings.size, "#{package}: every published role needs a Voice")
  bindings.each_key do |speaker|
    check(outputs.one? { |n| (n.dig('config', 'system_prompt') || n.dig('config', 'source') || '').include?("【#{speaker}】") }, "#{package}: missing unique published marker #{speaker}")
  end
  probes = GiztestLayout.probes("tests/giztest/smoke/#{manifest.fetch('id')}.giztest.yaml", 'flowcraft')
  probes.select { |p| p['peer_stream'] && p.dig('peer_stream', 'completion') != 'first_response' }.each do |probe|
    check(%w[【 】].all? { |marker| (probe.dig('expect', '/text', 'not_contains') || []).include?(marker) }, "#{package}: missing marker stripping gate")
    check(probe.dig('expect', '/audio_integrity/streams', 'minimum') == 1 && probe.dig('expect', '/audio_pacing/underruns', 'equals') == 0, "#{package}: missing playback gates")
  end
  check(bindings.values.include?(adapter.fetch('default_voice')), "#{package}: default Voice missing from slots")
  profiles.each do |name, profile|
    ids = slots.keys.map { |a| profile.fetch(a).fetch('resource_id') }
    check(ids.uniq.size == ids.size, "#{package}/#{name}: duplicate Voice resources")
    ids.each { |id| check(voice_files.key?(id), "#{package}/#{name}: missing Voice #{id}") }
  end
end
puts "validated #{packages.size} continuous narration raids: markers, single LLM, playback probes and Voice binding closure"
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
