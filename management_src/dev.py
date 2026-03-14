"""
management_src/dev.py
Developer-environment setup (local venv + compile + config bootstrap).
Standard library ONLY — no third-party dependencies.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

from .helpers import (
    get_platform,
    write_config_path_py,
)
from .core import (
    bootstrap_preset_plugins,
    create_compiled,
    create_venv,
    install_runtime_deps,
)


# ── Defaults ──────────────────────────────────────────────────────────────────

_DEFAULT_VENV   = Path("dev/.venv")
_DEFAULT_CONFIG = Path("dev/config")


# ── Main entry ────────────────────────────────────────────────────────────────

def run(
    venv_path:   Optional[Path] = None,
    conf_path:   Optional[Path] = None,
    auto_yes:    bool = False,
) -> None:
    """
    Set up a local developer environment:
      1. Create / reuse a venv
      2. Install runtime deps
      3. Compile amca + amcapl via PyInstaller
      4. Bootstrap preset plugins into the config dir
      5. Write src/config_path.py so the source tree points at the dev config

    *venv_path* and *conf_path* default to dev/.venv and dev/config
    (relative to cwd) when not supplied.
    """
    # ── Resolve paths ─────────────────────────────────────────────────────────
    if venv_path is None:
        if auto_yes or not sys.stdin.isatty():
            venv_path = _DEFAULT_VENV.resolve()
        else:
            sys.stdout.write(f"  Venv path    [{_DEFAULT_VENV}]:   ")
            sys.stdout.flush()
            try:
                raw = input().strip()
            except (EOFError, KeyboardInterrupt):
                print("\n  Cancelled.")
                return
            venv_path = (Path(raw).expanduser() if raw else _DEFAULT_VENV).resolve()

    if conf_path is None:
        if auto_yes or not sys.stdin.isatty():
            conf_path = _DEFAULT_CONFIG.resolve()
        else:
            sys.stdout.write(f"  Config path  [{_DEFAULT_CONFIG}]:  ")
            sys.stdout.flush()
            try:
                raw = input().strip()
            except (EOFError, KeyboardInterrupt):
                print("\n  Cancelled.")
                return
            conf_path = (Path(raw).expanduser() if raw else _DEFAULT_CONFIG).resolve()

    # ── 1. Venv ───────────────────────────────────────────────────────────────
    print()
    print("  [1/4] Venv")
    print("  " + "─" * 40)
    try:
        py = create_venv(venv_path, force=False)
        install_runtime_deps(py)
    except SystemExit as exc:
        print(f"  ERROR: {exc}")
        return

    # ── 2. Write config_path.py ───────────────────────────────────────────────
    print()
    print("  [2/4] Wiring config path")
    print("  " + "─" * 40)
    write_config_path_py(conf_path)
    print(f"  src/config_path.py → {conf_path}")

    # ── 3. Compile ────────────────────────────────────────────────────────────
    print()
    print("  [3/4] Compiling")
    print("  " + "─" * 40)
    try:
        compiled_path = create_compiled(py)
    except SystemExit as exc:
        print(f"  ERROR: {exc}")
        return

    # ── 4. Config + plugins ───────────────────────────────────────────────────
    print()
    print("  [4/4] Config")
    print("  " + "─" * 40)
    conf_path.mkdir(parents=True, exist_ok=True)
    plugins = bootstrap_preset_plugins(conf_path, overwrite=False)
    if plugins:
        print(f"  Plugins installed: {', '.join(plugins)}")
    else:
        print("  Config dir initialised (no preset plugins copied).")


    # ── Summary ───────────────────────────────────────────────────────────────
    if get_platform() == "windows":
        activate_cmd = str(venv_path / "Scripts" / "activate.bat")
    else:
        activate_cmd = f"source {venv_path / 'bin' / 'activate'}"

    print()
    print("  ✓  Dev environment ready.")
    print()
    print("  Paths")
    print("  " + "─" * 40)
    print(f"  Venv      : {venv_path}")
    print(f"  Compiled  : {compiled_path}")
    print(f"  Config    : {conf_path}")
    print()
    print("  Activate with:")
    print(f"    {activate_cmd}")
    print()
