from impl.amca.plugin_base import *
import impl.meson_implementation_i_guess as impl


class meson(Plugin):

    def should_load(
        self,
        amca_root_dir: Optional[DirInfo],
        working_dir: DirInfo,
        dir_parser: DirParser,
    ) -> bool:

        if amca_root_dir is None:
            self.meson_root_info = working_dir
        else:
            self.meson_root_info = amca_root_dir

        return "meson.build" in self.meson_root_info.files

    def load(
        self,
        amca_root_dir: Optional[DirInfo],
        working_dir: DirInfo,
        dir_parser: DirParser,
        args: list[str],
    ) -> None:
        impl.run(self.meson_root_info, dir_parser, args)
