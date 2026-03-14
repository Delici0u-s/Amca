from typing import Optional
from pathlib import Path

from ...amca.dirparse import DirInfo, DirParser
from ...amca.logger import Logger

from .impl.parse_args import parse_args
from .impl.util import check_meson
from .impl.modes import setup, compile as compiler, install, reconfigure, run, test, clean

PIPELINE = [clean, setup, reconfigure, compiler, install, test, run]

MODES = {
    "clean":       clean,
    "setup":       setup,
    "reconfigure": reconfigure,
    "compile":     compiler,
    "install":     install,
    "run":         run,
    "test":        test,
}


def _make_logger(verbose: bool, quiet: bool) -> Logger:
    """
    Map CLI verbosity flags to Logger configuration.

      verbose=True  → verbose prefix, INFO threshold (everything)
      quiet=True    → no prefix,      WARN threshold  (warnings/errors only)
      default       → simple prefix,  INFO threshold
    """
    if verbose:
        prefix    = "verbose"
        min_level = "INFO"
    elif quiet:
        prefix    = "None"
        min_level = "WARN"
    else:
        prefix    = "simple"
        min_level = "INFO"

    return Logger(
        log_prefix_level=prefix,
        min_log_level=min_level,
        file_enabled=False,
        console_enabled=True,
    )


def _call(module, opts, meson_file, meson_root_dir_info, amca_root_plugin_dir, working_dir, dir_parser, logger) -> bool:
    """Uniform call wrapper so every site has the same argument order."""
    return module.run(opts, meson_file, meson_root_dir_info, amca_root_plugin_dir, working_dir, dir_parser, logger)


def evaluate(
    meson_file: Path,
    meson_root_dir_info: DirInfo,
    amca_root_plugin_dir: Optional[Path],
    dir_parser: DirParser,
    args: list[str],
    working_dir: DirInfo,
) -> None:
    opts   = parse_args(args)
    logger = _make_logger(opts.verbose, opts.quiet)

    call = lambda module: _call(
        module, opts, meson_file, meson_root_dir_info,
        amca_root_plugin_dir, working_dir, dir_parser, logger,
    )

    if opts.clear or opts.s:
        if not call(clean):
            return

        if opts.s:
            # -s = clean then full pipeline (skip clean in the pipeline itself
            # by temporarily leaving opts.clear/s logic to clean.run's guard)
            for step in PIPELINE:
                if step is clean:
                    continue
                if not call(step):
                    break
        elif opts.mode is not None:
            module = MODES.get(opts.mode)
            if module is None:
                logger.error(f"Unknown mode: {opts.mode!r}")
                return
            call(module)
        # else: bare --clear, nothing more to do

    else:
        if opts.mode is None:
            for step in PIPELINE:
                if not call(step):
                    break
        else:
            module = MODES.get(opts.mode)
            if module is None:
                logger.error(f"Unknown mode: {opts.mode!r}")
                return
            call(module)
