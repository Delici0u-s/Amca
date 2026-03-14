import os, sys
from impl.util.globals import global_dir_parser as gdp
from pathlib import Path
import impl.util.config.config as cf
import impl.util.logger as logger
import impl.amca_impl.argparse as argp
from impl.util.globals import glog


def _apply_logger_config() -> None:
    """Reconfigure glog from general_settings after config has loaded."""
    log_mode = cf.general_settings.get("logging.log_mode") or "both"
    glog.set_mode(log_mode)

    min_level = cf.general_settings.get("logging.min_level") or "INFO"
    if min_level in logger.Logger._LEVEL_PRIORITY:
        glog.set_min_level(min_level)

    prefix_level_name = cf.general_settings.get("logging.log_prefix_level") or "normal"
    glog.prefix_level = logger.Logger._PREFIX_LEVELS.get(prefix_level_name, 3)


def main():
    _apply_logger_config()

    if cf.general_settings.get("extreamly_important.greet_user"):
        print("Hello Master")

    argp.eval_args()
