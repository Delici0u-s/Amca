from amca_abstract_plugin.abstract_plugin import *


class any_plugin(Plugin):
    def __init__(self):
        pass

    @override
    def matches(
        self,
        filepath: Path,
        filenames: set[str],
        dirnames: set[str],
    ) -> bool:
        return True

    @override
    def load(
        self,
        filepath: Path,
        filenames: set[str],
        dirnames: set[str],
    ) -> None:
        print("Any Plugin Loaded")
