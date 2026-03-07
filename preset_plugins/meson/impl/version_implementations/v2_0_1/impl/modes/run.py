from ..parse_args import MesonArgs
from typing import Optional
from pathlib import Path
from .....amca.dirparse import DirInfo, DirParser
from .... import meson_get_val
import subprocess
from ..util import parse_args_shlex

def run(
    opts: MesonArgs,
    meson_file: Path,
    meson_root_dir_info: DirInfo,
    amca_root_plugin_dir: Optional[Path],
    working_dir: DirInfo,
    dir_parser: DirParser,
) -> bool:
    if opts.skip_exec:
        return True

    # --- Resolve executable ---
    build_var_name = "amca_var__meson__build_dir"
    install_var_name = "amca_var__meson__install_dir"
    executable_var_name = "amca_var__meson__executable_name"

    build_dir_name: Optional[str] = meson_get_val(meson_file, build_var_name)
    install_dir_name: Optional[str] = meson_get_val(meson_file, install_var_name)
    executable_name: Optional[str] = meson_get_val(meson_file, executable_var_name)

    for val in [build_dir_name, install_dir_name, executable_name]:
        if val is None:
            print(f"[exec] Error: '{val}' is missing or misconfigured in {meson_file}")
            return False

    meson_build_dir: Path = (meson_root_dir_info.path / build_dir_name).resolve()
    executable_path: Path = (meson_build_dir / install_dir_name / executable_name).resolve()

    if not executable_path.exists():
        print(f"[exec] Error: executable not found: {executable_path}")
        return False

    # --- Build command ---
    cmd = [str(executable_path)]
    if opts.exec_args is not None:
        cmd += parse_args_shlex(opts.exec_args)

    # --- Execute ---
    if opts.dry_run:
        print(f"[dry-run] {' '.join(cmd)} in {working_dir.path}")
        return True

    if opts.clear_console:
        import os
        subprocess.call(['cls' if os.name == 'nt' else 'clear'])

    if opts.verbose:
        print(f"[exec] Running: {' '.join(cmd)} in {working_dir.path}")

    return subprocess.call(cmd, cwd=working_dir.path) == 0
