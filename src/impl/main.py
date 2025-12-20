import os, sys
from impl.util.dirparse import global_dir_parser as GDP
from pathlib import Path


def main():

    p = GDP.parse_dir(Path(sys.argv[1]).parent)

    print(p.path)
    print(p.files)
    print(p.folders)
