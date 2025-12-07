from amca_abstract_plugin.abstract_plugin import *
import sys


class meson_plugin(Plugin):
    def __init__(self):
        pass

    @override
    def matches(
        self,
        filepath: Path,
        filenames: set[str],
        dirnames: set[str],
    ) -> bool:
        return "meson.build" in filenames

    @override
    def load(
        self,
        filepath: Path,
        filenames: set[str],
        dirnames: set[str],
    ) -> None:
        print(f"Meson Plugin Loaded in {filepath} with {filenames}")
        print(f"Args: {sys.argv}")
