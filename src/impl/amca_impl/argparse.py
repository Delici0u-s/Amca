import sys
import argparse as ap
from pathlib import Path
from textwrap import dedent
from impl.util.dirparse import global_dir_parser as gdp
import impl.util.config.config as cf


def print_gen(Str: str):
    def a(args, plugin_args_map):
        # print("action:", Str)
        # print("parsed args:", args)
        # print("plugin args map:", plugin_args_map)
        ...

    return a


def normalize_plugin_opt_name(folder_name: str) -> str:
    return folder_name.replace("_", "-")


def normalize_plugin_name(name: str) -> str:
    return normalize_plugin_opt_name(str(name))


def build_main_parser(plugin_folders, enabled_plugins):
    """
    Build the top-level argparse parser and include enabled plugin markers in help.
    """
    plugin_markers = " ".join(
        f"--{normalize_plugin_opt_name(f)}"
        for f in sorted(plugin_folders)
        if normalize_plugin_name(f) in enabled_plugins
    )

    epilog = dedent(
        f"""
        Amca Version 2.0.1

        Plugin passthrough:
          You can pass arbitrary arguments to enabled plugins using plugin markers:
            {plugin_markers or "(no plugins enabled)"}

          Example:
            amca execute --meson <meson_args> --git <git_args>

          Notes:
            - Anything after a plugin marker is considered arguments for that plugin
              until the next plugin marker or end-of-command.
            - Plugin args are not interpreted by amca; they are handed to the plugin loader.
            - Plugin parsing is disabled for management subcommands: new (n), remove (r), args (a).
        """
    )

    parser = ap.ArgumentParser(
        prog="amca",
        description="loads plugins dynamically for AMCA",
        epilog=epilog,
        formatter_class=ap.RawDescriptionHelpFormatter,
        add_help=True,
    )

    subparsers = parser.add_subparsers(dest="mode")

    subparsers.add_parser(
        "new", aliases=["n"], help="create new amca root directory"
    ).set_defaults(func=print_gen("new"))

    subparsers.add_parser(
        "remove", aliases=["r"], help="remove amca root directory"
    ).set_defaults(func=print_gen("rem"))

    subparsers.add_parser(
        "args", aliases=["a"], help="cli interface for changing args"
    ).set_defaults(func=print_gen("args"))

    subparsers.add_parser(
        "execute",
        aliases=["e"],
        help="execute amca plugin loading (default if no arg is present)",
    ).set_defaults(func=print_gen("exec"))

    return parser


def extract_plugin_args(argv, plugin_folders):
    """
    Extract plugin argument groups using --<plugin> markers.
    """
    normalized_to_folder = {}
    plugin_markers = set()

    for f in plugin_folders:
        norm = normalize_plugin_opt_name(f)
        marker = f"--{norm}"
        plugin_markers.add(marker)
        normalized_to_folder[marker] = f

    remaining = []
    plugin_args = {f: [] for f in plugin_folders}

    i = 0
    L = len(argv)

    while i < L:
        tok = argv[i]

        if tok in plugin_markers:
            plugin = normalized_to_folder[tok]
            plugin_args[plugin] = []
            i += 1

            while i < L and argv[i] not in plugin_markers:
                plugin_args[plugin].append(argv[i])
                i += 1
        else:
            remaining.append(tok)
            i += 1

    return remaining, plugin_args


def eval_args():
    # --- config ---
    enabled_plugins = {
        normalize_plugin_name(p)
        for p in (cf.plugin_settings.get("enabled_plugins") or [])
    }

    warn_if_not_enabled = bool(
        cf.plugin_settings.get("logging.warn_if_plugin_arg_not_enabled")
    )

    # --- discovery ---
    plugin_path = Path(cf.plugin_settings.get("generic.plugin_path"))
    plugins = gdp.parse_dir(plugin_path).folders  # set(str)

    raw_argv = sys.argv[1:]

    # Disable plugin parsing for management commands
    management_tokens = {"new", "n", "remove", "r", "args", "a"}
    skip_plugin_parsing = any(tok in management_tokens for tok in raw_argv)

    if skip_plugin_parsing:
        remaining_argv = raw_argv
        plugin_args_map = {p: [] for p in plugins}
    else:
        remaining_argv, plugin_args_map = extract_plugin_args(raw_argv, plugins)

    # Filter + warn for disabled plugins
    filtered_plugin_args = {}

    for plugin, args in plugin_args_map.items():
        norm = normalize_plugin_name(plugin)

        if norm in enabled_plugins:
            filtered_plugin_args[plugin] = args
        else:
            filtered_plugin_args[plugin] = []

            if args and warn_if_not_enabled:
                print(
                    f"[amca] warning: arguments provided for disabled plugin "
                    f"'{plugin}' → ignored"
                )

    plugin_args_map = filtered_plugin_args

    # Parse remaining args
    parser = build_main_parser(plugins, enabled_plugins)
    parsed = parser.parse_args(remaining_argv)

    # Execute
    if hasattr(parsed, "func"):
        parsed.func(parsed, plugin_args_map)
    else:
        if cf.general_settings.get("debug"):
            print("No subcommand; parsed:", parsed)
            print("Plugin args:", plugin_args_map)


if __name__ == "__main__":
    eval_args()
