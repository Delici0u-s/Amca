import os
from pathlib import Path
from typing import Optional

from amca.logger import Logger
from amca.plugin_base import *

from impl.constants import CANDIDATES, EXT_INTERPRETER


def relevant_dir(amca_root_dir: Optional[DirInfo], working_dir: DirInfo) -> Path:
  return amca_root_dir.path if amca_root_dir is not None else working_dir.path


def find_script(directory: Path, logger: Optional[Logger] = None) -> Optional[Path]:
  found = [directory / name for name in CANDIDATES if (directory / name).is_file()]

  if len(found) > 1:
    names = ", ".join(p.name for p in found)
    if logger is not None:
      logger.error(
        f"Multiple auto-scripts found in {directory}: {names}\n"
        f"  Remove all but one."
      )
    return None

  return found[0] if found else None


def build_cmd(script: Path, args: list[str], logger: Logger) -> Optional[list[str]]:
  interpreter = EXT_INTERPRETER.get(script.suffix.lower())
  if interpreter is not None:
    return interpreter + [str(script)] + args

  if not os.access(script, os.X_OK):
    logger.warn(
      f"'{script.name}' is not executable. "
      f"Run: chmod +x {script}"
    )
    return None

  return [str(script)] + args
