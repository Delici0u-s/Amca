from impl.amca.plugin_base import *
import importlib
from impl.version_implementations import VERSION_MAP, meson_get_val


class meson(Plugin):

    def should_load(
        self,
        amca_root_dir: Optional[DirInfo], # directory inwhich amca_root.folder_name lies (if it doesnt exists this is none)
        amca_root_plugin_dir: Optional[Path], # designated plugin "config" folder: "amca_root_dir.path / amca_root.folder_name / plugins / plugin_name"
        working_dir: DirInfo, # dir inwhich amca was called
        dir_parser: DirParser, # dirparser to get info on files and folders in filepath with dir_parese.parse_dir
        args: list[str],
    ) -> bool:

        # dir_inf = working_dir
        # dir_inf = working_dir if amca_root_plugin_dir is None else dir_parser.parse_dir(amca_root_plugin_dir.path.parent.parent.parent)
        dir_inf = working_dir if amca_root_dir is None else amca_root_dir

        return "meson.build" in dir_inf.files

    def load(
        self,
        amca_root_dir: Optional[DirInfo],
        amca_root_plugin_dir: Optional[Path],
        working_dir: DirInfo,
        dir_parser: DirParser,
        args: list[str],
    ) -> None:

        dir_inf = working_dir if amca_root_dir is None else amca_root_dir

        # print(amca_root_plugin_dir)
        # print(amca_root_dir.path if amca_root_dir is not None else None)
        # print(working_dir.path)

        meson_file = dir_inf.path / "meson.build"

        # behaviour checking
        meson_version = meson_get_val(meson_file, "amca_var__meson__version_behaviour")
        mapped_version_interpretation = VERSION_MAP.get(meson_version, None)

        if mapped_version_interpretation is None:
            print(f"The given meson version '{meson_version}' is not supported by the amca meson plugin!")
        else:
            module_path = "impl.version_implementations." + str(mapped_version_interpretation)
            version = importlib.import_module(module_path)
            version.evaluate(meson_file, dir_inf, amca_root_plugin_dir, dir_parser, args, working_dir)

