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

    enabled_plugins = [str(p) for p in cf.plugin_settings.get("enabled_plugins") or []]

    if not all_plugins:
        print("No plugins available in the plugin path!")
        return

    print("Available plugins")

    last_index = 0  # Track the last cursor position

    while True:
        # Build choices with enabled/disabled mark
        choices = [f"[{'X' if p in enabled_plugins else ' '}] {p}" for p in all_plugins]
        choices.append("Exit selection")

        choice = inquirer.select(
            message="Toggle plugins (X = enabled):",
            choices=choices,
            default=choices[last_index],  # Keep cursor at last selected
        ).execute()

        if choice == "Exit selection":
            break

        # Update last_index to the index of selected item
        last_index = choices.index(choice)

        # Extract plugin name from choice string
        plugin_name = choice[4:]

        # Toggle plugin
        if plugin_name in enabled_plugins:
            enabled_plugins.remove(plugin_name)
        else:
            enabled_plugins.append(plugin_name)

    # Save changes
    cf.plugin_settings.set("enabled_plugins", enabled_plugins)
    cf.plugin_settings.save()
