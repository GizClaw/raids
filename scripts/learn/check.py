#!/usr/bin/env python3
"""Compare generated learn-* packages and print readable drift diagnostics."""

from __future__ import annotations

import difflib
import sys
from pathlib import Path


def files_below(root: Path) -> dict[Path, Path]:
    if not root.is_dir():
        return {}
    return {path.relative_to(root): path for path in root.rglob("*") if path.is_file()}


def compare_directory(expected: Path, actual: Path, label: Path) -> bool:
    expected_files = files_below(expected)
    actual_files = files_below(actual)
    clean = True
    for relative in sorted(expected_files.keys() - actual_files.keys()):
        print(f"missing generated file: {label / relative}", file=sys.stderr)
        clean = False
    for relative in sorted(actual_files.keys() - expected_files.keys()):
        print(f"unexpected generated file: {label / relative}", file=sys.stderr)
        clean = False
    for relative in sorted(expected_files.keys() & actual_files.keys()):
        expected_bytes = expected_files[relative].read_bytes()
        actual_bytes = actual_files[relative].read_bytes()
        if expected_bytes == actual_bytes:
            continue
        clean = False
        display = label / relative
        try:
            expected_lines = expected_bytes.decode("utf-8").splitlines(keepends=True)
            actual_lines = actual_bytes.decode("utf-8").splitlines(keepends=True)
        except UnicodeDecodeError:
            print(f"binary generated file differs: {display}", file=sys.stderr)
            continue
        sys.stderr.writelines(
            difflib.unified_diff(
                expected_lines,
                actual_lines,
                fromfile=f"committed/{display}",
                tofile=f"generated/{display}",
            )
        )
    return clean


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: check.py EXPECTED_ROOT GENERATED_ROOT", file=sys.stderr)
        return 2
    expected_root = Path(sys.argv[1]).resolve()
    actual_root = Path(sys.argv[2]).resolve()
    raids = sorted(path.parent.name for path in (expected_root / "workflows").glob("learn-*/knowledge.json"))
    if not raids:
        print("no workflows/learn-*/knowledge.json files found", file=sys.stderr)
        return 1
    clean = True
    for raid in raids:
        for label in (Path("workflows") / raid, Path("tests/giztest") / raid):
            if not compare_directory(expected_root / label, actual_root / label, label):
                clean = False
    if not clean:
        print("learn raid package drift detected; run python3 scripts/learn/generate.py", file=sys.stderr)
        return 1
    print("learn raid packages match generated output")
    return 0


if __name__ == "__main__":
    sys.exit(main())
