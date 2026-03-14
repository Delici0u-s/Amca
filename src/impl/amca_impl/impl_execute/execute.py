from impl.amca_impl.impl_execute.module_handler import load_if_valid_module
import impl.util.config.config as cf
from pathlib import Path
from impl.util.globals import global_dir_parser as gdp
from impl.util.globals import glog
from impl.util.globals import amca_root_dir_info
import os
import sys


def load(args, plugin_args_map):
    plugin_info = gdp.parse_dir(Path(cf.plugin_settings.get("generic.plugin_path")))

    # Resolve config flags once
    enabled_plugins: set[str] = {
        str(p) for p in (cf.plugin_settings.get("enabled_plugins") or [])
    }
    exit_on_error: bool      = bool(cf.plugin_settings.get("generic.exit_on_plugin_error"))
    exit_on_not_found: bool  = bool(cf.plugin_settings.get("generic.exit_on_plugin_not_found"))
    warn_not_found: bool     = bool(cf.plugin_settings.get("logging.warn_if_plugin_not_found"))
    print_loaded: bool       = bool(cf.plugin_settings.get("logging.print_loaded"))

    # Discover all plugin modules present on disk
    modules: list[tuple] = []
    for plugin_folder in plugin_info.folders:
        init_path = plugin_info.path / plugin_folder / "init.py"
        if init_path.exists():
            plugin_root_info = gdp.parse_dir(init_path.parent)
            result = load_if_valid_module(
                init_path, plugin_root_info=plugin_root_info, dir_parser=gdp
            )
            if result is not None:
                modules.append(result)

    # Warn / abort for enabled plugins that aren't on disk at all
    discovered_names: set[str] = {name for _, name in modules}
    for ep in enabled_plugins:
        if ep not in discovered_names:
            if warn_not_found:
                glog.warn(f"Enabled plugin '{ep}' not found on disk — skipping")
            if exit_on_not_found:
                glog.error(
                    f"Aborting: enabled plugin '{ep}' not found "
                    f"(generic.exit_on_plugin_not_found=True)"
                )
                sys.exit(1)

    # Shared context
    working_dir_info = gdp.parse_dir(Path(os.getcwd()))
    amca_conf_fold_name = str(cf.general_settings.get("amca_root.folder_name"))
    plugin_conf_path = (
        amca_root_dir_info.path / amca_conf_fold_name / "plugins"
        if amca_root_dir_info is not None
        else None
    )

    # should_load — only called for enabled plugins
    to_load: list[tuple] = []
    for plugin, pluginname in modules:
        if pluginname not in enabled_plugins:
            continue

        try:
            pl = None
            if plugin_conf_path is not None:
                pl = plugin_conf_path / pluginname
                pl.mkdir(parents=True, exist_ok=True)

            plugin_args = plugin_args_map.get(pluginname, [])
            if plugin.should_load(amca_root_dir_info, pl, working_dir_info, gdp, plugin_args):
                to_load.append((plugin, pluginname, pl))
        except Exception as exc:
            glog.error(f"Error in should_load for '{pluginname}': {exc}")
            if exit_on_error:
                sys.exit(1)

    # load
    for plugin, pluginname, pl in to_load:
        try:
            plugin.load(
                amca_root_dir_info,
                pl,
                working_dir_info,
                gdp,
                plugin_args_map.get(pluginname, []),
            )
            if print_loaded and cf.general_settings.get("debug"):
                glog.success(f"Plugin '{pluginname}' loaded")
        except Exception as exc:
            glog.error(f"Error loading plugin '{pluginname}': {exc}")
            if exit_on_error:
                sys.exit(1)
