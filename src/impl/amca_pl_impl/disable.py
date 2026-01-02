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
    all_plugins = [str(p) for p in path_info.folders]

    # Get enabled plugins
    enabled_plugins = [str(p) for p in cf.plugin_settings.get("enabled_plugins") or []]

    if not enabled_plugins:
        print("No plugins are currently enabled!")
        return

    print("\nEnabled Plugins:")
    # Interactive selection loop
    while True:
        choice = inquirer.select(
            message="Pick a plugin to disable (or exit selection):",
            choices=[*enabled_plugins, "Exit selection"],
        ).execute()

        if choice == "Exit selection":
            break

        # Update enabled plugins list
        enabled_plugins.remove(choice)
        all_plugins.append(choice)  # optional if you want to show it again as available

        if not enabled_plugins:
            print("No more plugins to disable.")
            break

    # Save updated enabled_plugins back to config
    cf.plugin_settings.set("enabled_plugins", enabled_plugins)
    cf.plugin_settings.save()
