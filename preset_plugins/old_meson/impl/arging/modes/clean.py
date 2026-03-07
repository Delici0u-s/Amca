import argparse
from ...amca.dirparse import DirInfo, DirParser
import shutil as sh
from pathlib import Path

def run(opts: argparse.Namespace, meson_root_dir_info: DirInfo, dir_parser: DirParser) -> bool:
    # print(__file__)

    build_dir: Path = opts.builddir

    if build_dir.exists():
        if not opts.dry_run:
            sh.rmtree(build_dir, True)
        else:

            print(f"rm -rf {build_dir}")
    return True

