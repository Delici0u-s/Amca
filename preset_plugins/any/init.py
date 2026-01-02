from impl.plugin_base import *


class any(Plugin):

    def should_load(
        self,
        amca_root_dir: Optional[DirInfo],
        working_dir: DirInfo,
        dir_parser: DirParser,
    ) -> bool:
        return True

    def load(
        self,
        amca_root_dir: Optional[DirInfo],
        working_dir: DirInfo,
        dir_parser: DirParser,
        args: list[str],
    ) -> None:
        msg: str = "Any plugin loaded"
        if len(args) > 0:
            msg += " with args: "
        for arg in args:
            msg += f" '{arg}'"

        print(msg)
