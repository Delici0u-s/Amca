import os, sys
from impl.util.globals import global_dir_parser as gdp
from pathlib import Path
import impl.util.config.config as cf
import impl.amca_pl_impl.argparse as argparse


def main():
    if cf.general_settings.get("extreamly_important.greet_user"):
        print("Hello Master")

    argparse.eval_args()
