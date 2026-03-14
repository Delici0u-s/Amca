# impl/amca_pl_impl/argparse.py
import argparse as ap
from impl.amca_pl_impl import (
    enable,
    disable,
    install,
    uninstall,
    call,
    toggle,
    update,
    list as lip,
)
import sys


def eval_args():
    parser = ap.ArgumentParser(
        prog="amcapl",
        description="Handles plugin management for AMCA",
        epilog="Amcapl Version 0.2",
    )

    subparsers = parser.add_subparsers(dest="mode", required=True)

    # -- enable --
    p_enable = subparsers.add_parser("enable", aliases=["e"], help="enable installed plugin(s)")
    p_enable.add_argument("plugins", nargs="*", metavar="PLUGIN", help="plugin(s) to enable (omit for TUI)")

    # -- disable --
    p_disable = subparsers.add_parser("disable", aliases=["d"], help="disable plugin(s)")
    p_disable.add_argument("plugins", nargs="*", metavar="PLUGIN", help="plugin(s) to disable (omit for TUI)")

    # -- toggle --
    p_toggle = subparsers.add_parser("toggle", aliases=["t"], help="toggle enabled/disabled for plugin(s)")
    p_toggle.add_argument("plugins", nargs="*", metavar="PLUGIN", help="plugin(s) to toggle (omit for TUI)")

    # -- install --
    p_install = subparsers.add_parser("install", aliases=["i"], help="install plugin(s) from configured sources")
    p_install.add_argument("plugins", nargs="*", metavar="PLUGIN", help="plugin(s) to install (omit for TUI)")

    # -- uninstall --
    p_uninstall = subparsers.add_parser("uninstall", aliases=["u"], help="permanently remove plugin(s)")
    p_uninstall.add_argument("plugins", nargs="*", metavar="PLUGIN", help="plugin(s) to uninstall (omit for TUI)")
    p_uninstall.add_argument("-y", "--yes", action="store_true", help="skip confirmation prompts")

    # -- update --
    p_update = subparsers.add_parser("update", aliases=["up"], help="re-download installed plugin(s) from sources")
    p_update.add_argument("plugins", nargs="*", metavar="PLUGIN", help="plugin(s) to update (omit for TUI, '*' for all)")

    # -- call --
    p_call = subparsers.add_parser("call", aliases=["c"], help="call a specific plugin directly")
    p_call.add_argument("plugin", nargs="?", metavar="PLUGIN", default=None, help="plugin to call (omit for TUI)")
    p_call.add_argument("args", nargs=ap.REMAINDER, metavar="ARG", help="args forwarded to the plugin")

    # -- list --
    subparsers.add_parser("list", aliases=["l"], help="list all installed plugins and their state")

    args = parser.parse_args()

    mode = args.mode

    if mode in ("enable", "e"):
        enable.load(plugins=args.plugins or None)
    elif mode in ("disable", "d"):
        disable.load(plugins=args.plugins or None)
    elif mode in ("toggle", "t"):
        toggle.load(plugins=args.plugins or None)
    elif mode in ("install", "i"):
        install.load(plugins=args.plugins or None)
    elif mode in ("uninstall", "u"):
        uninstall.load(plugins=args.plugins or None, yes=args.yes)
    elif mode in ("update", "up"):
        # treat ["*"] as "update all" sentinel
        plugins_arg = args.plugins if args.plugins else None
        update.load(plugins=plugins_arg)
    elif mode in ("call", "c"):
        call.load(plugin=args.plugin, args=args.args or None)
    elif mode in ("list", "l"):
        lip.load()
