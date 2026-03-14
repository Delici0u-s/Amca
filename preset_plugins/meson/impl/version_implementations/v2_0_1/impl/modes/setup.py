from ..parse_args import MesonArgs
from typing import Optional
from pathlib import Path
from .....amca.dirparse import DirInfo, DirParser
from .....amca.logger import Logger
from .... import meson_get_val
from ..util import parse_args_shlex, check_meson
import subprocess


def run(
    opts: MesonArgs,
    meson_file: Path,
    meson_root_dir_info: DirInfo,
    amca_root_plugin_dir: Optional[Path],
    working_dir: DirInfo,
    dir_parser: DirParser,
    logger: Logger,
) -> bool:
    if not check_meson(logger):
        return False

    build_var_name = "amca_var__meson__build_dir"
    build_dir_name: Optional[str] = meson_get_val(meson_file, build_var_name)

    if build_dir_name is None:
        logger.error(
            f"[setup] Could not determine build directory name.\n"
            f"  '{build_var_name}' is missing or misconfigured in {meson_file}"
        )
        return False

    meson_build_dir: Path = (meson_root_dir_info.path / build_dir_name).resolve()
    if meson_build_dir.exists():
        logger.log("[setup] Build dir already exists, skipping.")
        return True

    cmd = ["meson", "setup", str(meson_build_dir)]
    if opts.meson_setup_args is not None:
        cmd += parse_args_shlex(opts.meson_setup_args)

    logger.log(f"[setup] Running: {' '.join(cmd)}")

    if opts.dry_run:
        logger.log(f"[dry-run] {' '.join(cmd)}  (cwd: {meson_root_dir_info.path})")
        return True

    ok = subprocess.call(cmd, cwd=meson_root_dir_info.path) == 0
    if ok:
        logger.success("[setup] Done.")
    else:
        logger.error("[setup] meson setup failed.")
    return ok
