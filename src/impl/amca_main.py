import os, sys
from impl.util.globals import global_dir_parser as gdp
from pathlib import Path
import impl.util.config.config as cf
import impl.amca_impl.argparse as argp


def main():
    # cf.ensure_config_structure()
    if cf.general_settings.get("extreamly_important.greet_user"):
        print("Hello Master")

    argp.eval_args()

    # p = GDP.parse_dir(Path(sys.argv[1]).parent)
    # print(p.path)
    # print(p.files)
    # print(p.folders)
