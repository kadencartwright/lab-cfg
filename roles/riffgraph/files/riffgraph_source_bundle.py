#!/usr/bin/env python3
"""Build a deterministic archive of the allowlisted RiffGraph inputs."""

from __future__ import annotations

import hashlib
import json
import os
import sys
import tarfile
import tempfile
from pathlib import Path

ROOT_FILES = (
    "pyproject.toml",
    "uv.lock",
    "README.md",
    "LICENSE",
    "THIRD_PARTY.md",
)
TREE_DIRS = ("src", "requirements", "docs")
EXCLUDED_DIRS = {"__pycache__", ".pytest_cache", ".ruff_cache", ".mypy_cache"}
EXCLUDED_SUFFIXES = {".pyc", ".pyo", ".pyd"}
MANIFEST_NAME = ".riffgraph-manifest.sha256"


def deployment_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for name in ROOT_FILES:
        path = root / name
        if path.is_symlink():
            raise SystemExit(f"deployment symlinks are not allowed: {path}")
        if not path.is_file():
            raise SystemExit(f"missing deployment input: {path}")
        files.append(path)
    for directory_name in TREE_DIRS:
        directory = root / directory_name
        if directory.is_symlink():
            raise SystemExit(f"deployment symlinks are not allowed: {directory}")
        if not directory.is_dir():
            raise SystemExit(f"missing deployment input: {directory}")
        for path in directory.rglob("*"):
            relative = path.relative_to(root)
            if path.is_symlink():
                raise SystemExit(f"deployment symlinks are not allowed: {path}")
            if (
                path.is_file()
                and not EXCLUDED_DIRS.intersection(relative.parts)
                and path.suffix not in EXCLUDED_SUFFIXES
            ):
                files.append(path)
    return sorted(files, key=lambda path: path.relative_to(root).as_posix())


def add_bytes(archive: tarfile.TarFile, name: str, content: bytes) -> None:
    info = tarfile.TarInfo(name)
    info.size = len(content)
    info.mode = 0o644
    info.mtime = 0
    info.uid = 0
    info.gid = 0
    info.uname = ""
    info.gname = ""
    with tempfile.SpooledTemporaryFile() as payload:
        payload.write(content)
        payload.seek(0)
        archive.addfile(info, payload)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: riffgraph_source_bundle.py SOURCE_ROOT")
    root = Path(sys.argv[1]).expanduser().resolve()
    entries: list[tuple[str, bytes]] = []
    for path in deployment_files(root):
        relative = path.relative_to(root).as_posix()
        if "\n" in relative or "\r" in relative:
            raise SystemExit(f"unsupported deployment path: {relative!r}")
        entries.append((relative, path.read_bytes()))

    manifest = "".join(
        f"{hashlib.sha256(content).hexdigest()}  {relative}\n" for relative, content in entries
    ).encode()
    requirements = dict(entries).get("requirements/muscriptor.txt")
    if requirements is None:
        raise SystemExit("missing deployment input: requirements/muscriptor.txt")
    muscriptor_requirements_sha256 = hashlib.sha256(requirements).hexdigest()
    cache_dir = Path(tempfile.gettempdir()) / "riffgraph-source-bundles"
    cache_dir.mkdir(mode=0o755, parents=True, exist_ok=True)
    handle, temporary_name = tempfile.mkstemp(prefix=".building-", suffix=".tar", dir=cache_dir)
    os.close(handle)
    temporary = Path(temporary_name)
    try:
        with tarfile.open(temporary, mode="w", format=tarfile.PAX_FORMAT) as archive:
            for relative, content in entries:
                add_bytes(archive, relative, content)
            add_bytes(archive, MANIFEST_NAME, manifest)
        bundle_sha256 = sha256_file(temporary)
        destination = cache_dir / f"{bundle_sha256}.tar"
        if destination.exists():
            if sha256_file(destination) != bundle_sha256:
                raise SystemExit(f"cached bundle checksum mismatch: {destination}")
            temporary.unlink()
        else:
            os.replace(temporary, destination)
            destination.chmod(0o644)
    finally:
        if temporary.exists():
            temporary.unlink()

    print(
        json.dumps(
            {
                "path": str(destination),
                "sha256": bundle_sha256,
                "manifest_sha256": hashlib.sha256(manifest).hexdigest(),
                "muscriptor_requirements_sha256": muscriptor_requirements_sha256,
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
