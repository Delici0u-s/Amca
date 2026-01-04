import impl.util.config.config as cf
from pathlib import Path
from impl.util.globals import global_dir_parser as gdp
from InquirerPy import inquirer


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
    available_plugins = [str(p) for p in path_info.folders]

    if not available_plugins:
        print("No plugins installed!")
        return

    # Get enabled plugins
    enabled_plugins = [str(p) for p in cf.plugin_settings.get("enabled_plugins") or []]

    # Remove already enabled plugins from available list
    available_plugins = [p for p in available_plugins if p not in enabled_plugins]

    if not available_plugins:
        print("All plugins are already enabled!")
        return

    print("\ndisabled Plugins:")
    # Interactive selection loop
    while True:
        choice = inquirer.select(
            message="Pick a plugin to enable (or exit selection):",
            choices=[*available_plugins, "Exit selection"],
        ).execute()

        if choice == "Exit selection":
            break

        # Update enabled and available lists
        enabled_plugins.append(choice)
        available_plugins.remove(choice)

        # print(f"Enabled plugins: {enabled_plugins}")
        if not available_plugins:
            print("No more plugins to enable.")
            break

    # Optionally, save enabled_plugins back to config
    cf.plugin_settings.set("enabled_plugins", enabled_plugins)
