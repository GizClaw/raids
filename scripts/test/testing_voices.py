# Testing uses Volcengine TTS 2.0 for concurrency; inspect every resolved alias,
# including YAML anchors and resources not referenced by a workflow manifest.
import re
import sys

import yaml


def check_testing_voices(profile):
    voices = profile['resources']['voices']
    if not voices:
        sys.exit('testing: no Voice bindings')
    for name, binding in voices.items():
        voice_id = binding['resource_id']
        if not re.fullmatch(r'volc-tenant:volc-cn-beijing:[A-Za-z0-9_-]+_uranus_bigtts', voice_id):
            sys.exit(f'testing: {name} must bind a Volcengine TTS 2.0 (*_uranus_bigtts) Voice, got {voice_id}')
    print(f'validated {len(voices)} testing Voice bindings use Volcengine TTS 2.0')


if __name__ == '__main__':
    with open('runtime-profiles/testing.yaml', encoding='utf-8') as f:
        check_testing_voices(yaml.safe_load(f)['spec'])
