#!/usr/bin/env python3
"""
install_uninstall_update.py
Amca management CLI — install, update, or uninstall Amca.

Usage (interactive menu — recommended):
    python install_uninstall_update.py

Direct subcommands:
    python install_uninstall_update.py install   [--yes]
    python install_uninstall_update.py update    [--reconfigure] [--skip-recompile]
                                                 [--skip-plugins] [--yes]
    python install_uninstall_update.py uninstall [--yes] [--keep-config]
                                                 [--keep-venv] [--keep-compiled]
    python install_uninstall_update.py status

Standard library ONLY — no third-party packages required to run this script.
"""

from .management_src._future__ import annotations

import argparse
import sys
from pathlib import Path

# ── Bootstrap: add management_src/ to sys.path ────────────────────────────────
_MGMT_SRC = Path(__file__).parent / "management_src"
if not _MGMT_SRC.is_dir():
    print(f"ERROR: management_src/ directory not found next to this script.\n"
          f"       Expected: {_MGMT_SRC}", file=sys.stderr)
    raise SystemExit(1)
if str(_MGMT_SRC) not in sys.path:
    sys.path.insert(0, str(_MGMT_SRC))

# Imports from management_src — all stdlib only.
from management_src.helpers import (
    AMCA_VERSION,
    detect_new_install,
    detect_old_install,
    get_stored_bin_dir,
    get_stored_version,
    hr,
    query_yes_no,
)


# ─────────────────────────────────────────────────────────────────────────────
#  Pure-stdlib menu rendering
# ─────────────────────────────────────────────────────────────────────────────

_W = 62  # menu width


def _banner() -> None:
    inner = _W - 2
    print()
    print("┌" + "─" * inner + "┐")
    title = "  Amca Management"
    ver   = f"v{AMCA_VERSION}  "
    gap   = inner - len(title) - len(ver)
    print("│" + title + " " * gap + ver + "│")
    print("└" + "─" * inner + "┘")
    print()


def _status_block() -> None:
    """One-shot summary of what is (or isn't) installed."""
    new_conf = detect_new_install()
    old      = detect_old_install()

    print("  Status")
    print("  " + "─" * 40)

    if new_conf:
        version = get_stored_version(new_conf) or "?"
        bin_dir = get_stored_bin_dir(new_conf)
        print(f"  Current install  : v{version}")
        print(f"  Config root      : {new_conf}")
        print(f"  Bin directory    : {bin_dir or '(not recorded)'}")
    else:
        print("  Current install  : not found")

    if old and old.exists():
        tag = "← leftover, consider removing" if new_conf else "(C-runner, old version)"
        print(f"  Old install      : {old.amca_base}  {tag}")

    print()


def _numbered_menu(title: str, options: list[str], cancel_label: str = "Back") -> int:
    """
    Display a numbered list and return the 0-based index of the chosen option.
    Returns -1 if the user picks the cancel/back option.
    """
    all_opts = options + [cancel_label]
    print(f"  {title}")
    print("  " + "─" * 40)
    for i, opt in enumerate(all_opts, 1):
        prefix = "  └─" if i == len(all_opts) else "  ├─"
        print(f"{prefix} {i}) {opt}")
    print()
    while True:
        sys.stdout.write(f"  Choice [1-{len(all_opts)}]: ")
        sys.stdout.flush()
        raw = input().strip()
        if raw.isdigit():
            n = int(raw)
            if 1 <= n <= len(all_opts):
                return -1 if n == len(all_opts) else n - 1
        print(f"  Please enter a number between 1 and {len(all_opts)}.")


def _pause() -> None:
    print()
    try:
        input("  Press Enter to return to the menu …")
    except (EOFError, KeyboardInterrupt):
        pass


# ─────────────────────────────────────────────────────────────────────────────
#  Action menus
# ─────────────────────────────────────────────────────────────────────────────

