#!/usr/bin/env python3
"""Verify an extracted RiffGraph source bundle before executing its code."""

from __future__ import annotations

import hashlib
import re
import sys
from pathlib import Path, PurePosixPath

MANIFEST_NAME = ".riffgraph-manifest.sha256"
MANIFEST_LINE = re.compile(r"^([0-9a-f]{64})  (.+)$")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit(
            "usage: riffgraph_verify_source.py EXTRACTED_ROOT MANIFEST_SHA256"
        )
    root = Path(sys.argv[1]).resolve()
    expected_manifest_sha256 = sys.argv[2]
    manifest_path = root / MANIFEST_NAME
    if sha256_file(manifest_path) != expected_manifest_sha256:
        raise SystemExit("source manifest identity mismatch")

    expected: dict[str, str] = {}
    for line in manifest_path.read_text().splitlines():
        match = MANIFEST_LINE.fullmatch(line)
        if not match:
            raise SystemExit(f"invalid source manifest line: {line!r}")
        checksum, relative = match.groups()
        pure_path = PurePosixPath(relative)
        if pure_path.is_absolute() or ".." in pure_path.parts or relative in expected:
            raise SystemExit(f"unsafe or duplicate manifest path: {relative!r}")
        expected[relative] = checksum

    actual: set[str] = set()
    for path in root.rglob("*"):
        relative = path.relative_to(root).as_posix()
        if path.is_symlink():
            raise SystemExit(f"unexpected source symlink: {relative}")
        if path.is_file():
            actual.add(relative)
    expected_paths = set(expected) | {MANIFEST_NAME}
    if actual != expected_paths:
        missing = sorted(expected_paths - actual)
        extra = sorted(actual - expected_paths)
        raise SystemExit(f"source file-set mismatch; missing={missing}, extra={extra}")

    for relative, checksum in expected.items():
        if sha256_file(root / relative) != checksum:
            raise SystemExit(f"source checksum mismatch: {relative}")


if __name__ == "__main__":
    main()
