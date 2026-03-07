# src/impl/util/globals.py
import impl.util.logger as logger
import os
import sys
from pathlib import Path
from impl.util.dirparse import DirParser
from config_path import config_path as _baked_config_path

# Allow the config root to be overridden at runtime without recompiling.
# This mirrors the install-time AMCA_CONFIG_PATH env var support.
_env_override = os.environ.get("AMCA_CONFIG_PATH")
if _env_override:
    try:
        root_dir = Path(_env_override).expanduser().resolve()
    except Exception:
        root_dir = Path(_baked_config_path)
else:
    root_dir = Path(_baked_config_path)

if not root_dir or str(root_dir) == "" or str(root_dir) == ".":
    print(
        "FATAL: Amca config root is not set.\n"
        "       Please re-run INSTALL.py or set the AMCA_CONFIG_PATH environment variable.",
        file=sys.stderr,
    )
    raise SystemExit(1)

glog: logger.Logger = logger.Logger(root_dir / "Amca_config" / "amca_log.log")

global_dir_parser = DirParser()

from impl.util.path_helpers import _find_amca_root_dir

amca_root_dir_info = _find_amca_root_dir()
