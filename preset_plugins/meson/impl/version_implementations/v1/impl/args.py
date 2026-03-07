import argparse
from dataclasses import dataclass
from typing import Optional


@dataclass(slots=True)
class V1Args:
    force_setup:        bool        # -s  : meson setup --wipe
    no_exec:            bool        # -ne
    no_compile:         bool        # -nc
    no_install:         bool        # -ni
    clear_console:      bool        # -c
    clipboard:          bool        # -m
    clear:              bool        # -clear
    setup_args:         list[str]   # -Ab
    compile_args:       list[str]   # -Ac
    exec_args:          list[str]   # -Ae


def parse_args(args: list[str]) -> V1Args:
    p = argparse.ArgumentParser(prog="amca meson (v1)")

    p.add_argument('-s',     action='store_true', dest='force_setup')
    p.add_argument('-ne',    action='store_true', dest='no_exec')
    p.add_argument('-nc',    action='store_true', dest='no_compile')
    p.add_argument('-ni',    action='store_true', dest='no_install')
    p.add_argument('-c',     action='store_true', dest='clear_console')
    p.add_argument('-m',     action='store_true', dest='clipboard')
    p.add_argument('-clear', action='store_true', dest='clear')
    p.add_argument('-Ab',    nargs='*', default=[], dest='setup_args')
    p.add_argument('-Ac',    nargs='*', default=[], dest='compile_args')
    p.add_argument('-Ae',    nargs='*', default=[], dest='exec_args')

    ns = p.parse_args(args)
    return V1Args(
        force_setup   = ns.force_setup,
        no_exec       = ns.no_exec,
        no_compile    = ns.no_compile,
        no_install    = ns.no_install,
        clear_console = ns.clear_console,
        clipboard     = ns.clipboard,
        clear         = ns.clear,
        setup_args    = ns.setup_args,
        compile_args  = ns.compile_args,
        exec_args     = ns.exec_args,
    )
