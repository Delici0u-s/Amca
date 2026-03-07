"""
management_src/_update.py
Amca updater logic.
Standard library ONLY — no third-party dependencies.
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path
from typing import Optional

from .helpers import (
    AMCA_VERSION,
    ask_input,
    default_bin_dir,
    detect_new_install,
    detect_old_install,
    get_platform,
    get_stored_bin_dir,
    get_stored_version,
    hr,
    query_yes_no,
    read_config_path_py,
    remove_dir,
    store_install_state,
    write_config_path_py,
)
from .core import (
    bootstrap_preset_plugins,
    create_compiled,
    create_venv,
    deploy_binaries,
    install_runtime_deps,
    remove_dir,   # re-used
    setup_path,
    venv_is_healthy,
)


# ── Install-state loader ──────────────────────────────────────────────────────

def _load_install_state() -> tuple[Path, Path]:
    """
    Return (conf_path, bin_dir) for the current new-style install.
    Prints a clear error and exits if nothing is found — including
    a specific message when only an old-style install is detected.
    """
    conf_path = detect_new_install()
    if not conf_path:
        raw = read_config_path_py()
        old = detect_old_install()
        if old and old.exists():
            print(
                "\nERROR: Only an old-style (C-runner) installation was found.\n"
                f"  Location : {old.amca_base}\n"
                "\n"
                "  update.py works only with the current plugin-based version.\n"
                "  Choose Install instead — it will migrate away from the old version."
            )
        elif raw:
            print(
                f"\nERROR: src/config_path.py points to '{raw}'\n"
                f"       but that directory does not exist or is missing general_conf.json.\n"
                f"       Choose Install to create a fresh installation."
            )
        else:
            print(
                "\nERROR: No Amca installation found.\n"
                "       Choose Install first."
            )
        raise SystemExit(1)

    bin_dir = get_stored_bin_dir(conf_path)
    if bin_dir is None:
        print(
            f"  WARNING: bin_dir not recorded in config.\n"
            f"           Defaulting to: {default_bin_dir()}"
        )
        bin_dir = default_bin_dir()

    return conf_path, bin_dir


# ── Optional reconfigure ──────────────────────────────────────────────────────

def _reconfigure(conf_path: Path, bin_dir: Path) -> tuple[Path, Path, bool]:
    """
    Interactively ask whether to change config dir and/or bin dir.
    Returns (new_conf_path, new_bin_dir, anything_changed).
    """
    changed = False

    print(f"\n  Current config root : {conf_path}")
    raw = ask_input("  Press Enter to keep, or type a new path")
    if raw:
        try:
            new_conf = Path(raw).expanduser().resolve()
            if new_conf != conf_path:
                if query_yes_no(
                    f"  Move config dir\n    from {conf_path}\n    to   {new_conf}\n  ?",
                    default="no",
                ):
                    new_conf.parent.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(conf_path), str(new_conf))
                    write_config_path_py(new_conf)
                    conf_path = new_conf
                    changed   = True
                    print(f"  Config dir moved to {conf_path}")
        except Exception as e:
            print(f"  Warning: {e}")

    print(f"\n  Current bin dir : {bin_dir}")
    raw2 = ask_input("  Press Enter to keep, or type a new path")
    if raw2:
        try:
            new_bin = Path(raw2).expanduser().resolve()
            if new_bin != bin_dir:
                bin_dir = new_bin
                changed = True
                print(f"  New bin dir: {bin_dir}")
        except Exception as e:
            print(f"  Warning: {e}")

    return conf_path, bin_dir, changed


# ── Preset-plugin update (additive) ──────────────────────────────────────────

def _update_preset_plugins(conf_path: Path) -> tuple[list[str], list[str]]:
    """
    Overwrite only the preset plugins from the repo.
    User-installed plugins (names not in preset_plugins/) are left untouched.
    Returns (updated_names, kept_user_plugin_names).
    """
    from _helpers import repo_root
    preset_src = repo_root() / "preset_plugins"
    if not preset_src.is_dir():
        print("  WARNING: preset_plugins/ not found — skipping plugin update.")
        return [], []

    plugins_dst  = conf_path / "Amca_config" / "plugins" / "installed_plugins"
    plugins_dst.mkdir(parents=True, exist_ok=True)
    preset_names = {item.name for item in preset_src.iterdir() if item.is_dir()}

    import shutil as _sh
    updated: list[str] = []
    for name in preset_names:
        src = preset_src / name
        dst = plugins_dst / name
        if dst.exists():
            remove_dir(dst)
        _sh.copytree(src, dst)
        updated.append(name)
        print(f"  Plugin updated: {name}")

    kept = [
        d.name for d in plugins_dst.iterdir()
        if d.is_dir() and d.name not in preset_names
    ]
    return updated, kept


# ── Summary ───────────────────────────────────────────────────────────────────

def _summary(
    conf_path:    Path,
    bin_dir:      Path,
    deployed:     list[Path],
    path_target:  Optional[str],
    upd_plugins:  list[str],
    kept_plugins: list[str],
    old_version:  Optional[str],
) -> None:
    print(f"\n{hr('═')}")
    print("  Amca update complete")
    print(hr("═"))
    print(f"  Version      : {old_version or '?'} → {AMCA_VERSION}")
    print(f"  Config root  : {conf_path}")
    if deployed:
        print(f"  Binaries     : {bin_dir}")
        for d in deployed:
            print(f"               → {d.name}")
    if path_target:
        print(f"  PATH target  : {path_target}")
    if upd_plugins:
        print(f"  Plugins upd  : {', '.join(upd_plugins)}")
    if kept_plugins:
        print(f"  Plugins kept : {', '.join(kept_plugins)}  (user-installed)")
    print()
    if deployed:
        if get_platform() == "windows":
            print("  Open a new terminal, then run:  amca --help")
        else:
            print("  Restart your shell if binaries changed.")
    print(hr("═"))


# ── Main entry ────────────────────────────────────────────────────────────────

def run(
    reconfigure:    bool = False,
    skip_recompile: bool = False,
    skip_plugins:   bool = False,
    auto_yes:       bool = False,
) -> None:
    print(f"\n{hr()}")
    print("  Amca Updater")
    print(hr())

    # 1. Locate install.
    conf_path, bin_dir = _load_install_state()
    old_version = get_stored_version(conf_path)
    print(f"\n  Found v{old_version or '?'} at : {conf_path}")
    print(f"  Bin dir              : {bin_dir}")

    # 2. Warn about any lingering old-style install.
    old = detect_old_install()
    if old and old.exists() and old.bin_dir != bin_dir:
        print(
            f"\n  NOTE: An old-style (C-runner) Amca also exists at:\n"
            f"    {old.amca_base}\n"
            f"  Consider running Uninstall to clean it up."
        )

    # 3. Optional reconfigure (always interactive).
    must_recompile = False
    if reconfigure:
        conf_path, bin_dir, changed = _reconfigure(conf_path, bin_dir)
        if changed:
            store_install_state(conf_path, bin_dir)
            must_recompile = True
            print("  Configuration saved.")

    deployed:    list[Path]    = []
    path_target: Optional[str] = None

    # 4. Venv → deps → compile → deploy.
    if not skip_recompile or must_recompile:
        venv_path = conf_path / ".venv"
        print("\nVirtual environment …")
        py = create_venv(venv_path, force=(must_recompile or not venv_is_healthy(venv_path)))

        print("\nUpgrading runtime dependencies …")
        install_runtime_deps(py)

        print("\nRecompiling executables …")
        compiled_path = create_compiled(py)

        print("\nDeploying binaries …")
        bin_dir.mkdir(parents=True, exist_ok=True)
        deployed = deploy_binaries(compiled_path, bin_dir)

        print("\nRefreshing PATH …")
        path_target = setup_path(bin_dir)

        store_install_state(conf_path, bin_dir)
    else:
        print("\nSkipping recompile (--skip-recompile).")

    # 5. Plugin update.
    upd_plugins:  list[str] = []
    kept_plugins: list[str] = []
    if not skip_plugins:
        print("\nUpdating preset plugins …")
        upd_plugins, kept_plugins = _update_preset_plugins(conf_path)
    else:
        print("\nSkipping plugin update (--skip-plugins).")

    # 6. Summary.
    _summary(conf_path, bin_dir, deployed, path_target,
             upd_plugins, kept_plugins, old_version)
