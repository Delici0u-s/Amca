from impl.plugin_base import Plugin, DirInfo, DirParser


class any(Plugin):
    def should_load(
        self,
        amca_root_dir: DirInfo,
        working_dir: DirInfo,
        dir_parser: DirParser,
    ) -> bool:
        return True

    def load(
        self,
        amca_root_dir: DirInfo,
        working_dir: DirInfo,
        dir_parser: DirParser,
        args: list[str],
    ) -> None:
        print("Any plugin loaded")
