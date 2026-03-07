from impl.plugin_base import *


class any(Plugin):

    def should_load(
        self,
        amca_root_dir: Optional[DirInfo], # directory inwhich amca_root.folder_name lies (if it doesnt exists this is none)
        amca_root_plugin_dir: Optional[Path], # designated plugin "config" folder: "amca_root_dir.path / amca_root.folder_name / plugins / plugin_name"
        working_dir: DirInfo, # dir inwhich amca was called
        dir_parser: DirParser, # dirparser to get info on files and folders in filepath with dir_parese.parse_dir
    ) -> bool:
        return True

    def load(
        self,
        amca_root_dir: Optional[DirInfo],
        amca_root_plugin_dir: Optional[Path],
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
