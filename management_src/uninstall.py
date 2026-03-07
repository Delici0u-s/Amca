"""
management_src/_uninstall.py
Amca uninstaller logic.
Standard library ONLY — no third-party dependencies.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

from .helpers import (
    AMCA_VERSION,
    OldInstall,
    default_bin_dir,
    default_conf_base,
    detect_new_install,
    detect_old_install,
    exe,
    get_platform,
    get_stored_bin_dir,
    get_stored_version,
    hr,
    query_yes_no,
    read_config_path_py,
    remove_dir,
    remove_file,
    remove_from_posix_path,
    reset_config_path_py,
    windows_remove_from_path,
)


# ── Granular removal helpers ──────────────────────────────────────────────────

def _remove_binaries(bin_dir: Path, auto_yes: bool) -> list[Path]:
    removed: list[Path] = []
    for name in ["amca", "amcapl"]:
        target = bin_dir / exe(name)
        if target.exists():
            if auto_yes or query_yes_no(f"  Remove {target}?"):
                remove_file(target)
                print(f"  Removed: {target}")
                removed.append(target)
            else:
                print(f"  Skipped: {target}")
        else:
            print(f"  Not found (already removed?): {target}")
    return removed


def _clean_path_entries(bin_dir: Path) -> bool:
    """Remove bin_dir from PATH (shell profiles on POSIX, registry on Windows)."""
    if get_platform() == "windows":
        ok = windows_remove_from_path(bin_dir)
        print(f"  {'Removed' if ok else 'Could not remove'} entry from Windows PATH registry.")
        return ok
    cleaned = remove_from_posix_path()
    for p in cleaned:
        print(f"  Removed PATH block from: {p}")
    if not cleaned:
        print("  No amca PATH blocks found in shell profiles.")
    return bool(cleaned)


def _remove_venv(conf_path: Path, auto_yes: bool) -> bool:
    venv = conf_path / ".venv"
    if not venv.exists():
        print("  Venv not found.")
        return False
    if auto_yes or query_yes_no(f"  Remove venv at {venv}?"):
        remove_dir(venv)
        print(f"  Removed: {venv}")
        return True
    print("  Venv kept.")
    return False


def _remove_config_dir(conf_path: Path, auto_yes: bool) -> bool:
    if not conf_path.exists():
        print("  Config directory not found.")
        return False
    print(f"\n  Config dir: {conf_path}")
    print("  This contains settings, installed plugins, and logs.")
    if auto_yes or query_yes_no(
        "  Remove the entire config directory? (cannot be undone)", default="no"
    ):
        remove_dir(conf_path)
        print(f"  Removed: {conf_path}")
        return True
    print("  Config directory kept.")
    return False


def _remove_compiled_dir(auto_yes: bool) -> bool:
    from _helpers import repo_root
    compiled = repo_root() / "compiled"
    if not compiled.exists():
        print("  compiled/ not found.")
        return False
    if auto_yes or query_yes_no("  Remove compiled/ directory from the repo?"):
        remove_dir(compiled)
        print(f"  Removed: {compiled}")
        return True
    print("  compiled/ kept.")
    return False


# ── Old-style install removal ─────────────────────────────────────────────────

def remove_old_install(old: OldInstall, auto_yes: bool) -> bool:
    """
    Remove an old C-runner installation.  PATH blocks are always stripped;
    the data directory is opt-in.  Returns True if the data dir was removed.
    """
    # PATH — strip regardless of what the user decides about the data dir.
    if get_platform() == "windows":
        ok = windows_remove_from_path(old.bin_dir)
        print(f"  {'Removed' if ok else 'Could not remove'} old PATH registry entry.")
    else:
        cleaned = remove_from_posix_path()
        for p in cleaned:
            print(f"  Removed old PATH block from: {p}")
        if not cleaned:
            print("  No old PATH blocks found.")

    # Binary.
    if old.binary().exists():
        if auto_yes or query_yes_no(f"  Remove old binary {old.binary()}?"):
            remove_file(old.binary())
            print(f"  Removed: {old.binary()}")

    # Data directory.
    if old.amca_base.exists():
        print(f"  Old data directory: {old.amca_base}")
        if auto_yes or query_yes_no(
            f"  Remove it (contains snakes/, templates/, bin/)?", default="yes"
        ):
            remove_dir(old.amca_base)
            print(f"  Removed: {old.amca_base}")
            return True
    return False


# ── Summary ───────────────────────────────────────────────────────────────────

def _summary(
    conf_path:        Path,
    bin_dir:          Path,
    binaries_removed: list[Path],
    path_cleaned:     bool,
    venv_removed:     bool,
    config_removed:   bool,
    compiled_removed: bool,
    old_removed:      bool,
) -> None:
    yn = lambda b: "yes" if b else "no"
    print(f"\n{hr('═')}")
    print("  Amca uninstall complete")
    print(hr("═"))
    if binaries_removed:
        print(f"  Binaries removed  : {', '.join(p.name for p in binaries_removed)}")
    else:
        print("  Binaries          : none removed")
    print(f"  PATH cleaned      : {yn(path_cleaned)}")
    print(f"  Venv removed      : {yn(venv_removed)}")
    print(f"  Config dir removed: {yn(config_removed)}")
    print(f"  compiled/ removed : {yn(compiled_removed)}")
    if old_removed:
        print("  Old install       : removed")
    print("  config_path.py    : reset")
    if not config_removed and conf_path.exists():
        print(f"\n  Config preserved at: {conf_path}")
        print("  Delete it manually for a complete removal.")
    print()
    if get_platform() != "windows":
        print("  Restart your shell to clear PATH changes from the current session.")
    print(hr("═"))


# ── Main entry ────────────────────────────────────────────────────────────────

def run(
    keep_config:   bool = False,
    keep_venv:     bool = False,
    keep_compiled: bool = False,
    auto_yes:      bool = False,
) -> None:
    print(f"\n{hr()}")
    print("  Amca Uninstaller")
    print(hr())

    # 1. Detect what is installed.
    new_conf = detect_new_install()
    old      = detect_old_install()
    has_new  = new_conf is not None
    has_old  = old is not None and old.exists()

    if not has_new and not has_old:
        print("\n  Nothing to uninstall — no Amca installation detected.")
        return

    # Resolve conf_path and bin_dir for the new install with safe fallbacks.
    if has_new:
        conf_path = new_conf                      # type: ignore[assignment]
        bin_dir   = get_stored_bin_dir(conf_path)
        version   = get_stored_version(conf_path)
        if bin_dir is None:
            bin_dir = default_bin_dir()
            print(f"  WARNING: bin_dir not recorded; defaulting to {bin_dir}")
    else:
        # No new install record — use platform defaults for cleanup attempts.
        conf_path = default_conf_base() / "Amca"
        bin_dir   = default_bin_dir()
        version   = None

    # Print what we found.
    print()
    if has_new:
        print(f"  New-version install  v{version or '?'}")
        print(f"    Config : {conf_path}")
        print(f"    Bin    : {bin_dir}")
    if has_old:
        print(f"  Old-version install (C-runner)")
        print(f"    Data   : {old.amca_base}")  # type: ignore[union-attr]
    print()

    if not auto_yes and not query_yes_no("Proceed with uninstall?", default="no"):
        print("Uninstall cancelled.")
        return

    print()

    # ── 2. New-style removal ──────────────────────────────────────────────────
    binaries_removed: list[Path] = []
    path_cleaned   = False
    venv_removed   = False
    config_removed = False
    compiled_removed = False

    if has_new:
        print("Removing new-version binaries …")
        binaries_removed = _remove_binaries(bin_dir, auto_yes)

        print("\nCleaning PATH entries …")
        path_cleaned = _clean_path_entries(bin_dir)

        if not keep_venv:
            print("\nVirtual environment …")
            venv_removed = _remove_venv(conf_path, auto_yes)

        if not keep_config:
            print("\nConfig directory …")
            config_removed = _remove_config_dir(conf_path, auto_yes)

    elif has_old:
        # No new install, but still strip any marker blocks that might exist.
        print("Cleaning PATH (marker blocks) …")
        _clean_path_entries(bin_dir)

    # ── 3. Old-style removal ──────────────────────────────────────────────────
    old_removed = False
    if has_old:
        print("\nOld-version installation …")
        old_removed = remove_old_install(old, auto_yes)  # type: ignore[arg-type]

    # ── 4. compiled/ dir ─────────────────────────────────────────────────────
    if not keep_compiled:
        print("\nCompiled directory …")
        compiled_removed = _remove_compiled_dir(auto_yes)

    # ── 5. Always reset config_path.py ───────────────────────────────────────
    reset_config_path_py()
    print("\n  Reset src/config_path.py to empty placeholder.")

    # ── 6. Summary ────────────────────────────────────────────────────────────
    _summary(
        conf_path, bin_dir,
        binaries_removed, path_cleaned,
        venv_removed, config_removed,
        compiled_removed, old_removed,
    )
