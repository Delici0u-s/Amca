from ..parse_args import MesonArgs
from typing import Optional
from pathlib import Path
from .....amca.dirparse import DirInfo, DirParser
from .... import meson_get_val
import subprocess


def run(
    opts: MesonArgs,
    meson_file: Path,
    meson_root_dir_info: DirInfo,
    amca_root_plugin_dir: Optional[Path],
    working_dir: DirInfo,
    dir_parser: DirParser,
) -> bool:
    if opts.skip_test:
        return True

    build_var_name = "amca_var__meson__build_dir"
    build_dir_name: Optional[str] = meson_get_val(meson_file, build_var_name)

    if build_dir_name is None:
        print(f"[test] Error: '{build_var_name}' is missing or misconfigured in {meson_file}")
        return False

    meson_build_dir: Path = (meson_root_dir_info.path / build_dir_name).resolve()

    if not meson_build_dir.exists():
        print(f"[test] Build directory does not exist, ensure setup ran")
        return False

    cmd = ['meson', 'test', '--num-processes', str(opts.jobs)]

    if opts.verbose:
        cmd.append('--verbose')

    if opts.dry_run:
        print(f"[dry-run] {' '.join(cmd)}  (cwd: {meson_build_dir})")
        return True

    return subprocess.call(cmd, cwd=meson_build_dir) == 0
