#!/usr/bin/env python3
"""Compare generated guess-* packages with the catalog and print readable drift."""

from __future__ import annotations

import difflib
import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))

import generate  # noqa: E402


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: check.py EXPECTED_ROOT GENERATED_ROOT", file=sys.stderr)
        return 2
    expected_root = Path(sys.argv[1]).resolve()
    actual_root = Path(sys.argv[2]).resolve()
    raids = generate.discover_raids(expected_root)
    if not raids:
        print("no workflows/guess-*/puzzles.json files found", file=sys.stderr)
        return 1
    clean = True
    for raid in raids:
        generated = {path for path in (actual_root / "workflows" / raid).rglob("*") if path.is_file()}
        committed = {path for path in (expected_root / "workflows" / raid).rglob("*")
                     if path.is_file() and path.name != "puzzles.json"}
        relatives = {p.relative_to(actual_root) for p in generated} | {p.relative_to(expected_root) for p in committed}
        for tier in generate.TIERS:
            for root in (expected_root, actual_root):
                relatives |= {p.relative_to(root) for p in (root / "tests/giztest" / tier).glob(f"{raid}.*giztest.yaml")}
        for relative in sorted(relatives):
            expected, actual = expected_root / relative, actual_root / relative
            if not expected.is_file():
                print(f"missing committed file: {relative}", file=sys.stderr)
                clean = False
                continue
            if not actual.is_file():
                print(f"unexpected committed file: {relative}", file=sys.stderr)
                clean = False
                continue
            if expected.read_bytes() == actual.read_bytes():
                continue
            clean = False
            sys.stderr.writelines(difflib.unified_diff(
                expected.read_text(encoding="utf-8").splitlines(keepends=True),
                actual.read_text(encoding="utf-8").splitlines(keepends=True),
                fromfile=f"committed/{relative}", tofile=f"generated/{relative}"))
    if not clean:
        print("guess raid package drift detected; run python3 scripts/guess/generate.py", file=sys.stderr)
        return 1
    print(f"guess raid packages match generated output: {', '.join(raids)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
