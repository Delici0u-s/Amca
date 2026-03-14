import os
import subprocess
from typing import Optional
from pathlib import Path
from ..parse_args import MesonArgs
from .....amca.dirparse import DirInfo, DirParser
from .....amca.logger import Logger
from .... import meson_get_val
from ..util import parse_args_shlex


def run(
    opts: MesonArgs,
    meson_file: Path,
    meson_root_dir_info: DirInfo,
    amca_root_plugin_dir: Optional[Path],
    working_dir: DirInfo,
    dir_parser: DirParser,
    logger: Logger,
) -> bool:
    if opts.skip_exec:
        logger.log("[exec] Skipped.")
        return True

    build_var_name      = "amca_var__meson__build_dir"
    install_var_name    = "amca_var__meson__install_dir"
    executable_var_name = "amca_var__meson__executable_name"

    build_dir_name:   Optional[str] = meson_get_val(meson_file, build_var_name)
    install_dir_name: Optional[str] = meson_get_val(meson_file, install_var_name)
    executable_name:  Optional[str] = meson_get_val(meson_file, executable_var_name)

    missing = [
        name for name, val in [
            (build_var_name,      build_dir_name),
            (install_var_name,    install_dir_name),
            (executable_var_name, executable_name),
        ] if val is None
    ]
    if missing:
        for m in missing:
            logger.error(f"[exec] '{m}' is missing or misconfigured in {meson_file}")
        return False

    meson_build_dir:  Path = (meson_root_dir_info.path / build_dir_name).resolve()
    executable_path:  Path = (meson_build_dir / install_dir_name / executable_name).resolve()

    if not executable_path.exists():
        logger.error(
            f"[exec] Executable not found: {executable_path}\n"
            "  Has the project been compiled and installed?"
        )
        return False

    cmd = [str(executable_path)]
    if opts.exec_args is not None:
        cmd += parse_args_shlex(opts.exec_args)

    if opts.dry_run:
        logger.log(f"[dry-run] {' '.join(cmd)}  (cwd: {working_dir.path})")
        return True

    if opts.clear_console:
        subprocess.call(["cls" if os.name == "nt" else "clear"])

    logger.log(f"[exec] Running: {' '.join(cmd)}")

    return subprocess.call(cmd, cwd=working_dir.path) == 0
