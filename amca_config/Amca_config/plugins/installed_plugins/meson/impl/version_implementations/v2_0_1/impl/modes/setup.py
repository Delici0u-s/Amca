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
    build_var_name = "amca_var__meson__build_dir"

    build_dir_name: Optional[str]= meson_get_val(meson_file, build_var_name)

    if build_dir_name is None:
        print(f"Meson plugin could not determine build directory name.\n '{build_var_name}' seems to be misconfigured")
        return False

    meson_build_dir: Path = (meson_root_dir_info.path / build_dir_name).resolve()
    if meson_build_dir.exists():
        # abort since setup is not nessessary
        return True
    
    cmd = ['meson', 'setup', str(meson_build_dir)]

    if opts.meson_setup_args is not None:
        cmd += parse_args_shlex(opts.meson_setup_args)
    
    if opts.dry_run:
        print(f"Executing '{" ".join(cmd)}' in '{meson_root_dir_info.path}'")
        return True


    return subprocess.call(cmd, cwd=meson_root_dir_info.path) == 0
