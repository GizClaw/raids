#!/usr/bin/env python3
"""Regenerate repository learn-* raid packages from their knowledge cards."""

from __future__ import annotations

import argparse
import importlib
import re
import sys
from collections import defaultdict
from pathlib import Path


sys.dont_write_bytecode = True


def repository_root() -> Path:
    return Path(__file__).resolve().parents[2]


def discover_raids(repo: Path) -> list[str]:
    return sorted(path.parent.name for path in (repo / "workflows").glob("learn-*/knowledge.json"))


def subject_name(raid: str) -> str:
    # Grade-scoped packages share one subject module (learn-math-grade3 -> math);
    # an all-grades package is its own subject (learn-chinese-stories -> chinese_stories).
    match = re.fullmatch(r"learn-([a-z0-9-]+?)(?:-grade[1-6])?", raid)
    if not match:
        raise ValueError(f"learn raid does not follow learn-<subject>[-grade<N>]: {raid}")
    return match.group(1).replace("-", "_")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, help="output root (default: repository root)")
    parser.add_argument("raids", nargs="*", help="specific learn-* raid IDs (default: all)")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo = repository_root()
    out = args.out.resolve() if args.out else repo
    raids = args.raids or discover_raids(repo)
    if not raids:
        raise ValueError("no learn-* knowledge cards found")
    grouped: dict[str, list[str]] = defaultdict(list)
    for raid in raids:
        grouped[subject_name(raid)].append(raid)
    for subject, subject_raids in sorted(grouped.items()):
        module_name = f"subject_{subject}"
        try:
            module = importlib.import_module(module_name)
        except ModuleNotFoundError as error:
            if error.name == module_name:
                raise ValueError(f"missing subject module scripts/learn/{module_name}.py") from error
            raise
        for status in module.generate(repo, out, sorted(subject_raids)):
            print(status)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, ValueError, KeyError) as error:
        print(f"generate learn raids: {error}", file=sys.stderr)
        sys.exit(1)
