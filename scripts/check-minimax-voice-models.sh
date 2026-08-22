#!/usr/bin/env bash

set -euo pipefail

readonly expected_count=635
readonly expected_model='speech-2.6-turbo'
readonly voice_dirs=(voices/minimax-cn voices/minimax-global)

for dir in "${voice_dirs[@]}"; do
  if [[ ! -d "$dir" ]]; then
    printf 'missing MiniMax Voice directory: %s\n' "$dir" >&2
    exit 1
  fi
done

actual_count="$({ find "${voice_dirs[@]}" -type f -name '*.yaml' -print; } | wc -l | tr -d '[:space:]')"
if [[ "$actual_count" != "$expected_count" ]]; then
  printf 'expected %s MiniMax Voice files, found %s\n' "$expected_count" "$actual_count" >&2
  exit 1
fi

failed=0
while IFS= read -r file; do
  model_count="$(grep -Ec '^[[:space:]]+model:' "$file" || true)"
  expected_count_in_file="$(grep -Fxc "    model: ${expected_model}" "$file" || true)"
  if [[ "$model_count" != 1 || "$expected_count_in_file" != 1 ]]; then
    printf '%s must contain exactly one model: %s field\n' "$file" "$expected_model" >&2
    failed=1
  fi
done < <(find "${voice_dirs[@]}" -type f -name '*.yaml' -print | LC_ALL=C sort)

if [[ "$failed" != 0 ]]; then
  exit 1
fi

printf 'validated %s MiniMax Voices with model %s\n' "$actual_count" "$expected_model"
