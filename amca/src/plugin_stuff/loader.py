from __future__ import annotations

import importlib.util as importlib_util
import inspect
import sys
import warnings
from pathlib import Path
from types import ModuleType
from typing import Iterable, List, Optional, Set, Tuple
from src.util.settings import Settings

# Only import Plugin for type-checking to avoid runtime import issues if package layout differs.
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from plugins.amca_abstract_plugin.abstract_plugin import Plugin  # type: ignore


def load_plugins(
    s: Settings,
    filepath: Path,
    filenames: set[str],
    dirnames: set[str],
    active_plugins: Set[Tuple["Plugin", str]],
):
    for pl in active_plugins:
        pl[0].load(filepath, filenames, dirnames)
