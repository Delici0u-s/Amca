import impl.util.config.config as cf
from pathlib import Path
from impl.util.globals import global_dir_parser as gdp
from InquirerPy import inquirer


def load(*, plugins: list[str] | None = None) -> list[str]:
    """
    Disable one or more plugins.

    Args:
        plugins: List of plugin names to disable. When None, uses TUI.

    Returns:
        The updated list of enabled plugin names.
    """
    try:
        plugin_path = Path(cf.plugin_settings.get("generic.plugin_path"))
    except Exception:
        print(f"Provided plugin_path in {cf.plugin_settings._path} is not valid")
        return []

    if not plugin_path.exists():
        print("Plugin path is not available, please ensure the path is valid")
        return []

    enabled_plugins = [str(p) for p in cf.plugin_settings.get("enabled_plugins") or []]

    if not enabled_plugins:
        print("No plugins are currently enabled!")
        return []

    # Non-interactive path
    if plugins is not None:
        for p in plugins:
            if p not in enabled_plugins:
                print(f"Plugin '{p}' is not enabled — skipping")
                continue
            enabled_plugins.remove(p)
        cf.plugin_settings.set("enabled_plugins", enabled_plugins)
        cf.plugin_settings.save()
        return enabled_plugins

    # Interactive TUI path
    print("\nEnabled Plugins:")
    while True:
        choice = inquirer.select(
            message="Pick a plugin to disable (or exit selection):",
            choices=[*enabled_plugins, "Exit selection"],
        ).execute()

        if choice == "Exit selection":
            break

        enabled_plugins.remove(choice)

        if not enabled_plugins:
            print("No more plugins to disable.")
            break

    cf.plugin_settings.set("enabled_plugins", enabled_plugins)
    cf.plugin_settings.save()
    return enabled_plugins
