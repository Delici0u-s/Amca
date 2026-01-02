import impl.util.logger as logger
import sys
from pathlib import Path
from impl.util.dirparse import DirParser

root_dir = Path(sys.argv[0]).parent

glog: logger.Logger = logger.Logger(root_dir / "amca_log.log")

global_dir_parser = DirParser()
