from ..parse_args import MesonArgs
from typing import Optional
from pathlib import Path
from .....amca.dirparse import DirInfo, DirParser # love for relative imports
from .... import meson_get_val # <<<<< perfect import line
import subprocess
from ..util import parse_args_shlex

def run(opts: MesonArgs,
            meson_file: Path,
             meson_root_dir_info: DirInfo,
             amca_root_plugin_dir: Optional[Path],
             working_dir: DirInfo,
             dir_parser: DirParser,
        ) -> bool:
    if opts.skip_compile:
        return True;


    build_var_name = "amca_var__meson__build_dir"

    build_dir_name: Optional[str]= meson_get_val(meson_file, build_var_name)

    if build_dir_name is None:
        print(f"Meson plugin could not determine build directory name.\n '{build_var_name}' seems to be misconfigured")
        return False

    meson_build_dir: Path = (meson_root_dir_info.path / build_dir_name).resolve()
    if not meson_build_dir.exists():
        print(f"Build directory does not exist, ensure setup ran")
        return False

    cmd = ['meson', 'compile', '-j', str(opts.jobs)]

    if opts.meson_compile_args is not None:
        cmd += parse_args_shlex(opts.meson_compile_args)

    if opts.dry_run:
        print(f"Executing '{" ".join(cmd)}' in '{meson_build_dir}'")
        return True


    return subprocess.call(cmd, cwd=meson_build_dir) == 0
