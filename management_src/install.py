"""
management_src/_install.py
Amca installer logic.
Standard library ONLY — no third-party dependencies.
"""

from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path
from typing import Optional

from .helpers import (
    AMCA_VERSION,
    OldInstall,
    ask_input,
    default_bin_dir,
    default_conf_base,
    detect_new_install,
    detect_old_install,
    exe,
    get_platform,
    hr,
    query_yes_no,
    remove_dir,
    remove_file,
    remove_from_posix_path,
    store_install_state,
    windows_remove_from_path,
    write_config_path_py,
)
from .core import (
    bootstrap_preset_plugins,
    create_compiled,
    create_venv,
    deploy_binaries,
    install_runtime_deps,
    setup_path,
)


# ── Old-install cleanup ───────────────────────────────────────────────────────

def cleanup_old_install(old: OldInstall, auto_yes: bool = False) -> None:
    """
    Remove the old C-runner based installation:
      • Strip PATH marker blocks (POSIX) or remove registry entry (Windows).
      • Remove the old binary.
      • Optionally remove the entire old data root.
    """
    plat = get_platform()

    # PATH — always clean regardless of whether the data dir is kept.
    if plat == "windows":
        ok = windows_remove_from_path(old.bin_dir)
        print(f"  {'Removed' if ok else 'Could not remove'} old PATH registry entry.")
    else:
        cleaned = remove_from_posix_path()
        for p in cleaned:
            print(f"  Removed old PATH block from: {p}")
        if not cleaned:
            print("  No old PATH blocks found in shell profiles.")

    # Binary.
    binary = old.binary()
    if binary.exists():
        remove_file(binary)
        print(f"  Removed old binary: {binary}")

    # Whole data directory.
    if old.amca_base.exists():
        print(f"  Old data directory: {old.amca_base}")
        if auto_yes or query_yes_no("  Remove old amca data directory?", default="yes"):
            remove_dir(old.amca_base)
            print(f"  Removed: {old.amca_base}")
        else:
            print("  Old data directory kept (safe to remove manually).")


# ── Config-dir prompt ─────────────────────────────────────────────────────────

def get_conf_path(auto_yes: bool = False) -> Path:
    """
    Ask the user where the config directory should live (or use the default /
    AMCA_CONFIG_PATH env var).  Writes the result into src/config_path.py.
    Returns the chosen absolute Path.
    """
    default    = default_conf_base() / "Amca"
    env_override = os.environ.get("AMCA_CONFIG_PATH")

    amca_conf_path = default

    if env_override:
        try:
            amca_conf_path = Path(env_override).expanduser().resolve()
            print(f"  Using AMCA_CONFIG_PATH override: {amca_conf_path}")
        except Exception as e:
            print(f"  Warning: invalid AMCA_CONFIG_PATH value: {e}. Using default.")
    elif not auto_yes and sys.stdin.isatty():
        print(f"  Default config root: {default}")
        raw = ask_input("  Press Enter to accept, or type a custom path")
        if raw:
            try:
                amca_conf_path = Path(raw).expanduser().resolve()
            except Exception as e:
                print(f"  Warning: invalid path: {e}. Using default.")

    if amca_conf_path.exists():
        if auto_yes or query_yes_no(
            f"  '{amca_conf_path}' already exists. Remove and reinstall?",
            default="no",
        ):
            shutil.rmtree(amca_conf_path)
            print("  Removed existing directory.")
        else:
            print("  Merging into existing directory.")

    amca_conf_path.mkdir(parents=True, exist_ok=True)
    write_config_path_py(amca_conf_path)
    return amca_conf_path


# ── Bin-dir prompt ────────────────────────────────────────────────────────────

