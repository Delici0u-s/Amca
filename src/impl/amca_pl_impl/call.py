import impl.util.config.config as cf
from pathlib import Path
from impl.util.globals import global_dir_parser as gdp
import impl.amca_impl.impl_execute.module_handler as mh
from impl.util.globals import amca_root_dir_info
import sys, os
from impl.util.globals import glog
from InquirerPy import inquirer


def load(*, plugin: str | None = None, args: list[str] | None = None) -> None:
    """
    Call a specific plugin directly.

    Args:
        plugin: Plugin folder name to call. When None, uses TUI or parses sys.argv.
        args:   Args to pass to the plugin. When None, reads from sys.argv[1:].
    """
    try:
        plugin_path = Path(cf.plugin_settings.get("generic.plugin_path"))
    except Exception:
        print(f"Provided plugin_path in {cf.plugin_settings._path} is not valid")
        return

    if not plugin_path.exists():
        print("Plugin path is not available, please ensure the path is valid")
        return

    path_info = gdp.parse_dir(plugin_path)
    available_plugins = [str(p) for p in path_info.folders]

    # Resolve plugin name & args
    if plugin is None:
        # Try to extract from sys.argv (legacy CLI path)
        plugin_arg_prefix = cf.plugin_settings.get("args.plugin_prefix")
        remaining_args = sys.argv[1:]

        if remaining_args and remaining_args[0].startswith(plugin_arg_prefix):
            raw = remaining_args[0][len(plugin_arg_prefix):]
            split = raw.split(" ")
            plugin = split[0]
            extra = split[1:] if len(split) > 1 else remaining_args[1:]
            args = extra
        else:
            exit_message = "None (exit selection)"
            plugin = inquirer.select(
                message="Pick a plugin to specifically load with only provided args:",
                choices=[*available_plugins, exit_message],
            ).execute()
            if plugin == exit_message:
                return
            args = remaining_args

    if args is None:
        args = []

    # Load the plugin module
    init_path = path_info.path / plugin / "init.py"
    if not init_path.exists():
        print(f"Plugin '{plugin}' has no init.py")
        return

    plugin_root_info = gdp.parse_dir(init_path.parent)
    module_or_instance = mh.load_if_valid_module(
        init_path, plugin_root_info=plugin_root_info, dir_parser=gdp
    )

    if module_or_instance is None:
        print("Module could not be loaded")
        return

    module, pluginname = module_or_instance
    working_dir_info = gdp.parse_dir(Path(os.getcwd()))

    amca_conf_fold_name = str(cf.general_settings.get("amca_root.folder_name"))
    plugin_conf_path = (
        amca_root_dir_info.path / amca_conf_fold_name / "plugins"
        if amca_root_dir_info is not None
        else None
    )
    amca_root_plugin_dir = None
    if plugin_conf_path is not None:
        amca_root_plugin_dir = plugin_conf_path / pluginname
        amca_root_plugin_dir.mkdir(parents=True, exist_ok=True)

    try:
        module.load(amca_root_dir_info, amca_root_plugin_dir, working_dir_info, gdp, args)
    except Exception as exc:
        glog.error(f"Error while loading plugin '{pluginname}': {exc}")