def _menu_install() -> None:
    from management_src.install import run as _run

    print()
    print("  Install")
    print("  " + "─" * 40)
    print("  Will:")
    print("    • Ask where to store the config directory")
    print("    • Build a virtual environment and compile the executables")
    print("    • Deploy binaries to a bin directory and update PATH")
    print("    • Install preset plugins (meson enabled by default)")
    print()
    old = detect_old_install()
    if old and old.exists():
        print(f"  ⚠  Old-style (C-runner) install detected at: {old.amca_base}")
        print("     You will be asked whether to clean it up.")
        print()
    new = detect_new_install()
    if new:
        print(f"  ⚠  Current-version install already exists at: {new}")
        print("     You will be asked whether to reinstall or switch to Update.")
        print()

    if not query_yes_no("  Continue?", default="yes"):
        print("  Cancelled.")
        return

    _run(auto_yes=False)


def _menu_update() -> None:
    from management_src.update import run as _run

    print()
    print("  Update")
    print("  " + "─" * 40)

    new_conf = detect_new_install()
    if not new_conf:
        old = detect_old_install()
        if old and old.exists():
            print()
            print("  An old-style (C-runner) install was found, but Update requires")
            print("  the current plugin-based version to already be installed.")
            print("  Please run Install — it will migrate the old version.")
        else:
            print()
            print("  No installation found. Please run Install first.")
        return

    version = get_stored_version(new_conf) or "?"
    print(f"  Current version : v{version}")
    print(f"  Target version  : v{AMCA_VERSION}")
    print()

    choices = [
        "Full update  (recompile executables + refresh plugins)",
        "Update plugins only  (skip recompile)",
        "Recompile only  (skip plugin update)",
        "Full update + reconfigure paths first",
    ]
    idx = _numbered_menu("Choose update mode:", choices)
    if idx == -1:
        print("  Cancelled.")
        return

    _run(
        reconfigure    = (idx == 3),
        skip_recompile = (idx == 1),
        skip_plugins   = (idx == 2),
        auto_yes       = False,
    )


def _menu_uninstall() -> None:
    from .management_src.uninstall import run as _run, remove_old_install

    print()
    print("  Uninstall")
    print("  " + "─" * 40)

    new_conf = detect_new_install()
    old      = detect_old_install()
    has_new  = new_conf is not None
    has_old  = old is not None and old.exists()

    if not has_new and not has_old:
        print()
        print("  No Amca installation detected.")
        return

    if has_new:
        v = get_stored_version(new_conf) or "?"
        print(f"  Current install : v{v} at {new_conf}")
    if has_old:
        print(f"  Old install     : {old.amca_base}")
    print()

    choices = []
    if has_new:
        choices += [
            "Remove executables + PATH  (keep config & plugins)",
            "Full removal  (remove everything including config & plugins)",
        ]
    if has_old:
        choices.append(
            "Remove old-style (C-runner) install only"
            + ("  ← also removes leftover" if has_new else "")
        )

    idx = _numbered_menu("What would you like to remove?", choices)
    if idx == -1:
        print("  Cancelled.")
        return

    # Map choice index to what was actually shown.
    new_choices_count = 2 if has_new else 0
    has_old_choice    = len(choices) > new_choices_count

    if has_new and idx == 0:
        # Keep config and plugins — only remove binaries + PATH.
        _run(keep_config=True, keep_venv=True, keep_compiled=False, auto_yes=False)

    elif has_new and idx == 1:
        print()
        print("  WARNING: This permanently deletes your config, settings,")
        print("           and all installed plugins.")
        if query_yes_no("  Are you sure?", default="no"):
            _run(keep_config=False, keep_venv=False, keep_compiled=False, auto_yes=False)
        else:
            print("  Cancelled.")

    elif has_old_choice and idx == new_choices_count:
        print()
        remove_old_install(old, auto_yes=False)
        if not has_new:
            from .management_src.helpers import reset_config_path_py
            reset_config_path_py()
            print("  Reset src/config_path.py.")


def _menu_status() -> None:
    print()
    print("  Detailed Status")
    print("  " + "─" * 40)
    _status_block()


# ─────────────────────────────────────────────────────────────────────────────
#  Interactive main loop
# ─────────────────────────────────────────────────────────────────────────────

