import subprocess
from pathlib import Path
from typing import Optional

from amca.plugin_base import *
from amca.logger import Logger

from impl.args import parse_args, should_create_new
from impl.create import create_new_script
from impl.files import (
  build_cmd,
  find_script,
  relevant_dir,
  # should_create_new
)
from impl.constants import VERBOSE_FLAG


class autosh(Plugin):
  def should_load(
    self,
    amca_root_dir: Optional[DirInfo],
    amca_root_plugin_dir: Optional[Path],
    working_dir: DirInfo,
    dir_parser: DirParser,
    args: list[str],
  ) -> bool:
    directory = relevant_dir(amca_root_dir, working_dir)
    return should_create_new(args) or find_script(directory) is not None

  def load(
    self,
    amca_root_dir: Optional[DirInfo],
    amca_root_plugin_dir: Optional[Path],
    working_dir: DirInfo,
    dir_parser: DirParser,
    args: list[str],
  ) -> None:
    parsed = parse_args(args)
    logger = Logger(
      log_prefix_level="simple",
      min_log_level="INFO" if parsed.verbose else "WARN",
      file_enabled=False,
      console_enabled=True,
    )

    directory = relevant_dir(amca_root_dir, working_dir)

    if parsed.create_new:
      created = create_new_script(
        directory=directory,
        assume_yes=parsed.assume_yes,
        logger=logger,
      )
      if created is not None:
        logger.log(f"Created: {created.name}")
      return

    script = find_script(directory, logger)
    if script is None:
      return

    cmd = build_cmd(script, parsed.forwarded_args, logger)
    if cmd is None:
      return

    logger.log(f"Running: {' '.join(cmd)}")
    try:
      subprocess.call(cmd, cwd=script.parent)
    except OSError as e:
      logger.error(f"Failed to execute '{script.name}': {e}")
