# src/impl/amca_pl_impl/call.py
import impl.util.config.config as cf
from pathlib import Path
from impl.util.globals import global_dir_parser as gdp
import impl.amca_impl.impl_execute.module_handler as mh
from impl.util.globals import amca_root_dir_info
import sys, os
from impl.util.globals import glog
from InquirerPy import inquirer


def load():
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

    args = sys.argv[1:]

    plugin = None

    plugin_arg_prefix = cf.plugin_settings.get("args.plugin_prefix")

    if len(args) != 0:
        if args[0].startswith(plugin_arg_prefix):
            split = args[0][2:].split(" ")
            plugin = split[0]
            if len(split) > 1:
                args[0] = " ".join(split[1:])
            else:
                args = args[1:]

    exit_message = "None (exit selection)"
    if plugin is None:
        plugin = inquirer.select(
            message="Pick a plugin to specifically load with only provided args:",
            choices=[*available_plugins, exit_message],
        ).execute()

        if plugin == exit_message:
            return

    plugin_info = gdp.parse_dir(Path(cf.plugin_settings.get("generic.plugin_path")))
    init_path = plugin_info.path / plugin / "init.py"

    module_or_instance = None
    if init_path.exists():
        plugin_root_info = gdp.parse_dir(init_path.parent)
        module_or_instance = mh.load_if_valid_module(
            init_path, plugin_root_info=plugin_root_info, dir_parser=gdp
        )

    if module_or_instance is None:
        print("Module could not be loaded")
        return

    module, pluginname = module_or_instance
    working_dir_info = gdp.parse_dir(Path(os.getcwd()))

    # Resolve the plugin's designated config folder (same logic as execute.py).
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
        # Correct 5-argument signature:
        # load(amca_root_dir, amca_root_plugin_dir, working_dir, dir_parser, args)
        module.load(amca_root_dir_info, amca_root_plugin_dir, working_dir_info, gdp, args)
    except Exception as exc:
        glog.error(f"Error while loading plugin {pluginname}: {exc}")
