from ..parse_args import MesonArgs
from typing import Optional
from pathlib import Path
from .....amca.dirparse import DirInfo, DirParser
from .....amca.logger import Logger
from .... import meson_get_val
from ..util import check_meson
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
    if opts.skip_install:
        logger.log("[install] Skipped.")
        return True

    if not check_meson(logger):
        return False

    build_var_name = "amca_var__meson__build_dir"
    build_dir_name: Optional[str] = meson_get_val(meson_file, build_var_name)

    if build_dir_name is None:
        logger.error(
            f"[install] Could not determine build directory name.\n"
            f"  '{build_var_name}' is missing or misconfigured in {meson_file}"
        )
        return False

    meson_build_dir: Path = (meson_root_dir_info.path / build_dir_name).resolve()
    if not meson_build_dir.exists():
        logger.error("[install] Build directory does not exist — ensure setup and compile ran first.")
        return False

    cmd = ["meson", "install"]

    logger.log(f"[install] Running: {' '.join(cmd)}")

    if opts.dry_run:
        logger.log(f"[dry-run] {' '.join(cmd)}  (cwd: {meson_build_dir})")
        return True

    ok = subprocess.call(cmd, cwd=meson_build_dir) == 0
    if ok:
        logger.success("[install] Done.")
    else:
        logger.error("[install] meson install failed.")
    return ok
