from ....amca.dirparse import DirInfo, DirParser
from pathlib import Path
import argparse

def evaluate(meson_file: Path,
             opts: argparse.Namespace,
             meson_root_dir_info: DirInfo,
             dir_parser: DirParser,
             args: list[str]):
    print("hi")

