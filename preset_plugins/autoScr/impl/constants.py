import os
from pathlib import Path

VERBOSE_FLAG = "--verbose_auto_scr"
NAME = "amca_auto_script"

if os.name == "nt":
  EXT_INTERPRETER: dict[str, list[str]] = {
    ".bat": ["cmd", "/C"],
    ".cmd": ["cmd", "/C"],
    ".ps1": ["powershell", "-ExecutionPolicy", "Bypass", "-File"],
  }
else:
  EXT_INTERPRETER = {
    ".sh": ["sh"],
    ".bash": ["bash"],
    ".zsh": ["zsh"],
  }

if os.name == "nt":
  CANDIDATES: tuple[str, ...] = tuple(f"{NAME}{ext}" for ext in EXT_INTERPRETER)
else:
  CANDIDATES = (NAME,) + tuple(f"{NAME}{ext}" for ext in EXT_INTERPRETER)
