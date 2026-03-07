import argparse
from ...amca.dirparse import DirInfo, DirParser


def run(opts: argparse.Namespace, meson_root_dir_info: DirInfo, dir_parser: DirParser) -> bool:
    print(__file__)
    return True
