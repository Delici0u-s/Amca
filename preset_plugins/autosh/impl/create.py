import os
from pathlib import Path
from typing import Optional

from amca.logger import Logger

from impl.constants import NAME
from impl.files import find_script

try:
  from InquirerPy import inquirer
except ImportError as e:
  raise RuntimeError(
    "InquirerPy is required for new-file creation mode."
  ) from e


def _default_extension() -> str:
  return ".ps1" if os.name == "nt" else ".sh"


def _choices() -> list[dict[str, str]]:
  if os.name == "nt":
    return [
      {"name": "PowerShell (.ps1)", "value": ".ps1"},
      {"name": "Batch (.bat)", "value": ".bat"},
      {"name": "Command (.cmd)", "value": ".cmd"},
    ]

  return [
    {"name": "Bash (.sh)", "value": ".sh"},
    {"name": "Bash (.bash)", "value": ".bash"},
    {"name": "Zsh (.zsh)", "value": ".zsh"},
  ]


def _template(ext: str) -> str:
  if os.name == "nt":
    if ext == ".bat":
      return "@echo off\r\nrem Add your script here\r\n"
    if ext == ".cmd":
      return "@echo off\r\nrem Add your script here\r\n"
    return "# Add your PowerShell script here\r\n"

  shebangs = {
    ".sh": "#!/usr/bin/env sh",
    ".bash": "#!/usr/bin/env bash",
    ".zsh": "#!/usr/bin/env zsh",
  }
  shebang = shebangs.get(ext, "#!/usr/bin/env sh")
  return f"{shebang}\n\n# Add your script here\n"


def create_new_script(
  directory: Path,
  assume_yes: bool,
  logger: Logger,
) -> Optional[Path]:
  existing = find_script(directory, logger)
  if existing is not None:
    logger.warn(f"Script already exists: {existing.name}")
    return None

  default_ext = _default_extension()
  if assume_yes:
    ext = default_ext
  else:
    ext = inquirer.select(
      message="Select script type:",
      choices=_choices(),
      default=default_ext,
    ).execute()

  script_path = directory / f"{NAME}{ext}"
  if script_path.exists():
    logger.warn(f"File already exists: {script_path.name}")
    return None

  try:
    script_path.write_text(_template(ext), encoding="utf-8")
    if os.name != "nt":
      script_path.chmod(script_path.stat().st_mode | 0o111)
    return script_path
  except OSError as e:
    logger.error(f"Failed to create script: {e}")
    return None
