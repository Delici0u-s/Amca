from typing import Optional
from ...amca.dirparse import DirInfo, DirParser
from pathlib import Path

from .impl.parse_args import parse_args # crazy line tbh

from .impl.modes import setup, compile as compiler, install, reconfigure, run, setup, test, clean

PIPELINE = [clean, setup, reconfigure, compiler, install, test, run]

MODES = {
    "clean":       clean,
    "setup":       setup,
    "reconfigure": reconfigure,
    "compile":     compiler,
    "run":         run,
    "test":        test,
}

def evaluate(meson_file: Path,
             meson_root_dir_info: DirInfo,
             amca_root_plugin_dir: Optional[Path],
             dir_parser: DirParser,
             args: list[str],
             working_dir: DirInfo):

    # print("new_vers")

    opts = parse_args(args)

    if opts.clear:
        clean.run(opts, meson_file, meson_root_dir_info, amca_root_plugin_dir, working_dir, dir_parser)
        if opts.mode is not None:
            module = MODES.get(opts.mode)
            module.run(opts, meson_file, meson_root_dir_info, amca_root_plugin_dir, working_dir, dir_parser)
    else:
        if opts.mode is None:
            for step in PIPELINE:
                if not step.run(opts, meson_file, meson_root_dir_info, amca_root_plugin_dir, working_dir, dir_parser):
                    break
        elif module := MODES.get(opts.mode):
            module.run(opts, meson_file, meson_root_dir_info, amca_root_plugin_dir, dir_parser)
        else:
            raise ValueError(f"Unknown mode: {opts.mode!r}")

    # print("Printing:")
    #
    # print(opts)


