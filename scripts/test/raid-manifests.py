"""Checks every raid.json age rating and keeps raids.txt in step with them.

Every workflows/ package has a raid.json. rating.age lists each life stage a
raid suits, in STAGES order; raids.txt is the table of contents, one raid ID per line.

  python3 scripts/test/raid-manifests.py          # rewrite raids.txt
  python3 scripts/test/raid-manifests.py --check  # fail on a bad rating or a stale raids.txt
"""
import glob
import json
import os
import sys

TOC = 'raids.txt'
SCHEME = 'raids-age-v2'
# preschool 3-5, child 6-11, teen 12-17, adult 18-59, senior 60+.
STAGES = ['preschool', 'child', 'teen', 'adult', 'senior']


def manifests():
    return {os.path.basename(os.path.dirname(f)): f for f in sorted(glob.glob('workflows/*/raid.json'))}


def errors(raid, path):
    with open(path, encoding='utf-8') as f:
        manifest = json.load(f)
    rating = manifest.get('rating') or {}
    age = rating.get('age')
    found = []
    if manifest.get('id') != raid:
        found.append(f'{path}: id {json.dumps(manifest.get("id"))} does not match its directory')
    if rating.get('scheme') != SCHEME:
        found.append(f'{path}: rating.scheme must be {SCHEME}')
    if not isinstance(age, list) or not age or any(stage not in STAGES for stage in age):
        found.append(f'{path}: rating.age must list stages from {", ".join(STAGES)}')
    elif age != sorted(set(age), key=STAGES.index):
        found.append(f'{path}: rating.age must list each stage once, youngest first')
    return found


def run(check):
    found = manifests()
    toc = ''.join(f'{raid}\n' for raid in found)
    if not check:
        with open(TOC, 'w', encoding='utf-8') as f:
            f.write(toc)
        print(f'wrote {TOC} with {len(found)} raids')
        return
    problems = [f'workflows/{raid}: missing raid.json' for raid in sorted(os.listdir('workflows'))
                if os.path.isdir(f'workflows/{raid}') and raid not in found]
    problems += [e for raid, path in found.items() for e in errors(raid, path)]
    if not os.path.exists(TOC) or open(TOC, encoding='utf-8').read() != toc:
        problems.append(f'stale {TOC} (run python3 scripts/test/raid-manifests.py)')
    if problems:
        sys.exit('\n'.join(problems))
    print(f'validated {len(found)} raid age ratings and {TOC}')


if __name__ == '__main__':
    run('--check' in sys.argv[1:])
