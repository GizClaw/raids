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

resource_dirs='credentials tenants models voices memory-layouts petdefs workflows runtime-profiles registration-tokens'

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
	"$GIZCLAW" admin validate -f "$file"
done

test -d tests/giztest || {
	printf 'missing Giztest corpus: tests/giztest\n' >&2
	exit 1
}

# Every ordinary story/adventure package has one paced-audio RealTime document
# for each supported engine. Keep this inventory structural rather than a bare
# count so a future package cannot replace or hide another package's coverage.
realtime_count=0
for package in workflows/adventure-* workflows/story-*; do
	test -d "$package" || continue
	raid="${package#workflows/}"
	for engine in eino flowcraft; do
		test_file="tests/giztest/$raid/$engine.realtime.giztest.yaml"
		test -f "$test_file" || {
			printf 'missing RealTime Giztest: %s\n' "$test_file" >&2
			exit 1
		}
		grep -F 'input: WORKSPACE_INPUT_MODE_REALTIME' "$test_file" >/dev/null || {
			printf 'RealTime Giztest lacks realtime Workspace input: %s\n' "$test_file" >&2
			exit 1
		}
		grep -F 'mode: realtime' "$test_file" >/dev/null || {
			printf 'RealTime Giztest lacks paced realtime stream: %s\n' "$test_file" >&2
			exit 1
		}
		grep -F "\"file\": \"$test_file\"" "$package/raid.json" >/dev/null || {
			printf 'raid manifest lacks RealTime Giztest: %s\n' "$test_file" >&2
			exit 1
		}
		realtime_count=$((realtime_count + 1))
	done
	for engine in eino flowcraft; do
		jq -e --arg engine "$engine" \
			'.implementations[$engine].input | index("realtime") != null' \
			"$package/raid.json" >/dev/null || {
			printf 'raid manifest lacks %s realtime input capability: %s/raid.json\n' \
				"$engine" "$package" >&2
			exit 1
		}
	done
	grep -F 'voice_adapter:' "$package/eino.yaml" >/dev/null || {
		printf 'Eino Workflow lacks realtime voice adapter: %s/eino.yaml\n' "$package" >&2
		exit 1
	}
	grep -F 'asr_model: asr' "$package/eino.yaml" >/dev/null || {
		printf 'Eino Workflow lacks realtime ASR binding: %s/eino.yaml\n' "$package" >&2
		exit 1
	}
	eino_realtime="tests/giztest/$raid/eino.realtime.giztest.yaml"
	grep -F 'completion: first_response' "$eino_realtime" >/dev/null || {
		printf 'Eino RealTime Giztest lacks first-response probe: %s\n' "$raid" >&2
		exit 1
	}
	grep -F 'first_text_timeout: 2s' "$eino_realtime" >/dev/null || {
		printf 'Eino RealTime Giztest lacks 2 s text gate: %s\n' "$raid" >&2
		exit 1
	}
	grep -F 'require_audio: false' "$eino_realtime" >/dev/null || {
		printf 'Eino RealTime Giztest lacks text-only response contract: %s\n' "$raid" >&2
		exit 1
	}
	if grep -F 'first_audio_timeout:' "$eino_realtime" >/dev/null; then
		printf 'Eino RealTime Giztest must not claim an audio latency gate: %s\n' "$raid" >&2
		exit 1
	fi
	grep -F 'first_text_timeout: 2s' "tests/giztest/$raid/flowcraft.realtime.giztest.yaml" >/dev/null || {
		printf 'Flowcraft RealTime Giztest lacks 2 s text gate: %s\n' "$raid" >&2
		exit 1
	}
	grep -F 'first_audio_timeout: 3s' "tests/giztest/$raid/flowcraft.realtime.giztest.yaml" >/dev/null || {
		printf 'Flowcraft RealTime Giztest lacks 3 s audio gate: %s\n' "$raid" >&2
		exit 1
	}
done
test "$realtime_count" -eq 60 || {
	printf 'expected 60 story/adventure RealTime Giztests, found %s\n' "$realtime_count" >&2
	exit 1
}
printf 'validated %s story/adventure RealTime Giztests\n' "$realtime_count"

"$GIZCLAW_TEST_CLI" test validate -f tests/giztest
