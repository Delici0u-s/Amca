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
    if opts.skip_test:  # was incorrectly opts.skip_compile
        logger.log("[test] Skipped.")
        return True

    if not check_meson(logger):
        return False

    build_var_name = "amca_var__meson__build_dir"
    build_dir_name: Optional[str] = meson_get_val(meson_file, build_var_name)

    if build_dir_name is None:
        logger.error(f"[test] '{build_var_name}' is missing or misconfigured in {meson_file}")
        return False

    meson_build_dir: Path = (meson_root_dir_info.path / build_dir_name).resolve()
    if not meson_build_dir.exists():
        logger.error("[test] Build directory does not exist — ensure setup and compile ran first.")
        return False

    cmd = ["meson", "test", "--num-processes", str(opts.jobs)]
    if opts.verbose:
        cmd.append("--verbose")

    logger.log(f"[test] Running: {' '.join(cmd)}")

    if opts.dry_run:
        logger.log(f"[dry-run] {' '.join(cmd)}  (cwd: {meson_build_dir})")
        return True

    ok = subprocess.call(cmd, cwd=meson_build_dir) == 0
    if ok:
        logger.success("[test] All tests passed.")
    else:
        logger.error("[test] One or more tests failed.")
    return ok
