# Testing uses Volcengine TTS 2.0 for concurrency, except the explicitly selected
# Winston news announcer. Inspect every resolved alias, including YAML anchors.
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
        if name == 'eino-podcast-news.host':
            expected = 'minimax-tenant:minimax-cn:Chinese (Mandarin)_Male_Announcer'
            path = Path('voices/minimax-cn/Chinese%20%28Mandarin%29_Male_Announcer.yaml')
            resource = yaml.safe_load(path.read_text())
            spec = resource['spec']
            if (voice_id != expected or resource['metadata']['id'] != expected or
                    spec['provider'] != {'kind': 'minimax-tenant', 'id': 'minimax-cn'} or
                    spec['provider_data'].get('voice_id') != 'Chinese (Mandarin)_Male_Announcer' or
                    spec['provider_data'].get('model') != 'speech-2.6-hd'):
                sys.exit(f'testing: {name} must resolve to Deploy Winston with speech-2.6-hd')
            continue
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
    print(f'validated {len(voices)} testing Voice bindings: Winston news host and Volcengine TTS 2.0')


if __name__ == '__main__':
    with open('runtime-profiles/testing.yaml', encoding='utf-8') as f:
        check_testing_voices(yaml.safe_load(f)['spec'])