def get_bin_dir(auto_yes: bool = False) -> Path:
    default = default_bin_dir()
    if auto_yes or not sys.stdin.isatty():
        default.mkdir(parents=True, exist_ok=True)
        return default
    print(f"  Default bin dir: {default}")
    raw = ask_input("  Press Enter to accept, or type a custom path")
    if not raw:
        default.mkdir(parents=True, exist_ok=True)
        return default
    try:
        bd = Path(raw).expanduser().resolve()
        bd.mkdir(parents=True, exist_ok=True)
        return bd
    except Exception as e:
        print(f"  Warning: invalid path: {e}. Using default.")
        default.mkdir(parents=True, exist_ok=True)
        return default


# ── Summary ───────────────────────────────────────────────────────────────────

def _summary(
    conf_path:   Path,
    bin_dir:     Path,
    deployed:    list[Path],
    path_target: Optional[str],
    plugins:     list[str],
) -> None:
    print(f"\n{hr('═')}")
    print("  Amca installation complete")
    print(hr("═"))
    print(f"  Version      : {AMCA_VERSION}")
    print(f"  Config root  : {conf_path}")
    print(f"  Binaries     : {bin_dir}")
    for d in deployed:
        print(f"               → {d.name}")
    if path_target:
        print(f"  PATH updated : {path_target}")
    else:
        print(f"  PATH update  : FAILED — add {bin_dir} to PATH manually")
    if plugins:
        print(f"  Plugins      : {', '.join(plugins)}")
    print()
    if get_platform() == "windows":
        print("  Open a new terminal, then run:  amca --help")
    else:
        print("  Restart your shell (or: source <profile>), then run:")
        print("    amca --help")
    print(hr("═"))


# ── Main entry ────────────────────────────────────────────────────────────────

def run(auto_yes: bool = False) -> None:
    print(f"\n{hr()}")
    print("  Amca Installer")
    print(hr())

    # 1. Warn if a new-style install already exists.
    existing = detect_new_install()
    if existing:
        print(f"\n  Existing installation detected: {existing}")
        if not auto_yes and query_yes_no(
            "  Run Update instead of a full reinstall?", default="yes"
        ):
            print("  Tip: choose Update from the menu, or run:")
            print("    python install_uninstall_update.py update")
            return

    # 2. Handle any lingering old-style install.
    old = detect_old_install()
    if old and old.exists():
        print(f"\n  Old-style (C-runner) installation found: {old.amca_base}")
        if auto_yes or query_yes_no(
            "  Clean it up before installing the new version?", default="yes"
        ):
            cleanup_old_install(old, auto_yes=auto_yes)
        else:
            print(
                f"  WARNING: old binary left at {old.bin_dir}.\n"
                f"           Make sure it does not shadow the new install."
            )

    # 3. Config directory.
    print("\nConfig directory …")
    conf_path = get_conf_path(auto_yes)
    print(f"  → {conf_path}")

    # 4. Bin directory.
    print("\nBinary directory …")
    bin_dir = get_bin_dir(auto_yes)
    print(f"  → {bin_dir}")

    # Persist early so update/uninstall can find everything even on partial failure.
    store_install_state(conf_path, bin_dir)

    # 5. Virtual environment (stored in conf_path, not the repo).
    print("\nVirtual environment …")
    venv_path = conf_path / ".venv"
    py = create_venv(venv_path)

    # 6. Runtime dependencies.
    print("\nInstalling runtime dependencies …")
    install_runtime_deps(py)

    # 7. Compile.
    print("\nCompiling executables …")
    compiled_path = create_compiled(py)

    # 8. Deploy.
    print("\nDeploying binaries …")
    deployed = deploy_binaries(compiled_path, bin_dir)
    if not deployed:
        print("ERROR: No binaries were deployed.")
        raise SystemExit(1)

    # 9. PATH.
    print("\nConfiguring PATH …")
    path_target = setup_path(bin_dir)

    # 10. Preset plugins.
    print("\nInstalling preset plugins …")
    plugins = bootstrap_preset_plugins(conf_path, overwrite=True)

    # 11. Summary.
    _summary(conf_path, bin_dir, deployed, path_target, plugins)
