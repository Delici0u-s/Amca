"""
helper/source_cache.py

Detects whether the set of C/C++ source files under a meson project root has
changed since the last recorded snapshot.  The snapshot (cache) is stored as a
sorted, newline-delimited text file of POSIX-relative paths so it is readable,
diff-able, and portable across Windows / Linux / macOS.

Intended use: called once per pipeline run by reconfigure.py to decide whether
`meson setup --reconfigure` is necessary.
"""

from pathlib import Path
from typing import Optional

# Patterns that constitute "source files" for the purposes of change detection.
_SOURCE_GLOBS: tuple[str, ...] = ('*.c', '*.cpp', '*.cxx', '*.cc')

_CACHE_FILENAME = '.amca_sources_cache'


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _cache_path(meson_root: Path, amca_plugin_dir: Optional[Path]) -> Path:
    """
    Return the path where the cache file should live.

    Preference order:
      1. amca_root_plugin_dir  — plugin-reserved folder, keeps project root clean.
      2. meson_root            — fallback when no plugin dir is designated.
    """
    base = amca_plugin_dir if amca_plugin_dir is not None else meson_root
    return base / _CACHE_FILENAME


def _glob_sources(meson_root: Path, exclude_dirs: frozenset[Path] = frozenset()) -> set[str]:
    """
    Return all C/C++ source files under *meson_root* as POSIX paths relative to
    that root.

    *exclude_dirs* — absolute, resolved Paths that should be skipped wholesale
    (e.g. the build directory, which may live inside the project tree).
    Uses POSIX representation so the stored cache is identical on every OS.
    """
    found: set[str] = set()
    for pattern in _SOURCE_GLOBS:
        for p in meson_root.rglob(pattern):
            # Skip anything inside an excluded subtree.
            try:
                resolved = p.resolve()
                if any(resolved.is_relative_to(exc) for exc in exclude_dirs):
                    continue
                found.add(p.relative_to(meson_root).as_posix())
            except ValueError:
                pass  # relative_to failed — path is outside root, ignore
    return found


def _read_cache(cache_file: Path) -> set[str]:
    if not cache_file.exists():
        return set()
    return set(filter(None, cache_file.read_text(encoding='utf-8').splitlines()))


def _write_cache(cache_file: Path, sources: set[str]) -> None:
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    cache_file.write_text('\n'.join(sorted(sources)), encoding='utf-8')


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def sources_changed(
    meson_root: Path,
    amca_plugin_dir: Optional[Path],
    exclude_dirs: frozenset[Path] = frozenset(),
) -> bool:
    """
    Return True if the C/C++ source tree has changed since the last snapshot.

    Side-effects
    ------------
    - If no cache exists yet (e.g. right after the first `meson setup`):
      writes the current snapshot and returns **False**.  This avoids a
      spurious `--reconfigure` on the first pipeline run after setup.
    - If the cache exists and differs from the current state:
      overwrites the cache with the current snapshot and returns **True**.
    - If the cache matches: returns **False**, cache untouched.

    Parameters
    ----------
    meson_root      : Absolute path to the directory containing meson.build.
    amca_plugin_dir : Plugin-reserved directory (may be None).
    exclude_dirs    : Resolved absolute Paths to skip during globbing
                      (typically the meson build directory).
    """
    cache_file = _cache_path(meson_root, amca_plugin_dir)
    current = _glob_sources(meson_root, exclude_dirs)

    if not cache_file.exists():
        # First encounter: seed the cache so the *next* run has a baseline.
        _write_cache(cache_file, current)
        return False

    cached = _read_cache(cache_file)
    if current != cached:
        _write_cache(cache_file, current)
        return True

    return False
