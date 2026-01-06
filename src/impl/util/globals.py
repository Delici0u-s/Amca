import impl.util.logger as logger
import sys
from pathlib import Path
from impl.util.dirparse import DirParser
from config_path import config_path

root_dir = Path(config_path)

glog: logger.Logger = logger.Logger(root_dir / "Amca_config" / "amca_log.log")

global_dir_parser = DirParser()

from impl.util.path_helpers import _find_amca_root_dir

amca_root_dir_info = _find_amca_root_dir()
