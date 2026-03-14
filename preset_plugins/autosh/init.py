# init.py

import os
import subprocess
from pathlib import Path
from amca.plugin_base import *
from amca.logger import Logger

# ── Constants ─────────────────────────────────────────────────────────────────

_VERBOSE_FLAG = "--verbose_auto_sh"
_NAME         = "amca_auto_sh"

# Platform-specific: extension → interpreter command prefix
_EXT_INTERPRETER: dict[str, list[str]] = (
    {
        ".bat": ["cmd", "/C"],
        ".cmd": ["cmd", "/C"],
        ".ps1": ["powershell", "-ExecutionPolicy", "Bypass", "-File"],
    }
    if os.name == "nt" else
    {
        ".sh":   ["sh"],
        ".bash": ["bash"],
        ".zsh":  ["zsh"],
    }
)

# Candidates: extensionless first (Unix only), then one per known extension
_CANDIDATES: tuple[str, ...] = (
    tuple() if os.name == "nt" else (_NAME,)
) + tuple(f"{_NAME}{ext}" for ext in _EXT_INTERPRETER)

# ── Module-level helpers ──────────────────────────────────────────────────────

def _relevant(amca_root_dir: Optional[DirInfo], working_dir: DirInfo) -> Path:
    return amca_root_dir.path if amca_root_dir is not None else working_dir.path


def _find(directory: Path, logger: Logger) -> Optional[Path]:
    found = [directory / name for name in _CANDIDATES if (directory / name).is_file()]

    if len(found) > 1:
        names = ", ".join(p.name for p in found)
        logger.error(
            f"Multiple auto-scripts found in {directory}: {names}\n"
            f"  Remove all but one."
        )
        return None

    return found[0] if found else None


def _build_cmd(script: Path, args: list[str], logger: Logger) -> Optional[list[str]]:
    interpreter = _EXT_INTERPRETER.get(script.suffix.lower())
    if interpreter is not None:
        return interpreter + [str(script)] + args

    # Extensionless: needs executable bit (shebang is the user's responsibility)
    if not os.access(script, os.X_OK):
        logger.warn(
            f"'{script.name}' is not executable. "
            f"Run: chmod +x {script}"
        )
        return None

    return [str(script)] + args


def _parse_args(args: list[str]) -> tuple[bool, list[str]]:
    verbose = _VERBOSE_FLAG in args
    return verbose, [a for a in args if a != _VERBOSE_FLAG]


def _make_logger(verbose: bool) -> Logger:
    return Logger(
        log_prefix_level="simple",
        min_log_level="INFO" if verbose else "WARN",
        file_enabled=False,
        console_enabled=True,
    )

# ── Plugin ────────────────────────────────────────────────────────────────────

class autosh(Plugin):

    def should_load(
        self,
        amca_root_dir:        Optional[DirInfo],
        amca_root_plugin_dir: Optional[Path],
        working_dir:          DirInfo,
        dir_parser:           DirParser,
        args:                 list[str],
    ) -> bool:
        directory = _relevant(amca_root_dir, working_dir)
        return any((directory / name).is_file() for name in _CANDIDATES)

    def load(
        self,
        amca_root_dir:        Optional[DirInfo],
        amca_root_plugin_dir: Optional[Path],
        working_dir:          DirInfo,
        dir_parser:           DirParser,
        args:                 list[str],
    ) -> None:
        verbose, forwarded_args = _parse_args(args)
        logger = _make_logger(verbose)

        script = _find(_relevant(amca_root_dir, working_dir), logger)
        if script is None:
            return

        cmd = _build_cmd(script, forwarded_args, logger)
        if cmd is None:
            return

        logger.log(f"Running: {' '.join(cmd)}")
        try:
            subprocess.call(cmd, cwd=script.parent)
        except OSError as e:
            logger.error(f"Failed to execute '{script.name}': {e}")
