import impl.util.config.config as cf
from pathlib import Path
from impl.util.globals import global_dir_parser as gdp


def load():
    # Load plugin path
    try:
        plugin_path = Path(cf.plugin_settings.get("generic.plugin_path"))
    except Exception:
        print(f"Provided plugin_path in {cf.plugin_settings._path} is not valid")
        return

    if not plugin_path.exists():
        print("Plugin path is not available, please ensure the path is valid")
        return

    path_info = gdp.parse_dir(plugin_path)
    all_plugins = [str(p) for p in path_info.folders]
    enabled_plugins = set(cf.plugin_settings.get("enabled_plugins") or [])

    if not all_plugins:
        print("No plugins available in the plugin path!")
        return

    print("Installed plugins:\n")

    for plugin in all_plugins:
        status = "ENABLED" if plugin in enabled_plugins else "disabled"
        print(f" - {plugin} [{status}]")
