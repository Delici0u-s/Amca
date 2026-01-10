from impl.amca.plugin_base import *
import impl.meson_implementation_i_guess as impl


class meson(Plugin):

    def should_load(
        self,
        amca_root_dir: Optional[DirInfo],
        working_dir: DirInfo,
        dir_parser: DirParser,
    ) -> bool:

        dir_inf = working_dir if amca_root_dir is None else amca_root_dir

        return "meson.build" in dir_inf.files

    def load(
        self,
        amca_root_dir: Optional[DirInfo],
        working_dir: DirInfo,
        dir_parser: DirParser,
        args: list[str],
    ) -> None:

        dir_inf = working_dir if amca_root_dir is None else amca_root_dir

        impl.run(dir_inf, dir_parser, args)
