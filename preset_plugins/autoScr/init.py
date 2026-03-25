import subprocess
from pathlib import Path
from typing import Optional

from amca.plugin_base import *
from amca.logger import Logger

from impl.args import parse_args
from impl.create import create_new_script
from impl.files import build_cmd, find_preferred_script, find_script, relevant_dir


class autoscript(Plugin):
  def should_load(
    self,
    amca_root_dir: Optional[DirInfo],
    amca_root_plugin_dir: Optional[Path],
    working_dir: DirInfo,
    dir_parser: DirParser,
    args: list[str],
  ) -> bool:
    directory = relevant_dir(amca_root_dir, working_dir)
    return bool(args) or find_script(directory) is not None

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

    if "--help" in parsed.forwarded_args or "-h" in parsed.forwarded_args:
      print(
        "Usage: amca.py [n|new] [-y] [--verbose_auto_scr] [args for script]\n"
        "  n|new              Create a new script in the working directory\n"
        "  -y, --yes          Auto-confirm creation\n"
        "  --verbose_auto_scr Enable verbose logging\n"
        "  --help, -h         Show this message\n"
        "  other args         Forwarded to the selected script"
      )
      return

    try:
      if parsed.forwarded_args and parsed.forwarded_args[0] in ("n", "new"):
        working_existing = find_script(working_dir.path, logger=None)
        if working_existing is not None:
          logger.warn(
            f"Cannot create new script. Existing script found in working dir: "
            f"{working_existing.name}"
          )
          return

        root_existing = find_script(amca_root_dir.path, logger=None) if amca_root_dir else None
        if root_existing is not None:
          logger.warn(
            f"Root dir already has script: {root_existing.name}. "
            f"Creating in working dir instead."
          )

        created = create_new_script(
          directory=working_dir.path,
          assume_yes=parsed.assume_yes,
          logger=logger,
        )
        if created is not None:
          logger.log(f"Created: {created.name}")
        return

      script = find_preferred_script(amca_root_dir, working_dir, logger)
      if script is None:
        logger.warn("No script found to execute.")
        return

      cmd = build_cmd(script, parsed.forwarded_args, logger)
      if cmd is None:
        return

      logger.log(f"Running: {' '.join(cmd)}")
      subprocess.call(cmd, cwd=working_dir.path)
      # subprocess.call(cmd, cwd=script.parent)

    except KeyboardInterrupt:
      logger.warn("Operation cancelled by user (Ctrl-C).")
      return
