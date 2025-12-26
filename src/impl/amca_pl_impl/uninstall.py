import argparse
import impl.util.config.config as cf
from pathlib import Path
from impl.util.dirparse import global_dir_parser as gdp
from InquirerPy import inquirer


def load():
    # Load plugin path
    parser = argparse.ArgumentParser(
        "uninstall option", "used to permanently remove plugins from the system"
    )

    parser.add_argument(
        "-y", "--yes", action="store_true", help="Automatically answer yes to prompts"
    )

    parsed = parser.parse_args()

    try:
        plugin_path = Path(cf.plugin_settings.get("generic.plugin_path"))
    except Exception:
        print(f"Provided plugin_path in {cf.plugin_settings._path} is not valid")
        return

    if not plugin_path.exists():
        print("Plugin path is not available, please ensure the path is valid")
        return

    path_info = gdp.parse_dir(plugin_path)
    available_plugins = path_info.folders
