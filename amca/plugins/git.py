from amca_abstract_plugin.abstract_plugin import *


class git_plugin(Plugin):
    def __init__(self):
        pass

    @override
    def matches(
        self,
        filepath: Path,
        filenames: set[str],
        dirnames: set[str],
    ) -> bool:
        return ".git" in dirnames

    @override
    def load(
        self,
        filepath: Path,
        filenames: set[str],
        dirnames: set[str],
    ) -> None:
        print("Git Plugin Loaded")
