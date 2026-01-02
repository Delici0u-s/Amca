import impl.util.config.config as cf
from pathlib import Path
from InquirerPy import inquirer
from impl.util import github  # your github.py
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

    # Use gdp to get installed plugins (on disk)
    path_info = gdp.parse_dir(plugin_path)
    installed_plugins = [str(p) for p in path_info.folders]

    # Get enabled plugins from config
    enabled_plugins = [str(p) for p in cf.plugin_settings.get("enabled_plugins") or []]

    # Plugins that exist on disk but are not enabled
    available_plugins = [p for p in installed_plugins if p not in enabled_plugins]

    # Add plugins from GitHub sources
    sources = cf.plugin_settings.get("plugin_sources") or []
    for source in sources:
        if isinstance(source, str) and source.startswith("https://api.github.com/"):
            contents = github.list_github_contents(api_url=source)
        elif isinstance(source, dict):
            contents = github.list_github_contents(
                owner=source.get("owner"),
                repo=source.get("repo"),
                branch=source.get("branch", "main"),
                path=source.get("path", ""),
            )
        else:
            continue

        remote_folders = [item["name"] for item in contents if item["type"] == "dir"]
        # Only include remote plugins not already installed
        for f in remote_folders:
            if f not in installed_plugins:
                available_plugins.append(f)

    if not available_plugins:
        print("No new plugins available to download or enable!")
        return

    print("\nAvailable Plugins:")
    while True:
        choice = inquirer.select(
            message="Pick a plugin to download/enable (or exit selection):",
            choices=[*available_plugins, "Exit selection"],
        ).execute()

        if choice == "Exit selection":
            break

        # Download plugin if it does not exist on disk
        # Download plugin if it does not exist on disk
        if choice not in installed_plugins:
            for source in sources:
                if isinstance(source, str) and source.startswith(
                    "https://api.github.com/"
                ):
                    # Fix URL construction
                    if "?ref=" in source:
                        base, query = source.split("?ref=")
                        branch = query
                    else:
                        base = source
                        branch = "main"

                    api_url = f"{base}/{choice}?ref={branch}"
                    github.download_github_folder(
                        api_url=api_url, local_dir=plugin_path / choice
                    )
                    break

                elif isinstance(source, dict):
                    path = source.get("path", "")
                    full_path = f"{path}/{choice}".strip("/")
                    github.download_github_folder(
                        owner=source.get("owner"),
                        repo=source.get("repo"),
                        branch=source.get("branch", "main"),
                        path=full_path,
                        local_dir=plugin_path / choice,
                    )
                    break

        # Update enabled and available lists
        enabled_plugins.append(choice)
        available_plugins.remove(choice)
        installed_plugins.append(choice)  # now exists on disk

        if not available_plugins:
            print("No more plugins to download/enable.")
            break

    # Save enabled_plugins back to config
    cf.plugin_settings.set("enabled_plugins", enabled_plugins)
