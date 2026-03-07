from impl.amca_impl.impl_execute.module_handler import load_if_valid_module
import impl.util.config.config as cf
from pathlib import Path
from impl.util.globals import global_dir_parser as gdp
from impl.util.globals import glog
from impl.util.globals import amca_root_dir_info
import os

def load(args, plugin_args_map):
    plugin_info = gdp.parse_dir(Path(cf.plugin_settings.get("generic.plugin_path")))
    modules = []
    for plugin in plugin_info.folders:
        init_path = plugin_info.path / plugin / "init.py"
        if init_path.exists():
            # produce a DirInfo for the plugin root and pass gdp as dir_parser
            plugin_root_info = gdp.parse_dir(init_path.parent)
            module_or_instance = load_if_valid_module(
                init_path, plugin_root_info=plugin_root_info, dir_parser=gdp
            )
            if module_or_instance is not None:
                modules.append(module_or_instance)
    to_load_modules = []
    working_dir_info = gdp.parse_dir(Path(os.getcwd()))
    amca_conf_fold_name = str(cf.general_settings.get("amca_root.folder_name"))
    plugin_conf_path = amca_root_dir_info.path / amca_conf_fold_name / "plugins" if amca_root_dir_info is not None else None
    for plugin, pluginname in modules:
        # plugin might be a module or an instance — both should expose should_load/load
        try:
            pl = None
            if amca_root_dir_info is not None:
                pl = plugin_conf_path / pluginname
                pl.mkdir(parents=True, exist_ok=True)
            if plugin.should_load(amca_root_dir_info, pl, working_dir_info, gdp, plugin_args_map[pluginname]):
                to_load_modules.append([plugin, pluginname])
        except Exception as exc:
            glog.error(f"Error when calling should_load on {plugin}: {exc}")
    enabled_plugins = [str(p) for p in cf.plugin_settings.get("enabled_plugins") or []]
    for plugin, pluginname in to_load_modules:
        try:
            if pluginname in enabled_plugins:
                pl = None
                if amca_root_dir_info is not None:
                    pl = plugin_conf_path / pluginname
                    pl.mkdir(parents=True, exist_ok=True)
                plugin.load(
                    amca_root_dir_info,
                    pl,
                    working_dir_info,
                    gdp,
                    plugin_args_map[pluginname],
                )
        except Exception as exc:
            glog.error(f"Error while loading plugin {plugin}: {exc}")
