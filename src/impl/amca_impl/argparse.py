import sys
import argparse as ap
from pathlib import Path
from textwrap import dedent
import impl.util.config.config as cf
from impl.amca_impl import new, remove, args_cli
from impl.amca_impl.impl_execute import execute
from impl.util.globals import global_dir_parser as gdp, amca_root_dir_info
from impl.util.globals import root_dir, glog


def normalize_plugin_opt_name(folder_name: str) -> str:
    return folder_name.replace("_", "-")


def normalize_plugin_name(name: str) -> str:
    return normalize_plugin_opt_name(str(name))


def _prescan_plugin_prefix(argv: list[str]) -> str | None:
    """
    Quick pre-scan for --plugin-prefix before full argparse, so the prefix
    used during plugin-arg extraction can be overridden in the same invocation.
    """
    for i, tok in enumerate(argv):
        if tok == "--plugin-prefix" and i + 1 < len(argv):
            return argv[i + 1]
        if tok.startswith("--plugin-prefix="):
            return tok.split("=", 1)[1]
    return None


def build_main_parser(plugin_folders, enabled_plugins):
    plugin_arg_prefix = cf.plugin_settings.get("args.plugin_prefix")
    plugin_markers = " ".join(
        f"{plugin_arg_prefix}{normalize_plugin_opt_name(f)}"
        for f in sorted(plugin_folders)
        if normalize_plugin_name(f) in enabled_plugins
    )

    epilog = dedent(
        f"""
        Amca Version 2.0.2

        Plugin passthrough:
          You can pass arbitrary arguments to enabled plugins using plugin markers:
            {plugin_markers or "(no plugins enabled)"}

          Example:
            amca execute {plugin_arg_prefix}meson <meson_args> {plugin_arg_prefix}git <git_args>

          Notes:
            - Anything after a plugin marker is consumed by that plugin until the
              next marker or end-of-command.
            - Plugin args are not interpreted by amca itself.
            - Plugin parsing is skipped for: new (n), remove (r), args (a).
            - --plugin-prefix, --plugin-path, and --depth take effect after
              amca-root resolution, which happens at import time.

          Amca config path: "{root_dir}"
        """
    )

    parser = ap.ArgumentParser(
        prog="amca",
        description="Loads plugins dynamically based on directory contents and args.",
        epilog=epilog,
        formatter_class=ap.RawDescriptionHelpFormatter,
        add_help=True,
    )

    # ── Config-override flags ─────────────────────────────────────────────────
    cfg = parser.add_argument_group("config overrides (session-only, not persisted)")
    cfg.add_argument(
        "--debug",
        action="store_true",
        default=False,
        help="enable debug output (overrides config 'debug')",
    )
    cfg.add_argument(
        "--no-greet",
        dest="no_greet",
        action="store_true",
        default=False,
        help="suppress greeting (overrides 'extreamly_important.greet_user')",
    )
    cfg.add_argument(
        "--exit-on-error",
        dest="exit_on_error",
        action="store_true",
        default=False,
        help="exit on first plugin error (overrides 'generic.exit_on_plugin_error')",
    )
    cfg.add_argument(
        "--exit-on-not-found",
        dest="exit_on_not_found",
        action="store_true",
        default=False,
        help="exit if an enabled plugin is missing on disk (overrides 'generic.exit_on_plugin_not_found')",
    )
    cfg.add_argument(
        "--plugin-prefix",
        dest="plugin_prefix",
        metavar="PREFIX",
        default=None,
        help=(
            "plugin marker prefix (overrides 'args.plugin_prefix', "
            "default: '---'). Note: affects *next* plugin-arg extraction only "
            "if passed before any plugin markers in the same invocation."
        ),
    )
    cfg.add_argument(
        "--plugin-path",
        dest="plugin_path",
        metavar="PATH",
        default=None,
        help="override plugin directory (overrides 'generic.plugin_path')",
    )
    cfg.add_argument(
        "--depth",
        type=int,
        metavar="N",
        default=None,
        help="amca-root search depth (overrides 'amca_root.recursive_search_depth')",
    )
    cfg.add_argument(
        "--editor",
        metavar="CMD",
        default=None,
        help="default file editor (overrides 'default_file_editor')",
    )
    cfg.add_argument(
        "--no-warn",
        dest="no_warn",
        action="store_true",
        default=False,
        help="suppress 'plugin arg ignored' warnings (overrides 'logging.warn_if_plugin_arg_not_enabled')",
    )
    cfg.add_argument(
        "--print-loaded",
        dest="print_loaded",
        action="store_true",
        default=False,
        help="print a line when each plugin loads (overrides 'logging.print_loaded')",
    )
    cfg.add_argument(
        "--log-mode",
        dest="log_mode",
        choices=["console", "file", "both", "silent"],
        default=None,
        help="logger output mode (overrides 'logging.log_mode')",
    )
    cfg.add_argument(
        "--log-level",
        dest="log_level",
        choices=["INFO", "SUCCESS", "WARN", "ERROR", "FATAL"],
        default=None,
        help="minimum log level (overrides 'logging.min_level')",
    )

    # ── Subcommands ───────────────────────────────────────────────────────────
    subparsers = parser.add_subparsers(dest="mode")

    subparsers.add_parser(
        "new", aliases=["n"], help="create new amca root directory"
    ).set_defaults(func=new.load)

    subparsers.add_parser(
        "remove", aliases=["r"], help="remove amca root directory"
    ).set_defaults(func=remove.load)

    subparsers.add_parser(
        "args", aliases=["a"], help="cli interface for changing plugin args"
    ).set_defaults(func=args_cli.load)

    subparsers.add_parser(
        "execute",
        aliases=["e"],
        help="execute plugin loading (default when no subcommand is given)",
    ).set_defaults(func=execute.load)

    return parser


