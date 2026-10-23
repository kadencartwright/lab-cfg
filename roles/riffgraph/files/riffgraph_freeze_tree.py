#!/usr/bin/env python3
"""Make an installed runtime root-owned and read-only to unprivileged users."""

from __future__ import annotations

import argparse
import json
import os
import stat
from collections.abc import Iterator
from pathlib import Path


def walk_without_following_links(root: Path) -> Iterator[Path]:
    """Yield root and every descendant without traversing symbolic links."""
    yield root
    stack = [root]
    while stack:
        directory = stack.pop()
        with os.scandir(directory) as entries:
            for entry in entries:
                path = Path(entry.path)
                yield path
                if entry.is_dir(follow_symlinks=False):
                    stack.append(path)


def desired_mode(current_mode: int, *, is_directory: bool) -> int:
    """Match chmod u=rwX,go=rX without treating symlink 0777 as drift."""
    executable = is_directory or bool(current_mode & 0o111)
    return 0o755 if executable else 0o644


def freeze_tree(root: Path, *, check: bool) -> dict[str, int | bool]:
    if not root.is_dir() or root.is_symlink():
        raise ValueError(f"runtime root must be a real directory: {root}")

    ownership_updates = 0
    mode_updates = 0

    for path in walk_without_following_links(root):
        metadata = path.lstat()
        is_link = stat.S_ISLNK(metadata.st_mode)
        ownership_drift = metadata.st_uid != 0 or metadata.st_gid != 0

        if ownership_drift:
            ownership_updates += 1
            if not check:
                os.lchown(path, 0, 0)

        if is_link:
            continue

        current_mode = stat.S_IMODE(metadata.st_mode)
        expected_mode = desired_mode(
            current_mode,
            is_directory=stat.S_ISDIR(metadata.st_mode),
        )
        if current_mode != expected_mode:
            mode_updates += 1
            if not check:
                path.chmod(expected_mode)

    return {
        "changed": bool(ownership_updates or mode_updates),
        "ownership_updates": ownership_updates,
        "mode_updates": mode_updates,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    print(json.dumps(freeze_tree(args.root, check=args.check), sort_keys=True))


if __name__ == "__main__":
    main()
