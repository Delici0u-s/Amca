from __future__ import annotations

import importlib.util as importlib_util
import inspect
import sys
import types
import uuid
from pathlib import Path
from types import ModuleType
from typing import Any, List, Optional, Union, Tuple

from plugin.plugin_base import Plugin as abstract_plugin
from impl.util.globals import glog


class PluginLoadError(Exception):
    """Raised when a plugin cannot be loaded from a file."""


def _ensure_path_inserted(path_str: str) -> bool:
    """Insert path_str at front of sys.path if not already present. Return True if inserted."""
    if path_str in sys.path:
        return False
    sys.path.insert(0, path_str)
    return True


def _gather_candidate_sys_paths(plugin_dir: Path) -> List[str]:
    plugin_dir = plugin_dir.resolve()
    candidates: List[str] = []

    # plugin dir itself
    candidates.append(str(plugin_dir))

    # include any immediate sub-package dirs to help resolving local imports
    for sub in plugin_dir.iterdir():
        if sub.is_dir():
            candidates.append(str(sub))

    # installed_plugins (parent)
    parent_dir = plugin_dir.parent
    candidates.append(str(parent_dir))

    # walk upwards to find a directory which *looks* like project root (heuristic)
    up = plugin_dir
    for _ in range(6):
        if (up / "src").exists() or (up / "plugin").exists() or (up / "impl").exists():
            candidates.append(str(up))
            break
        if up.parent == up:
            break
        up = up.parent

    # de-duplicate preserving order and ensure path exists
    seen = set()
    ordered: List[str] = []
    for p in candidates:
        if p not in seen and Path(p).exists():
            seen.add(p)
            ordered.append(p)
    return ordered


def _maybe_inject_local_packages(plugin_dir: Path) -> List[str]:
    """
    Inject synthetic package modules for any top-level subdirectories of plugin_dir
    that look like packages (contain init.py) and are not already importable.

    This avoids hard-coding an "impl" name and supports arbitrary package names
    that plugin authors may choose. Returns list of injected package names.
    """
    injected: List[str] = []
    for sub in plugin_dir.iterdir():
        if not sub.is_dir():
            continue
        if (sub / "init.py").exists():
            name = sub.name
            if name in sys.modules:
                continue
            try:
                pkg = types.ModuleType(name)
                pkg.__path__ = [str(sub.resolve())]
                sys.modules[name] = pkg
                injected.append(name)
            except Exception:
                pass
    return injected


def load_module_from_path(
    filepath: Path, module_name: Optional[str] = None
) -> Optional[ModuleType]:
    """
    Load a module from a specific file path. If filepath is an init.py we prefer
    to use the containing folder name as the module name so package-style imports
    (relative and absolute within the package) resolve sensibly.
    """
    module = None
    filepath = filepath.resolve()
    if module_name is None:
        if filepath.name == "init.py":
            module_name = filepath.parent.name
        else:
            module_name = f"amca_plugin_{filepath.stem}_{uuid.uuid4().hex[:8]}"

    try:
        spec = importlib_util.spec_from_file_location(module_name, str(filepath))
        if spec is None or spec.loader is None:
            raise PluginLoadError(f"spec not found or loader missing for {filepath!s}")

        module = importlib_util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)  # type: ignore[attr-defined]
        return module
    except Exception as exc:
        try:
            if module_name in sys.modules and sys.modules[module_name] is module:
                del sys.modules[module_name]
        except Exception:
            pass
        glog.error(f"Failed to load plugin '{module_name}' from '{filepath}': {exc}")
        return None


def find_plugin_classes_by_duck_typing(module: ModuleType) -> List[type]:
    """
    Return classes *defined in module* that implement the plugin API by duck-typing:
    they have callable should_load(...) and load(...).
    """
    results: List[type] = []
    for _, obj in inspect.getmembers(module, inspect.isclass):
        if obj.__module__ != module.__name__:
            continue
        if callable(getattr(obj, "should_load", None)) and callable(
            getattr(obj, "load", None)
        ):
            results.append(obj)
    return results


def find_subclasses_in_module(module: ModuleType, abstract_cls: type) -> List[type]:
    """Return classes defined in module that subclass abstract_cls (ignore imported classes)."""
    subclasses: List[type] = []
    for _, obj in inspect.getmembers(module, inspect.isclass):
        if obj.__module__ != module.__name__:
            continue
        try:
            if issubclass(obj, abstract_cls) and obj is not abstract_cls:
                subclasses.append(obj)
        except TypeError:
            continue
    return subclasses


def _try_instantiate(
    cls: type, plugin_root_info: Any = None, dir_parser: Any = None
) -> Optional[object]:
    """
    Try multiple constructor shapes and return an instance or None.
    Preference: (plugin_root_info, dir_parser) -> (plugin_root_info) -> ()
    """
    try_variants = []
    if plugin_root_info is not None and dir_parser is not None:
        try_variants.append((plugin_root_info, dir_parser))
    if plugin_root_info is not None:
        try_variants.append((plugin_root_info,))
    try_variants.append(tuple())

    for args in try_variants:
        try:
            return cls(*args)
        except TypeError:
            # ctor signature didn't match -> try next
            continue
        except Exception as exc:
            glog.error(f"Instantiation error for {cls!r} with args {args}: {exc}")
            return None
    return None


