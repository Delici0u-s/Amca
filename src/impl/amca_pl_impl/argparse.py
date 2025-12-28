import argparse as ap
from impl.amca_pl_impl import (
    enable,
    disable,
    install,
    uninstall,
    call,
    toggle,
    list as lip,
)
import sys


def eval_args():
    parser = ap.ArgumentParser(
        prog="amcapl",
        description="Handles plugin management for AMCA",
        epilog="Amcapl Version 0.1",
    )

    subparsers = parser.add_subparsers(dest="mode", required=True)

    subparsers.add_parser(
        "enable", aliases=["e"], help="enable an installed plugin"
    ).set_defaults(func=enable.load)

    subparsers.add_parser(
        "disable", aliases=["d"], help="disable an installed plugin"
    ).set_defaults(func=disable.load)

    subparsers.add_parser(
        "toggle", aliases=["t"], help="toggle enabled/disabled for plugins"
    ).set_defaults(func=toggle.load)

    subparsers.add_parser(
        "install", aliases=["i"], help="install an plugin from added sources"
    ).set_defaults(func=install.load)

    subparsers.add_parser(
        "uninstall", aliases=["u"], help="uninstall a plugin from this device"
    ).set_defaults(func=uninstall.load)

    subparsers.add_parser(
        "call", aliases=["c"], help="call specific plugins"
    ).set_defaults(func=call.load)

    subparsers.add_parser("list", aliases=["l"], help="list all plugins").set_defaults(
        func=lip.load
    )

    args, _ = parser.parse_known_args()

    sys.argv.pop(1)

    args.func()
