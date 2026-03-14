import impl.util.config.config as cf
from pathlib import Path
from impl.util.globals import global_dir_parser as gdp
from InquirerPy import inquirer


def load(*, plugins: list[str] | None = None) -> list[str]:
    """
    Toggle enabled/disabled state for plugins.

    Args:
        plugins: List of plugin names to toggle. When None, uses TUI.

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

    path_info = gdp.parse_dir(plugin_path)
    all_plugins = [str(p) for p in path_info.folders]
    enabled_plugins = [str(p) for p in cf.plugin_settings.get("enabled_plugins") or []]

    if not all_plugins:
        print("No plugins available in the plugin path!")
        return enabled_plugins

    # Non-interactive path
    if plugins is not None:
        for p in plugins:
            if p not in all_plugins:
                print(f"Plugin '{p}' not found — skipping")
                continue
            if p in enabled_plugins:
                enabled_plugins.remove(p)
            else:
                enabled_plugins.append(p)
        cf.plugin_settings.set("enabled_plugins", enabled_plugins)
        cf.plugin_settings.save()
        return enabled_plugins

    # Interactive TUI path
    print("Available plugins")
    last_index = 0

    while True:
        choices = [f"[{'X' if p in enabled_plugins else ' '}] {p}" for p in all_plugins]
        choices.append("Exit selection")

        choice = inquirer.select(
            message="Toggle plugins (X = enabled):",
            choices=choices,
            default=choices[last_index],
        ).execute()

        if choice == "Exit selection":
            break

        last_index = choices.index(choice)
        plugin_name = choice[4:]

        if plugin_name in enabled_plugins:
            enabled_plugins.remove(plugin_name)
        else:
            enabled_plugins.append(plugin_name)

    cf.plugin_settings.set("enabled_plugins", enabled_plugins)
    cf.plugin_settings.save()
    return enabled_plugins
