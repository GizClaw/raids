import glob
import json

import yaml


def load_yaml(path):
    with open(path, encoding='utf-8') as f:
        return yaml.safe_load(f)


# Walk all workflow documents, including nested graphs and every Tester variant.
scripts = []


def walk(value, file, path):
    if isinstance(value, dict):
        if value.get('type') == 'script' and value.get('language') == 'starlark':
            scripts.append({'file': file, 'path': path, 'source': value['source'], 'entrypoint': value.get('entrypoint')})
        for key, child in value.items():
            walk(child, file, f'{path}/{key}')
    elif isinstance(value, list):
        for i, child in enumerate(value):
            walk(child, file, f'{path}/{i}')


for file in sorted(glob.glob('workflows/**/*.yaml', recursive=True)):
    walk(load_yaml(file), file, '')
print(json.dumps(scripts, ensure_ascii=False, separators=(',', ':')))
