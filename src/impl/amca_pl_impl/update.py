"""
amcapl update — re-download installed plugins from their sources.

Since sources carry no version metadata, "update" means: for each selected
plugin, delete the on-disk folder and re-download from the first source that
provides it.  The enabled/disabled state is preserved.
"""
import shutil
import impl.util.config.config as cf
from pathlib import Path
from impl.util.globals import global_dir_parser as gdp
from impl.util import github
from InquirerPy import inquirer


def _find_and_download(plugin_name: str, plugin_path: Path, sources: list) -> bool:
    # print("''''''''''''''''''''''''''''''''''''##")
    # print(sources)
    # print("''''''''''''''''''''''''''''''''''''##")
    """Re-download plugin_name from the first matching source. Returns True on success."""
    for source in sources:
        if isinstance(source, str) and source.startswith("https://api.github.com/"):
            base = source.split("?ref=")[0] if "?ref=" in source else source
            branch = source.split("?ref=")[1] if "?ref=" in source else "main"
            api_url = f"{base}/{plugin_name}?ref={branch}"
            print(api_url)
            try:
                github.download_github_folder(api_url=api_url, local_dir=str(plugin_path / plugin_name))
                return True
            except Exception as e:
                print(f"  [github url] failed: {e}")
                continue

        if isinstance(source, dict):
            src_type = source.get("type", "github")

            if src_type == "local":
                src_folder = Path(source.get("path", "")) / plugin_name
                if src_folder.exists():
                    try:
                        shutil.copytree(str(src_folder), str(plugin_path / plugin_name))
                        return True
                    except Exception as e:
                        print(f"  [local] copy failed: {e}")
                continue

            path = source.get("path", "")
            full_path = f"{path}/{plugin_name}".strip("/")
            try:
                github.download_github_folder(
                    owner=source.get("owner"),
                    repo=source.get("repo"),
                    branch=source.get("branch", "main"),
                    path=full_path,
                    local_dir=str(plugin_path / plugin_name),
                )
                return True
            except Exception as e:
                print(f"  [github dict] failed: {e}")
                continue

    return False


def _update_one(plugin_name: str, plugin_path: Path, sources: list) -> bool:
    plugin_folder = plugin_path / plugin_name
    print(f"Updating '{plugin_name}'...")

    if plugin_folder.exists():
        try:
            shutil.rmtree(plugin_folder)
        except Exception as e:
            print(f"  Could not remove existing folder: {e}")
            return False

    if _find_and_download(plugin_name, plugin_path, sources):
        print(f"  ✓ '{plugin_name}' updated successfully")
        return True
    else:
        print(f"  ✗ '{plugin_name}' not found in any source — left removed")
        return False


def load(*, plugins: list[str] | None = None) -> None:
    """
    Update (re-download) installed plugins.

    Args:
        plugins: List of plugin names to update. When None, uses TUI.
                 Pass ["*"] or an empty list with all=True to update all.
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

    if not installed_plugins:
        print("No plugins installed — nothing to update.")
        return

    sources = cf.plugin_settings.get("plugin_sources") or []
    if not sources:
        print("No plugin sources configured — cannot update.")
        return

    # Non-interactive path
    if plugins is not None:
        to_update = installed_plugins if plugins == ["*"] else plugins
        for p in to_update:
            if p not in installed_plugins:
                print(f"Plugin '{p}' is not installed — skipping")
                continue
            _update_one(p, plugin_path, sources)
        return

    # Interactive TUI path
    choices = [*installed_plugins, "— Update ALL —", "Exit selection"]
    choice = inquirer.select(
        message="Pick a plugin to update (or update all):",
        choices=choices,
    ).execute()

    if choice == "Exit selection":
        return

    if choice == "— Update ALL —":
        for p in installed_plugins:
            _update_one(p, plugin_path, sources)
        return

    _update_one(choice, plugin_path, sources)
