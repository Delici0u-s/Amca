# impl/amca_pl_impl/uninstall.py
import shutil
import impl.util.config.config as cf
from pathlib import Path
from impl.util.globals import global_dir_parser as gdp
from InquirerPy import inquirer


def load(*, plugins: list[str] | None = None, yes: bool = False) -> None:
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

    # Non-interactive path
    if plugins:
        for plugin_name in plugins:
            if plugin_name not in all_plugins:
                print(f"Plugin '{plugin_name}' is not installed — skipping")
                continue
            if not yes:
                confirm = inquirer.confirm(
                    message=f"Uninstall '{plugin_name}'? This cannot be undone."
                ).execute()
                if not confirm:
                    continue
            plugin_folder = plugin_path / plugin_name
            try:
                shutil.rmtree(plugin_folder)
                print(f"Plugin '{plugin_name}' has been uninstalled.")
            except Exception as e:
                print(f"Failed to remove '{plugin_name}': {e}")
                continue
            if plugin_name in enabled_plugins:
                enabled_plugins.remove(plugin_name)
        cf.plugin_settings.set("enabled_plugins", enabled_plugins)
        cf.plugin_settings.save()
        return

    # Interactive TUI path
    while True:
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

        plugin_name = choice.split()[0]

        if not yes:
            confirm = inquirer.confirm(
                message=f"Uninstall '{plugin_name}'? This cannot be undone."
            ).execute()
            if not confirm:
                continue

        plugin_folder = plugin_path / plugin_name
        try:
            shutil.rmtree(plugin_folder)
            print(f"Plugin '{plugin_name}' has been uninstalled.")
        except Exception as e:
            print(f"Failed to remove '{plugin_name}': {e}")

        if plugin_name in enabled_plugins:
            enabled_plugins.remove(plugin_name)
            cf.plugin_settings.set("enabled_plugins", enabled_plugins)
            cf.plugin_settings.save()

        all_plugins = [p for p in all_plugins if p != plugin_name]
        if not all_plugins:
            print("All plugins have been uninstalled!")
            break

    print("Plugin uninstall process complete!")
