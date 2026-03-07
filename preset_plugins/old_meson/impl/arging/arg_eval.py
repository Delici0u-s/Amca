import argparse
import re
from pathlib import Path
from typing import Optional

from ..amca.dirparse import DirInfo, DirParser
from ..util import logger as lg
# import get_log, set_log, Logger
meson_file : Path
import importlib


# which provided version in meson is mapped to which implementation
VERSION_MAP = {
    None    : "v1",
    "2_0_1" : "v2_0_1",
}

def meson_get_val(var_name) -> Optional[str]:
    pat = re.compile(rf"^amca_var__meson__{var_name}\s*=\s*['\"](.*)['\"]")
    
    global meson_file
    for line in (meson_file).read_text().splitlines():
        m = pat.match(line)
        if m:
            return m.group(1)
    return None

def arg_eval(opts: argparse.Namespace,
             meson_root_dir_info: DirInfo, dir_parser: DirParser, args: list[str]):
    # for k, v in sorted(vars(opts).items()):
    #     print(f"  {k}: {v}")

    # lg.log = lg.Logger(opts.builddir / "AmcaMesonLog.log")
    # if opts.verbose:
    #     lg.log.log(f"Build dir: {opts.builddir}")

    global meson_file
    meson_file = meson_root_dir_info.path / "meson.build"
    opts.meson_version_behaviour = meson_get_val("version_behaviour")

    # behaviour checking
    module_path = "version_interpretations." + str(VERSION_MAP.get(opts.meson_version_behaviour))

    if module_path is None:
        lg.log.error(f"The given meson version '{opts.meson_version_behaviour}' is not supported by the amca meson plugin!")
    else:
        version = importlib.import_module(module_path)
        version.evaluate(meson_file, opts, meson_root_dir_info, dir_parser, args)