def extract_plugin_args(argv, plugin_folders):
    plugin_arg_prefix = cf.plugin_settings.get("args.plugin_prefix")
    normalized_to_folder: dict[str, str] = {}
    plugin_markers: set[str] = set()

    for f in plugin_folders:
        norm = normalize_plugin_opt_name(f)
        marker = f"{plugin_arg_prefix}{norm}"
        plugin_markers.add(marker)
        normalized_to_folder[marker] = f

    remaining: list[str] = []
    plugin_args: dict[str, list[str]] = {f: [] for f in plugin_folders}

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


def _apply_overrides(parsed: ap.Namespace) -> None:
    """Push session-only CLI flag values into the in-memory config store."""
    from impl.util.globals import glog

    if parsed.debug:
        cf.general_settings.set("debug", True)
    if parsed.no_greet:
        cf.general_settings.set("extreamly_important.greet_user", False)
    if parsed.exit_on_error:
        cf.plugin_settings.set("generic.exit_on_plugin_error", True)
    if parsed.exit_on_not_found:
        cf.plugin_settings.set("generic.exit_on_plugin_not_found", True)
    if parsed.plugin_prefix is not None:
        cf.plugin_settings.set("args.plugin_prefix", parsed.plugin_prefix)
    if parsed.plugin_path is not None:
        cf.plugin_settings.set("generic.plugin_path", parsed.plugin_path)
    if parsed.depth is not None:
        cf.general_settings.set("amca_root.recursive_search_depth", parsed.depth)
    if parsed.editor is not None:
        cf.general_settings.set("default_file_editor", parsed.editor)
    if parsed.no_warn:
        cf.plugin_settings.set("logging.warn_if_plugin_arg_not_enabled", False)
    if parsed.print_loaded:
        cf.plugin_settings.set("logging.print_loaded", True)
    if parsed.log_mode is not None:
        cf.general_settings.set("logging.log_mode", parsed.log_mode)
        glog.set_mode(parsed.log_mode)
    if parsed.log_level is not None:
        cf.general_settings.set("logging.min_level", parsed.log_level)
        glog.set_min_level(parsed.log_level)

