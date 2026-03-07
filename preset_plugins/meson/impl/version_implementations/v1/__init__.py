from typing import Optional
from ...amca.dirparse import DirInfo, DirParser
from pathlib import Path

def evaluate(meson_file: Path,
             meson_root_dir_info: DirInfo,
             amca_root_plugin_dir: Optional[Path],
             dir_parser: DirParser,
             args: list[str],
             working_dir: DirInfo):

    print("old_vers")

