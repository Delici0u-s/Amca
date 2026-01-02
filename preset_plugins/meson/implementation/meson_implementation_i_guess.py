from plugin.dirparse import DirInfo, DirParser


def run(meson_root_dir_info: DirInfo, dir_parser: DirParser, args: list[str]):
    print("Meson directory detected")
