import shutil
import impl.util.config.config as cf
from pathlib import Path
from InquirerPy import inquirer
from impl.util import github
from impl.util.globals import global_dir_parser as gdp


def _list_source(source) -> list[str]:
    """Return folder names available from a single source entry."""
    if isinstance(source, str) and source.startswith("https://api.github.com/"):
        contents = github.list_github_contents(api_url=source)
        return [item["name"] for item in contents if item["type"] == "dir"]

    if isinstance(source, dict):
        src_type = source.get("type", "github")

        if src_type == "local":
            local_path = Path(source.get("path", ""))
            if local_path.is_dir():
                return [d.name for d in local_path.iterdir() if d.is_dir()]
            return []

        # Default: GitHub dict source
        contents = github.list_github_contents(
            owner=source.get("owner"),
            repo=source.get("repo"),
            branch=source.get("branch", "main"),
            path=source.get("path", ""),
        )
        return [item["name"] for item in contents if item["type"] == "dir"]

    return []


def _download_plugin(choice: str, plugin_path: Path, sources: list, installed_plugins: list[str]) -> bool:
    """Download plugin from the first source that provides it. Returns True on success."""
    for source in sources:
        if isinstance(source, str) and source.startswith("https://api.github.com/"):
            base = source.split("?ref=")[0] if "?ref=" in source else source
            branch = source.split("?ref=")[1] if "?ref=" in source else "main"
            api_url = f"{base}/{choice}?ref={branch}"
            try:
                github.download_github_folder(api_url=api_url, local_dir=str(plugin_path / choice))
                return True
            except Exception as e:
                print(f"Download failed from GitHub URL source: {e}")
                continue

        if isinstance(source, dict):
            src_type = source.get("type", "github")

            if src_type == "local":
                src_folder = Path(source.get("path", "")) / choice
                if src_folder.exists():
                    try:
                        shutil.copytree(str(src_folder), str(plugin_path / choice))
                        return True
                    except Exception as e:
                        print(f"Copy failed from local source: {e}")
                continue

            # GitHub dict source
            path = source.get("path", "")
            full_path = f"{path}/{choice}".strip("/")
            try:
                github.download_github_folder(
                    owner=source.get("owner"),
                    repo=source.get("repo"),
                    branch=source.get("branch", "main"),
                    path=full_path,
                    local_dir=str(plugin_path / choice),
                )
                return True
            except Exception as e:
                print(f"Download failed from GitHub dict source: {e}")
                continue

    return False


def load(*, plugins: list[str] | None = None) -> None:
    """
    Install (download + enable) plugins from configured sources.

    Args:
        plugins: List of plugin names to install. When None, uses TUI.
                 Plugins already on disk are enabled without re-downloading.
    """
    try:
        plugin_path = Path(cf.plugin_settings.get("generic.plugin_path"))
    except Exception:
        print(f"Provided plugin_path in {cf.plugin_settings._path} is not valid")
        return

    if not plugin_path.exists():
        print("Plugin path is not available, please ensure the path is valid")
        return

    path_info = gdp.parse_dir(plugin_path)
    installed_plugins = [str(p) for p in path_info.folders]
    enabled_plugins = [str(p) for p in cf.plugin_settings.get("enabled_plugins") or []]
    sources = cf.plugin_settings.get("plugin_sources") or []

    # Build list of available (not yet installed) plugins from all sources
    available_plugins = [p for p in installed_plugins if p not in enabled_plugins]
    for source in sources:
        for name in _list_source(source):
            if name not in installed_plugins and name not in available_plugins:
                available_plugins.append(name)

    # Non-interactive path
    if plugins is not None:
        for choice in plugins:
            if choice not in installed_plugins:
                if not _download_plugin(choice, plugin_path, sources, installed_plugins):
                    print(f"Could not find '{choice}' in any source — skipping")
                    continue
                installed_plugins.append(choice)
            if choice not in enabled_plugins:
                enabled_plugins.append(choice)
        cf.plugin_settings.set("enabled_plugins", enabled_plugins)
        cf.plugin_settings.save()
        return

    # Interactive TUI path
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

        if choice not in installed_plugins:
            if not _download_plugin(choice, plugin_path, sources, installed_plugins):
                print(f"Failed to download '{choice}' from any source.")
                continue
            installed_plugins.append(choice)

        enabled_plugins.append(choice)
        available_plugins.remove(choice)

        if not available_plugins:
            print("No more plugins to download/enable.")
            break

    cf.plugin_settings.set("enabled_plugins", enabled_plugins)
    cf.plugin_settings.save()
