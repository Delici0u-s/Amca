import argparse
import os
from dataclasses import dataclass
from typing import Optional


VERSION = "2.0.1"


@dataclass(slots=True)
class MesonArgs:
    mode:               Optional[str] 
    skip_reconf:        bool 
    skip_compile:       bool
    skip_install:       bool
    skip_exec:          bool
    skip_test:          bool
    clear:              bool
    s:                  bool  # shorthand: clear then run
    clear_console:      bool 
    meson_setup_args:   Optional[str]
    meson_compile_args: Optional[str]
    exec_args:          Optional[str]
    dry_run:            bool
    verbose:            bool
    quiet:              bool
    jobs:               int


_SKIP_ALIASES: dict[str, str] = {
    "r": "reconf",  "reconfigure": "reconf",
    "c": "compile", "compile":     "compile",
    "i": "install", "install":     "install",
    "e": "exec",    "exec":        "exec",
    "t": "test",    "test":        "test",
}


def _build_parser() -> argparse.ArgumentParser:
    default_jobs = os.cpu_count() or 1

    p = argparse.ArgumentParser(
        prog="amca meson",
        description="AMCA Meson helper",
    )

    p.add_argument("-V", "--version", action="version", version=f"%(prog)s {VERSION}")

    p.add_argument(
        "mode", nargs="?",
        choices=["setup", "reconfigure", "compile", "install", "run", "clean", "test"],
        help="Mode to run (default pipeline if omitted)",
    )

    # -n accepts short tokens or full names; repeatable
    p.add_argument(
        "-n", "--skip", dest="skip", action="append",
        choices=list(_SKIP_ALIASES),
        metavar="{r,c,i,e,t,reconfigure,compile,install,exec,test}",
        help="Skip a pipeline step. Repeatable: -n r -n c -n t",
    )

    # Explicit long-form skip flags
    p.add_argument("--skip-reconf",   dest="skip_reconf",   action="store_true")
    p.add_argument("--skip-compile",  dest="skip_compile",  action="store_true")
    p.add_argument("--skip-install",  dest="skip_install",  action="store_true")
    p.add_argument("--skip-exec",     dest="skip_exec",     action="store_true")
    p.add_argument("--skip-test",     dest="skip_test",     action="store_true")

    p.add_argument("-clear", "--clear", "--clean", dest="clear", action="store_true",
                   help="Remove build artifacts (safe clean)")
    p.add_argument("-s", dest="s", action="store_true",
                   help="Shorthand: --clear then run")
    p.add_argument("-c", "--clear-console", dest="clear_console", action="store_true",
                   help="Clear the terminal before executing the final binary")

    p.add_argument("--meson-setup-args",   "-Ab", dest="meson_setup_args",
                   metavar='"ARGS"', help='Pass-through args to `meson setup`')
    p.add_argument("--meson-compile-args", "-Ac", dest="meson_compile_args",
                   metavar='"ARGS"', help='Pass-through args to `meson compile`')
    p.add_argument("--exec-args",          "-Ae", dest="exec_args",
                   metavar='"ARGS"', help="Args passed to the executed binary")

    p.add_argument("--dry-run", dest="dry_run", action="store_true",
                   help="Print commands without running them")
    p.add_argument("-v", "--verbose", dest="verbose", action="store_true")
    p.add_argument("-q", "--quiet",   dest="quiet",   action="store_true",
                   help="Suppress typical output")
    p.add_argument("-jobs", "--jobs", "-j", dest="jobs", type=int, default=default_jobs,
                   metavar="N", help=f"Compile thread count (default: {default_jobs})")

    return p


def parse_args(args: list[str]) -> MesonArgs:
    ns = _build_parser().parse_args(args)

    skipped = {_SKIP_ALIASES[t] for t in (ns.skip or [])}

    return MesonArgs(
        mode               = ns.mode,
        skip_reconf        = ns.skip_reconf  or "reconf"  in skipped,
        skip_compile       = ns.skip_compile or "compile" in skipped,
        skip_install       = ns.skip_install or "install" in skipped,
        skip_exec          = ns.skip_exec    or "exec"    in skipped,
        skip_test          = ns.skip_test    or "test"    in skipped,
        clear              = ns.clear,
        s                  = ns.s,
        clear_console      = ns.clear_console,
        meson_setup_args   = ns.meson_setup_args,
        meson_compile_args = ns.meson_compile_args,
        exec_args          = ns.exec_args,
        dry_run            = ns.dry_run,
        verbose            = ns.verbose,
        quiet              = ns.quiet,
        jobs               = ns.jobs,
    )
