import glob
import json
import re
import sys

import yaml

# A small lexical check, not a script evaluator. Inspect return {...} literals
# in every language, ignoring comments/string contents and nested value keys.
TOKEN = re.compile(r'''\s+|\#.*?$|//.*?$|/\*.*?\*/|""".*?"""|\'\'\'.*?\'\'\'|"(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*'|`(?:\\.|[^`\\])*`|[A-Za-z_$][\w$]*|.''',
                   re.ASCII | re.DOTALL | re.MULTILINE)
SPACE = re.compile(r'\s', re.ASCII)


def return_keys(source):
    tokens = [t for t in TOKEN.findall(source) if not SPACE.match(t) and not t.startswith(('#', '//', '/*'))]

    def at(i):
        return tokens[i] if i < len(tokens) else None

    keys = []
    for i in range(len(tokens)):
        if tokens[i] != 'return':
            continue
        j = i + 1
        while at(j) == '(':
            j += 1
        if at(j) != '{':
            continue
        stack = ['{']
        key_position = True
        j += 1
        while j < len(tokens) and stack:
            token = tokens[j]
            if len(stack) == 1 and key_position:
                if at(j + 1) == ':':
                    keys.append(token[1:-1] if token.startswith(('"', "'")) else token)
                key_position = False
            if token in ('{', '[', '('):
                stack.append(token)
            elif token in ('}', ']', ')'):
                stack.pop()
            elif token == ',' and len(stack) == 1:
                key_position = True
            j += 1
    return list(dict.fromkeys(keys))


def errors(document, file):
    found = []
    for node in document['spec']['eino']['graph']['nodes']:
        if node.get('type') != 'script':
            continue
        keys = return_keys(node['source'])
        declared = node.get('outputs', {}).keys()
        for key in keys:
            if key not in declared:
                language = node.get('language')
                found.append(f"{file}: {node['id']} ({'' if language is None else language}): undeclared returned output {json.dumps(key, ensure_ascii=False)}")
    return found


if __name__ == '__main__':
    files = sys.argv[1:] or sorted(glob.glob('workflows/*/eino*.yaml'))
    if not files:
        sys.exit('no Eino workflows found')
    found = []
    for file in files:
        with open(file, encoding='utf-8') as f:
            found += errors(yaml.safe_load(f), file)
    if found:
        sys.exit('\n'.join(found))
    multi_role = sum(1 for file in files if file.endswith('.multi-role.yaml'))
    print(f'validated script return outputs in {len(files)} Eino workflows ({len(files) - multi_role} original, {multi_role} multi-role)')
