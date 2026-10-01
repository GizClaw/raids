# GizClaw rejects a RuntimeProfile whose Workflow binding keys
# or app_config keys break runtimealias.Validate, but only when a Server
# normalizes it: `gizclaw admin validate` accepts the same file. Mirror the rule
# so a non-conforming alias fails offline instead of at `gizclaw admin apply`.
import glob
import json
import re
import sys

import yaml

# pkgs/gizclaw/runtimealias/alias.go in GizClaw v0.18.15.
PATTERN = re.compile(r'[a-z0-9]+(?:-[a-z0-9]+)*(?:\.[a-z0-9]+(?:-[a-z0-9]+)*)*')
MAX_BYTES = 63


def valid(alias_name):
    return isinstance(alias_name, str) and len(alias_name.encode('utf-8')) <= MAX_BYTES and PATTERN.fullmatch(alias_name) is not None


# Returns [path, alias] pairs for every alias the Server would reject.
def errors(spec):
    found = []

    def check(path, name):
        if not valid(name):
            found.append([path, name])

    for name, binding in (spec.get('workflows') or {}).items():
        check('workflows', name)
        if not isinstance(binding, dict) or not isinstance(binding.get('resource_id'), str):
            found.append(['workflows (expected a flat resource binding)', name])
    for kind, bindings in (spec.get('resources') or {}).items():
        for name in (bindings or {}).keys():
            check(f'resources.{kind}', name)
    for name in (spec.get('app_config') or {}).keys():
        check('app_config', name)
    return found


if __name__ == '__main__':
    files = sorted(glob.glob('runtime-profiles/*.yaml'))
    if not files:
        sys.exit('no RuntimeProfile files found')
    count = 0
    for file in files:
        with open(file, encoding='utf-8') as f:
            doc = yaml.safe_load(f)
        if doc.get('kind') != 'RuntimeProfile':
            continue

        found = errors(doc['spec'])
        if found:
            for path, name in found:
                label = 'nil' if name is None else json.dumps(name, ensure_ascii=False)
                print(f'{file}: {path}: {label} must be 1-{MAX_BYTES} bytes of dot-separated lowercase kebab-case segments', file=sys.stderr)
            sys.exit(1)
        count += 1
    print(f'validated RuntimeProfile aliases in {count} files')