def split_at_first_plugin_marker(argv: list[str], plugin_prefix: str) -> tuple[list[str], list[str]]:
  first_marker_index = next(
    (i for i, tok in enumerate(argv) if tok.startswith(plugin_prefix)),
    len(argv),
  )
  return argv[:first_marker_index], argv[first_marker_index:]

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
  plugins = gdp.parse_dir(plugin_path).folders

  raw_argv = sys.argv[1:]

  early_prefix = _prescan_plugin_prefix(raw_argv)
  if early_prefix is not None:
    cf.plugin_settings.set("args.plugin_prefix", early_prefix)

  plugin_prefix = cf.plugin_settings.get("args.plugin_prefix")

  # Split once: main CLI before first plugin marker, plugin payload after it
  main_argv, plugin_argv = split_at_first_plugin_marker(raw_argv, plugin_prefix)

  # Parse plugin args only from the plugin slice
  _, plugin_args_map = extract_plugin_args(plugin_argv, plugins)

  # Filter + warn for disabled plugins
  filtered_plugin_args: dict[str, list[str]] = {}
  arg_path = Path()
  if amca_root_dir_info is not None:
    amca_root_folder = amca_root_dir_info.path / cf.general_settings.get(
      "amca_root.folder_name"
    )
    arg_path = amca_root_folder / "args"

  for plugin, args in plugin_args_map.items():
    norm = normalize_plugin_name(plugin)

    if norm in enabled_plugins:
      if amca_root_dir_info is not None:
        plugin_arg_file = arg_path / f"{plugin}.args"
        if plugin_arg_file.exists():
          tf: list[str] = []
          with plugin_arg_file.open("r", encoding="utf-8") as fh:
            for line in fh:
              line = line.strip()
              if not line or line.startswith("#"):
                continue
              tf.append(line)
          args = [*tf, *args]

      filtered_plugin_args[plugin] = args
    else:
      filtered_plugin_args[plugin] = []
      if args and warn_if_not_enabled:
        print(
          f"[amca] warning: arguments provided for disabled plugin "
          f"'{plugin}' → ignored"
        )

  plugin_args_map = filtered_plugin_args

  parser = build_main_parser(plugins, enabled_plugins)
  parsed = parser.parse_args(main_argv)

  _apply_overrides(parsed)

  if hasattr(parsed, "func"):
    parsed.func(parsed, plugin_args_map)
  else:
    if cf.general_settings.get("debug"):
      print("No subcommand; parsed:", parsed)
      print("Plugin args:", plugin_args_map)
    execute.load(parsed, plugin_args_map)

# def eval_args():
#     # --- config ---
#     enabled_plugins = {
#         normalize_plugin_name(p)
#         for p in (cf.plugin_settings.get("enabled_plugins") or [])
#     }
#     warn_if_not_enabled = bool(
#         cf.plugin_settings.get("logging.warn_if_plugin_arg_not_enabled")
#     )
#
#     # --- discovery ---
#     plugin_path = Path(cf.plugin_settings.get("generic.plugin_path"))
#     plugins = gdp.parse_dir(plugin_path).folders  # set(str)
#
#     raw_argv = sys.argv[1:]
#
#     # Pre-scan for --plugin-prefix so the override applies to plugin-arg extraction
#     early_prefix = _prescan_plugin_prefix(raw_argv)
#     if early_prefix is not None:
#         cf.plugin_settings.set("args.plugin_prefix", early_prefix)
#
#     # Disable plugin parsing for management commands
#     management_tokens = {"new", "n", "remove", "r", "args", "a"}
#     skip_plugin_parsing = any(tok in management_tokens for tok in raw_argv)
#
#     if skip_plugin_parsing:
#         remaining_argv = raw_argv
#         plugin_args_map = {p: [] for p in plugins}
#     else:
#         remaining_argv, plugin_args_map = extract_plugin_args(raw_argv, plugins)
#
#     # Filter + warn for disabled plugins
#     filtered_plugin_args: dict[str, list[str]] = {}
#
#     arg_path = Path()
#     if amca_root_dir_info is not None:
#         amca_root_folder = amca_root_dir_info.path / cf.general_settings.get(
#             "amca_root.folder_name"
#         )
#         arg_path = amca_root_folder / "args"
#
#     for plugin, args in plugin_args_map.items():
#         norm = normalize_plugin_name(plugin)
#
#         if norm in enabled_plugins:
#             if amca_root_dir_info is not None:
#                 plugin_arg_file = arg_path / f"{plugin}.args"
#                 if plugin_arg_file.exists():
#                     tf: list[str] = []
#                     with plugin_arg_file.open("r", encoding="utf-8") as fh:
#                         for line in fh:
#                             line = line.strip()
#                             if not line or line.startswith("#"):
#                                 continue
#                             tf.append(line)
#                     args = [*tf, *args]
#
#             filtered_plugin_args[plugin] = args
#         else:
#             filtered_plugin_args[plugin] = []
#             if args and warn_if_not_enabled:
#                 print(
#                     f"[amca] warning: arguments provided for disabled plugin "
#                     f"'{plugin}' → ignored"
#                 )
#
#     plugin_args_map = filtered_plugin_args
#
#     # Parse remaining args (includes config-override flags)
#     parser = build_main_parser(plugins, enabled_plugins)
#     parsed = parser.parse_args(remaining_argv)
#
#     # Apply session-only overrides before dispatch
#     _apply_overrides(parsed)
#
#     # Dispatch
#     if hasattr(parsed, "func"):
#         parsed.func(parsed, plugin_args_map)
#     else:
#         if cf.general_settings.get("debug"):
#             print("No subcommand; parsed:", parsed)
#             print("Plugin args:", plugin_args_map)
#         execute.load(parsed, plugin_args_map)


if __name__ == "__main__":
    eval_args()
