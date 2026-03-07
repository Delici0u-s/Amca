# src/impl/amca_pl_impl/enable.py
import impl.util.config.config as cf
from pathlib import Path
from impl.util.globals import global_dir_parser as gdp
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

    if not available_plugins:
        print("No plugins installed!")
        return

    enabled_plugins = [str(p) for p in cf.plugin_settings.get("enabled_plugins") or []]

    # Only show plugins that are not already enabled.
    available_plugins = [p for p in available_plugins if p not in enabled_plugins]

    if not available_plugins:
        print("All plugins are already enabled!")
        return

    print("\nDisabled plugins:")
    while True:
        choice = inquirer.select(
            message="Pick a plugin to enable (or exit):",
            choices=[*available_plugins, "Exit selection"],
        ).execute()

        if choice == "Exit selection":
            break

        enabled_plugins.append(choice)
        available_plugins.remove(choice)

        if not available_plugins:
            print("No more plugins to enable.")
            break

    cf.plugin_settings.set("enabled_plugins", enabled_plugins)
    cf.plugin_settings.save()  # BUG FIX: was missing — changes were never persisted
