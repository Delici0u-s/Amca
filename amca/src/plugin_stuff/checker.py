from __future__ import annotations

import importlib.util as importlib_util
import inspect
import sys
import warnings
from pathlib import Path
from types import ModuleType
from typing import Iterable, List, Optional, Set, Tuple
from src.util.settings import Settings

from src.util.log import glog

# Only import Plugin for type-checking to avoid runtime import issues if package layout differs.
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from plugins.amca_abstract_plugin.abstract_plugin import Plugin  # type: ignore


class PluginLoadError(Exception):
    """Raised when a plugin cannot be loaded from a file."""

    pass


def load_module_from_path(filepath: Path, module_name: str) -> Optional[ModuleType]:
    """
    Load a Python file as a module given its full path.

    Parameters
    ----------
    filepath
        Full path to the .py file to import.
    module_name
        Name to assign to the imported module (should be unique).

    Returns
    -------
    ModuleType | None
        The imported module, or None on failure.
    """
    try:
        spec = importlib_util.spec_from_file_location(module_name, str(filepath))
        if spec is None or spec.loader is None:
            raise PluginLoadError(f"spec not found for {filepath!s}")

        module = importlib_util.module_from_spec(spec)
        # make available for intra-plugin imports
        sys.modules[module_name] = module
        spec.loader.exec_module(module)  # type: ignore[attr-defined]
        return module
    except Exception as exc:
        # Keep error message clear but do not crash the caller
        glog.error(f"Failed to load plugin '{module_name}' from '{filepath}': {exc}")
        return None


def find_plugin_classes(module: ModuleType) -> List[type]:
    """
    Return classes defined in `module` that implement both `matches` and `load`.

    We only consider classes declared in the module itself to avoid imported base classes.
    """
    plugin_classes: List[type] = []
    for _, obj in inspect.getmembers(module, inspect.isclass):
        if obj.__module__ != module.__name__:
            # ignore imported classes
            continue
        if callable(getattr(obj, "matches", None)) and callable(
            getattr(obj, "load", None)
        ):
            plugin_classes.append(obj)
    return plugin_classes


def _normalize_active_plugins(active_plugins: Iterable[str]) -> Set[str]:
    """
    Normalize plugin names in `active_plugins` to filenames ending with '.py'.

    Examples: 'git' -> 'git.py', 'git.py' -> 'git.py'
    """
    return {p if p.endswith(".py") else f"{p}.py" for p in active_plugins}


def check_plugins(
    s: Settings,
    filepath: Path,
    filenames: Iterable[str],
    dirnames: Iterable[str],
) -> Set[Tuple["Plugin", str]]:
    """
    Load, inspect and instantiate active plugins found in plugin paths.

    - Only .py files are considered.
    - Does NOT call plugin.load(...) (per requirement).
    - Calls plugin.matches(...) and returns instantiated plugins whose
      matches(...) returned True.
    - Emits a RuntimeWarning for any active plugin not found in any plugin path.

    Parameters
    ----------
    s
        Settings object providing 'plugin_config.plugin_paths' and
        'plugin_config.active_plugins'.
    filepath
        The path being inspected (forwarded to plugin.matches).
    filenames
        Filenames (forwarded to plugin.matches) — the abstract API expects sets.
    dirnames
        Directory names (forwarded to plugin.matches) — the abstract API expects sets.

    Returns
    -------
    Set[Tuple[Plugin, str]]
        Set of tuples (plugin_instance, plugin_filename) for plugins that matched.
    """
    plugin_paths: List[str] = list(s.get("plugin_config.plugin_paths", []))
    active_plugins_raw: Set[str] = set(s.get("plugin_config.active_plugins", []))

    normalized_active: Set[str] = _normalize_active_plugins(active_plugins_raw)
    found_active_files: Set[str] = set()
    loaded_instances: Set[Tuple["Plugin", str]] = set()

    # Pre-convert filenames/dirnames to sets as per your abstract Plugin signature
    filenames_set: Set[str] = set(filenames)
    dirnames_set: Set[str] = set(dirnames)

    # Quick exit if nothing to do
    if not plugin_paths or not normalized_active:
        missing = normalized_active
        if missing:
            warnings.warn(
                f"No plugin paths configured; active plugins {sorted(missing)} not found.",
                RuntimeWarning,
            )
        return loaded_instances

    for plugin_path_str in plugin_paths:
        plugin_dir = Path(plugin_path_str)
        if not plugin_dir.exists() or not plugin_dir.is_dir():
            glog.warn(f"plugin path not found or not a dir: {plugin_dir!s}")
            continue

        # Ensure plugin imports that reference package roots succeed
        parent_dir = str(plugin_dir.resolve().parent)
        plugin_dir_str = str(plugin_dir.resolve())
        if parent_dir not in sys.path:
            sys.path.insert(0, parent_dir)
        if plugin_dir_str not in sys.path:
            sys.path.insert(0, plugin_dir_str)

        # iterate directory entries (fast; generators, avoids building large lists)
        try:
            for entry in plugin_dir.iterdir():
                if not entry.is_file():
                    continue
                if entry.suffix != ".py":
                    continue

                filename = entry.name
                if filename not in normalized_active:
                    continue

                # mark that we found this active plugin file
                found_active_files.add(filename)

                # unique module name to reduce collision risk
                module_name = f"amca_plugin_{entry.stem}"

                module = load_module_from_path(entry, module_name)
                if module is None:
                    # error already reported in loader; skip this file
                    continue

                plugin_classes = find_plugin_classes(module)
                if not plugin_classes:
                    glog.error(f"No plugin classes found in {filename}")
                    continue

                for cls in plugin_classes:
                    try:
                        instance = cls()  # instantiate plugin
                    except Exception as exc:
                        glog.error(
                            f"Failed to instantiate {cls.__name__} from {filename}: {exc}"
                        )
                        continue

                    # call matches only (do NOT call load)
                    try:
                        if instance.matches(filepath, filenames_set, dirnames_set):
                            loaded_instances.add((instance, filename))
                    except Exception as exc:
                        glog.error(
                            f"Error while running matches() of plugin {cls.__name__} "
                            f"from {filename}: {exc}"
                        )
        except PermissionError as exc:
            glog.error(f"Permission denied while scanning {plugin_dir}: {exc}")
            continue

    # Emit a runtime warning for any active plugin not discovered
    missing_plugins = normalized_active - found_active_files
    if missing_plugins:
        glog.warn(
            f"Active plugins not found in plugin paths: {sorted(missing_plugins)}"
        )

    # return set of (plugin_instance, filename)
    return loaded_instances
