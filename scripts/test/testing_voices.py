# Testing uses Volcengine TTS 2.0 for concurrency; inspect every resolved alias,
# including YAML anchors and resources not referenced by a workflow manifest.
import re
import sys
from pathlib import Path

import yaml


def check_testing_voices(profile):
    voices = profile['resources']['voices']
    if not voices:
        sys.exit('testing: no Voice bindings')
    for name, binding in voices.items():
        voice_id = binding['resource_id']
        if not re.fullmatch(r'volc-tenant:volc-cn-beijing:[A-Za-z0-9_-]+', voice_id):
            sys.exit(f'testing: {name} must bind a Beijing Volcengine TTS 2.0 Voice, got {voice_id}')
        path = Path('voices/volc-cn-beijing') / (voice_id.split(':')[-1] + '.yaml')
        if not path.is_file():
            sys.exit(f'testing: {name} has no Voice resource: {voice_id}')
        resource = yaml.safe_load(path.read_text())
        spec = resource['spec']
        if (resource['metadata']['id'] != voice_id or
                spec['provider'] != {'kind': 'volc-tenant', 'id': 'volc-cn-beijing'} or
                spec['provider_data'].get('resource_id') != 'seed-tts-2.0'):
            sys.exit(f'testing: {name} must resolve to seed-tts-2.0, got {voice_id}')
    print(f'validated {len(voices)} testing Voice bindings use Volcengine TTS 2.0')


if __name__ == '__main__':
    with open('runtime-profiles/testing.yaml', encoding='utf-8') as f:
        check_testing_voices(yaml.safe_load(f)['spec'])
