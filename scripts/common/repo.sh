# Shared helpers for the Make target scripts. Source this file; do not run it.

# repo_root prints the repository root, resolved from the calling script's own
# location so a target works from any working directory.
repo_root() {
	CDPATH='' cd -- "$(dirname -- "$0")/../.." && pwd
}

# require_command exits when a required executable is missing.
require_command() {
	command -v "$1" >/dev/null 2>&1 || {
		printf 'missing required command: %s\n' "$1" >&2
		exit 1
	}
}

# require_python_yaml exits when python3 cannot import PyYAML, the only
# third-party module the repository scripts use.
require_python_yaml() {
	require_command python3
	python3 -c 'import yaml' 2>/dev/null || {
		printf 'missing Python module yaml: python3 -m pip install -r scripts/requirements.txt\n' >&2
		exit 1
	}
}

# go_modules prints every Go module directory under tools/.
go_modules() {
	root="$1"
	for manifest in "$root"/tools/*/go.mod; do
		test -f "$manifest" || continue
		dirname -- "$manifest"
	done
}