def _maybe_call_init(module_or_instance: Any) -> None:
    """
    If the module or instance exposes an init/setup function, call it (best-effort).
    Accepts names: 'init', 'initialize', 'setup'.
    """
    for name in ("init", "initialize", "setup"):
        fn = getattr(module_or_instance, name, None)
        if callable(fn):
            try:
                fn()
            except Exception as exc:
                glog.error(f"Error calling {name} on {module_or_instance}: {exc}")
            break


def _derive_plugin_name(candidate: Any, filepath: Path) -> str:
    """
    Determine a plugin name string from various heuristics:
      - PLUGIN_NAME module attribute (if module provided)
      - __plugin_name__ attribute
      - instance attribute 'name' or 'plugin_name'
      - module.__package__ or module.__name__
      - fallback to containing folder name
    """
    # module-level attrs
    try:
        if isinstance(candidate, ModuleType):
            if isinstance(getattr(candidate, "PLUGIN_NAME", None), str):
                return candidate.PLUGIN_NAME
            if isinstance(getattr(candidate, "__plugin_name__", None), str):
                return candidate.__plugin_name__
            if candidate.__package__:
                return candidate.__package__
            return candidate.__name__

        # instance-level attrs
        if hasattr(candidate, "PLUGIN_NAME") and isinstance(
            getattr(candidate, "PLUGIN_NAME"), str
        ):
            return getattr(candidate, "PLUGIN_NAME")
        if hasattr(candidate, "plugin_name") and isinstance(
            getattr(candidate, "plugin_name"), str
        ):
            return getattr(candidate, "plugin_name")
        if hasattr(candidate, "name") and isinstance(getattr(candidate, "name"), str):
            return getattr(candidate, "name")
    except Exception:
        pass

    # fallback to the containing folder name
    return filepath.parent.name


def load_if_valid_module(
    path: Path,
    abstract_cls: type = abstract_plugin,
    plugin_root_info: Any = None,
    dir_parser: Any = None,
) -> Optional[Tuple[Union[ModuleType, object], str]]:
    """
    Load plugin and return either:
      - (module, plugin_name) (if module-level API present), or
      - (instantiated_plugin_object, plugin_name) (if class-based plugin)

    plugin_root_info and dir_parser are optional context objects to pass to plugin constructors.
    """
    plugin_dir = path.parent

    # --- insert candidate sys.path entries ---
    candidate_paths = _gather_candidate_sys_paths(plugin_dir)
    inserted_paths = []
    for p in candidate_paths:
        if _ensure_path_inserted(p):
            inserted_paths.append(p)

    # --- maybe inject synthetic local package modules ---
    injected_packages: List[str] = []
    try:
        injected_packages = _maybe_inject_local_packages(plugin_dir)

        # choose module name preference: if loading an init.py use the folder name
        module_name = None
        if path.name == "init.py":
            module_name = plugin_dir.name

        module = load_module_from_path(path, module_name=module_name)
        if module is None:
            return None

        # 1) module-level API (module.should_load / module.load)
        if callable(getattr(module, "should_load", None)) and callable(
            getattr(module, "load", None)
        ):
            # optional module init hook
            _maybe_call_init(module)
            return module, _derive_plugin_name(module, path)

        # 2) classes that subclass the project's abstract base
        plugin_classes = find_subclasses_in_module(module, abstract_cls)
        if plugin_classes:
            for cls in plugin_classes:
                inst = _try_instantiate(cls, plugin_root_info, dir_parser)
                if (
                    inst is not None
                    and callable(getattr(inst, "should_load", None))
                    and callable(getattr(inst, "load", None))
                ):
                    _maybe_call_init(inst)
                    return inst, _derive_plugin_name(inst, path)
            glog.error(
                f"Found classes subclassing abstract base in {path} but none could be instantiated usable."
            )

        # 3) duck-typed classes defined in module (have should_load/load)
        duck_classes = find_plugin_classes_by_duck_typing(module)
        if duck_classes:
            for cls in duck_classes:
                inst = _try_instantiate(cls, plugin_root_info, dir_parser)
                if (
                    inst is not None
                    and callable(getattr(inst, "should_load", None))
                    and callable(getattr(inst, "load", None))
                ):
                    _maybe_call_init(inst)
                    return inst, _derive_plugin_name(inst, path)
            glog.error(
                f"Found duck-typed plugin classes in {path} but none instantiable."
            )

        # 4) module.PLUGINS list (pre-instantiated)
        maybe_plugins = getattr(module, "PLUGINS", None)
        if isinstance(maybe_plugins, list):
            for candidate in maybe_plugins:
                if callable(getattr(candidate, "should_load", None)) and callable(
                    getattr(candidate, "load", None)
                ):
                    _maybe_call_init(candidate)
                    return candidate, _derive_plugin_name(candidate, path)

        glog.warn(f"No usable plugin found in {path}")
        return None

    finally:
        # keep sys.path and injected modules in place — callers may rely on them
        # If you want to remove injected packages after load, do it explicitly here.
        pass
