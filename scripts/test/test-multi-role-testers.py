#!/usr/bin/env python3
"""Offline contract regression; Ruby parses YAML, Python exercises portable scripts.

Only codepoints() is adapted to Python's native Unicode iteration. Admin validate
remains responsible for validating the actual Starlark resource.
"""
import json
from pathlib import Path
import subprocess


def documents(paths):
    return json.loads(subprocess.check_output(
        ['ruby', '-ryaml', '-rjson', '-e',
         'puts JSON.generate(ARGV.map { |p| YAML.load_file(p) })', *map(str, paths)],
        text=True))


def script(doc):
    node = next(n for n in doc['spec']['eino']['graph']['nodes'] if n['id'] == 'route-turn')
    return node['source']


paths = sorted(Path('workflows').glob('*/test.multi-role.yaml'))
assert len(paths) == 31
for path, doc, original, soak in zip(paths, documents(paths),
        documents([p.with_name('test.yaml') for p in paths]),
        documents([Path('tests/giztest/soak') / (p.parent.name + '.giztest.yaml') for p in paths])):
    raid = path.parent.name
    ns = {}
    exec(script(doc).replace('.codepoints()', ''), ns)
    old = {}
    exec(script(original).replace('.codepoints()', ''), old)
    assert ns['REQUESTS'] == old['REQUESTS']
    assert ns['CHECKPOINTS'] == old['CHECKPOINTS']
    for current, previous in zip(ns['CHECKS'], old['CHECKS']):
        for field in ('required', 'required_any', 'forbidden'):
            assert current[field] == previous[field], (raid, field)
    for request, current, previous in zip(ns['REQUESTS'], ns['CHECKS'], old['CHECKS']):
        if '只确认' in request:
            assert current['min_runes'] == previous['min_runes'], (raid, request)
            assert current['max_runes'] <= previous['max_runes'], (raid, request)
    ordinary = [i for i, c in enumerate(ns['CHECKS']) if c['min_runes'] == 300]
    assert ordinary
    for index in ordinary:
        assert ns['CHECKS'][index]['max_runes'] == 600
    index = ordinary[0]
    # Isolate counting from the scenario's mandatory content, without mutating files.
    ns['CHECKS'][index] = {'min_runes': 300, 'max_runes': 600}
    for size, failure in [(299, 'min_runes:'), (300, None), (600, None), (601, 'max_runes:')]:
        text = '景' * size
        for candidate in (text, '【旁白】' + text if raid != 'murder-mystery' else '【主持人】' + text):
            failures = ns['deterministic_failures'](index, candidate)
            assert (not failures if failure is None else any(f.startswith(failure) for f in failures)), (raid, size, failures)
    manifest = json.loads(path.with_name('raid.json').read_text())
    tester = manifest['testers']['multi-role']
    assert tester['workflow_id'] == doc['metadata']['id'] == raid + '-test-multi-role'
    assert tester['file'] == path.name
    assert tester['parameters'] == manifest['tester']['parameters']
    expected = sorted(k for k in manifest['implementations'] if k.endswith('-multi-role'))
    assert tester['implementations'] == expected or sorted(tester['implementations']) == expected
    routed = []
    for step in soak['steps']:
        request = step.get('rpc', {}).get('request', {})
        if step.get('client', '').endswith('_tester') and 'workflow_name' in request:
            multi = 'multi_role' in step['client']
            assert request['workflow_name'] == raid + ('-test-multi-role' if multi else '-test')
            if multi:
                routed.append(step['client'])
    assert len(set(routed)) == len(expected), raid
print('validated 31 multi-role Tester contracts, Unicode boundaries, marker stripping and soak routing')
