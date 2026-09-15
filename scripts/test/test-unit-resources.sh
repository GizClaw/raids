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
ruby scripts/test/starlark-modules.rb | scripts/test/test-starlark-routing.sh --modules
python3 scripts/test/test-multi-role-testers.py
ruby scripts/test/original-workflows.rb
ruby scripts/test/test-eino-script-outputs.rb
ruby scripts/test/eino-script-outputs.rb
ruby scripts/test/test-giztest-layout.rb
# Includes upstream RealTime inventory, ASR, complete-audio and 2s/3s
# first-response checks, mapped to original clients in smoke tier files.
ruby scripts/test/giztest-layout.rb

# Resolve the complete manifest -> branch -> published node -> alias -> Voice
# chain using parsed YAML, not aggregate text counts. Ruby uses only stdlib.
require_command ruby
ruby scripts/test/voice-bindings.rb

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
	for engine in eino flowcraft eino.multi-role flowcraft.multi-role; do
		grep -F '并紧接新章开场' "$package/$engine.yaml" >/dev/null || {
			printf 'story Workflow lacks chapter-opening continuation: %s/%s.yaml\n' "$package" "$engine" >&2
			exit 1
		}
		client="$(printf %s "$engine" | tr .- __)"
		test_file="tests/giztest/quality/$raid.$engine.giztest.yaml"
		test -f "$test_file" || {
			printf 'missing story transition Giztest: %s\n' "$test_file" >&2
			exit 1
		}
		for step in opening_with_guidance choice_prompts_next_chapter enter_next_chapter_with_story; do
			grep -F "id: ${client}_transitions_$step" "$test_file" >/dev/null || {
				printf 'story transition Giztest lacks %s: %s\n' "$step" "$test_file" >&2
				exit 1
			}
		done
        ruby -ryaml -e '
          require File.expand_path("scripts/test/giztest-layout.rb")
          step = GiztestLayout.steps(YAML.load_file(ARGV[0])).find { |s| s["id"] == "#{ARGV[1]}_transitions_enter_next_chapter_with_story" }
          pattern = step && step.dig("expect", "/text", "pattern")
          abort "#{ARGV[0]}: #{ARGV[1]} missing chapter-opening continuation assertion" unless pattern && (ARGV[1].include?("multi_role") ? pattern.include?("[？?]") : pattern.include?("第 2 章[：:]") && pattern.include?("{20,}"))
        ' "$test_file" "$client"

		grep -F "\"file\": \"$test_file\"" "$package/raid.json" >/dev/null || {
			printf 'raid manifest lacks story transition Giztest: %s\n' "$test_file" >&2
			exit 1
		}
		transition_count=$((transition_count + 1))
	done
done
printf 'validated %s story transition Giztests\n' "$transition_count"

"$GIZCLAW_TEST_CLI" test validate -f tests/giztest
