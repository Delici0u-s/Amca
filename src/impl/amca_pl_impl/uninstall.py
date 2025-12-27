import argparse
import shutil
import impl.util.config.config as cf
from pathlib import Path
from impl.util.dirparse import global_dir_parser as gdp
from InquirerPy import inquirer


def load():
    # Argument parsing
    parser = argparse.ArgumentParser(
        description="Used to permanently remove plugins from the system"
    )
    parser.add_argument(
        "-y", "--yes", action="store_true", help="Automatically answer yes to prompts"
    )
    parsed = parser.parse_args()

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

    if not all_plugins:
        print("No plugins available in the plugin path!")
        return

    # Get currently enabled plugins
    enabled_plugins = [str(p) for p in cf.plugin_settings.get("enabled_plugins") or []]

    while True:
        # Display all plugins
        choices = [
            f"{p} {'(enabled)' if p in enabled_plugins else ''}" for p in all_plugins
        ]
        choices.append("Exit selection")

        choice = inquirer.select(
            message="Pick a plugin to uninstall:",
            choices=choices,
        ).execute()

        if choice == "Exit selection":
            break

        plugin_name = choice.split()[0]  # Extract folder name

        # Confirm uninstall unless -y is passed
        if not parsed.yes:
            confirm = inquirer.confirm(
                message=f"Are you sure you want to uninstall '{plugin_name}'? This cannot be undone."
            ).execute()
            if not confirm:
                continue

        plugin_folder = plugin_path / plugin_name

        if plugin_folder.exists():
            try:
                shutil.rmtree(plugin_folder)
                print(f"Plugin '{plugin_name}' has been uninstalled.")
            except Exception as e:
                print(f"Failed to remove plugin '{plugin_name}': {e}")
        else:
            print(f"Plugin '{plugin_name}' folder does not exist, skipping.")

        # Remove from enabled list if present
        if plugin_name in enabled_plugins:
            enabled_plugins.remove(plugin_name)
            cf.plugin_settings.set("enabled_plugins", enabled_plugins)
            cf.plugin_settings.save()

        # Update all_plugins list for next iteration
        all_plugins = [p for p in all_plugins if p != plugin_name]

        if not all_plugins:
            print("All plugins have been uninstalled!")
            break

    print("Plugin uninstall process complete!")
