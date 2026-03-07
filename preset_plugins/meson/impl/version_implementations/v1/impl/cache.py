"""
cache.py  (v1)

Drop-in replacement for the old globber.py subprocess call.
Detects C/C++ source changes using Path.rglob — no external dependency.
"""

from pathlib import Path

_GLOBS = ('*.c', '*.cpp', '*.cxx', '*.cc')
_CACHE_FILE = '.sources_cache'


def _glob(root: Path, exclude: Path) -> set[str]:
    found: set[str] = set()
    for pattern in _GLOBS:
        for p in root.rglob(pattern):
            resolved = p.resolve()
            if resolved.is_relative_to(exclude):
                continue
            found.add(p.relative_to(root).as_posix())
    return found


def _read(root: Path) -> set[str]:
    p = root / _CACHE_FILE
    if not p.exists():
        return set()
    return set(filter(None, p.read_text(encoding='utf-8').splitlines()))


def _write(root: Path, sources: set[str]) -> None:
    (root / _CACHE_FILE).write_text('\n'.join(sorted(sources)), encoding='utf-8')


def seed(root: Path, build_dir: Path) -> None:
    """Write the initial snapshot. Called on first meson setup."""
    _write(root, _glob(root, build_dir))


def changed(root: Path, build_dir: Path) -> bool:
    """
    Return True if sources differ from the last snapshot, and update the cache.
    Returns False (without reconfiguring) if no cache exists yet.
    """
    current = _glob(root, build_dir)
    cached  = _read(root)

    if not (root / _CACHE_FILE).exists():
        _write(root, current)
        return False

    if current != cached:
        _write(root, current)
        return True

    return False
