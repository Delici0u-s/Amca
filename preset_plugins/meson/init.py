from impl.plugin_base import Plugin, DirInfo, DirParser


class meson(Plugin):
    def should_load(
        self,
        amca_root_dir: DirInfo,
        working_dir: DirInfo,
        dir_parser: DirParser,
    ) -> bool:
        return "meson.build" in amca_root_dir.files

    def load(
        self,
        amca_root_dir: DirInfo,
        working_dir: DirInfo,
        dir_parser: DirParser,
        args: list[str],
    ) -> None:
        print("meson plugin loaded, with args ", args)
        ...  # todo lmao