def _interactive() -> None:
    top_choices = ["Install", "Update", "Uninstall", "Status"]
    while True:
        _banner()
        _status_block()

        idx = _numbered_menu("Choose an action:", top_choices, cancel_label="Exit")
        if idx == -1:
            print()
            print("  Bye!")
            print()
            return

        try:
            if   idx == 0: _menu_install()
            elif idx == 1: _menu_update()
            elif idx == 2: _menu_uninstall()
            elif idx == 3: _menu_status()
        except SystemExit as exc:
            # Let sub-commands raise SystemExit without killing the menu loop,
            # unless it's a real error code.
            if exc.code not in (0, None):
                print(f"\n  Operation failed (exit code {exc.code}).")

        _pause()


# ─────────────────────────────────────────────────────────────────────────────
#  Argument-driven (non-interactive) mode
# ─────────────────────────────────────────────────────────────────────────────

def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="install_uninstall_update.py",
        description="Amca management — install, update, or uninstall.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Run without arguments for the interactive menu.\n\n"
            "Examples:\n"
            "  python install_uninstall_update.py install\n"
            "  python install_uninstall_update.py install --yes\n"
            "  python install_uninstall_update.py update --skip-plugins\n"
            "  python install_uninstall_update.py uninstall --yes\n"
            "  python install_uninstall_update.py status\n"
        ),
    )
    sub = p.add_subparsers(dest="command")

    # install
    pi = sub.add_parser("install", help="Install Amca.")
    pi.add_argument("--yes", "-y", action="store_true",
                    help="Non-interactive: accept all defaults.")

    # update
    pu = sub.add_parser("update", help="Update an existing Amca installation.")
    pu.add_argument("--reconfigure",    "-r", action="store_true",
                    help="Re-ask for config dir and bin dir before updating.")
    pu.add_argument("--skip-recompile",       action="store_true",
                    help="Skip venv rebuild and binary recompilation.")
    pu.add_argument("--skip-plugins",         action="store_true",
                    help="Skip refreshing preset plugins.")
    pu.add_argument("--yes", "-y",            action="store_true",
                    help="Non-interactive.")

    # uninstall
    pun = sub.add_parser("uninstall", help="Uninstall Amca.")
    pun.add_argument("--yes",           "-y", action="store_true",
                     help="Answer yes to all prompts (full non-interactive removal).")
    pun.add_argument("--keep-config",         action="store_true",
                     help="Keep the config directory (settings + plugins).")
    pun.add_argument("--keep-venv",           action="store_true",
                     help="Keep the virtual environment.")
    pun.add_argument("--keep-compiled",       action="store_true",
                     help="Keep the compiled/ directory in the repo.")

    # status
    sub.add_parser("status", help="Show installation status and exit.")

    return p


def _run_command(args: argparse.Namespace) -> None:
    cmd = args.command

    if cmd == "install":
        from .management_src.install import run as _run
        _run(auto_yes=args.yes)

    elif cmd == "update":
        from .management_src.update import run as _run
        _run(
            reconfigure    = args.reconfigure,
            skip_recompile = args.skip_recompile,
            skip_plugins   = args.skip_plugins,
            auto_yes       = args.yes,
        )

    elif cmd == "uninstall":
        from .management_src.uninstall import run as _run
        _run(
            keep_config   = args.keep_config,
            keep_venv     = args.keep_venv,
            keep_compiled = args.keep_compiled,
            auto_yes      = args.yes,
        )

    elif cmd == "status":
        _banner()
        _status_block()

    else:
        _build_parser().print_help()


# ─────────────────────────────────────────────────────────────────────────────
#  Entry point
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    if len(sys.argv) == 1:
        # No arguments → interactive menu.
        try:
            _interactive()
        except (KeyboardInterrupt, EOFError):
            print("\n\n  Interrupted. Bye!")
        return

    parser = _build_parser()
    args   = parser.parse_args()

    if args.command is None:
        parser.print_help()
        return

    try:
        _run_command(args)
    except KeyboardInterrupt:
        print("\n\nInterrupted.")
        raise SystemExit(7)


if __name__ == "__main__":
    main()
