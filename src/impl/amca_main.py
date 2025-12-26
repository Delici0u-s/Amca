import os, sys
from impl.util.dirparse import global_dir_parser as GDP
from pathlib import Path
import impl.util.config.config as cf


def main():
    # cf.ensure_config_structure()
    if cf.general_settings.get("extreamly_important.greet_user"):
        print("Hello Master")
    p = GDP.parse_dir(Path(sys.argv[1]).parent)

    print(p.path)
    print(p.files)
    print(p.folders)
