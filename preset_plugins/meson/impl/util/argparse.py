import argparse
import os
import shlex
from impl.amca.dirparse import DirInfo, DirParser


def parse_args(args: list[str]) -> argparse.Namespace:
    """
    Parse CLI arguments for the meson plugin.

    Returns argparse.Namespace with normalized attributes:
      mode: Optional[str]
      builddir: Optional[str]
      skip_reconf / skip_compile / skip_exec: booleans
      clear: bool
      s: bool  # shorthand: clear then run
      clear_console: bool
      meson_setup_args: Optional[str]
      meson_compile_args: Optional[str]
      exec_args: Optional[str]
      dry_run: bool
      force: bool
      verbose: bool
      quiet: bool
      jobs: int
    """
    parser = argparse.ArgumentParser(
        prog="amca [prefix]meson", description="AMCA Meson helper"
    )

    # positional mode
    parser.add_argument(
        "mode",
        nargs="?",
        choices=["setup", "reconfigure", "compile", "run", "clean", "test"],
        help="Mode to run (default pipeline if omitted)",
    )

    # builddir
    parser.add_argument(
        "-builddir",
        "--builddir",
        "-C",
        dest="builddir",
        metavar="DIR",
        help="Build directory",
    )

    # skip: accepts -n r, -n c, -n e (can be given multiple times), or the long flags below
    parser.add_argument(
        "-n",
        "--skip",
        dest="skip",
        action="append",
        choices=["r", "c", "e", "reconfigure", "compile", "exec"],
        help="Skip step. Use -n r (skip reconfigure), -n c (skip compile), -n e (skip exec). Can be repeated.",
    )

    # explicit skip flags (long form convenience)
    parser.add_argument(
        "--skip-reconf",
        dest="skip_reconf_flag",
        action="store_true",
        help="Do not reconfigure",
    )
    parser.add_argument(
        "--skip-compile",
        dest="skip_compile_flag",
        action="store_true",
        help="Do not compile",
    )
    parser.add_argument(
        "--skip-exec", dest="skip_exec_flag", action="store_true", help="Do not execute"
    )

    # clean / clear
    parser.add_argument(
        "-clear",
        "--clear",
        "--clean",
        dest="clear",
        action="store_true",
        help="Remove build artifacts (safe clean)",
    )
    parser.add_argument(
        "--force",
        dest="force",
        action="store_true",
        help="Allow destructive action [TODO: not yet used in anything lmao]",
    )

    # shorthand -s: clear then run
    parser.add_argument(
        "-s", dest="s", action="store_true", help="Shorthand: -clear then run"
    )

    # clear console before exec
    parser.add_argument(
        "-c",
        "--clear-console",
        dest="clear_console",
        action="store_true",
        help="Clear the terminal before executing the final binary",
    )

    # meson args: long forms and short forms -Ab, -Ac, -Ae (literal short names)
    parser.add_argument(
        "--meson-setup-args",
        "-Ab",
        dest="meson_setup_args",
        metavar='"ARGS"',
        help="Pass-through args to `meson setup` / configure (string)",
    )
    parser.add_argument(
        "--meson-compile-args",
        "-Ac",
        dest="meson_compile_args",
        metavar='"ARGS"',
        help="Pass-through args to `meson compile` (string)",
    )
    parser.add_argument(
        "--exec-args",
        "-Ae",
        dest="exec_args",
        metavar='"ARGS"',
        help="Args to pass to the executed binary (string)",
    )

    # misc flags
    parser.add_argument(
        "--dry-run",
        dest="dry_run",
        action="store_true",
        help="Show commands without running",
    )
    parser.add_argument(
        "-v", "--verbose", dest="verbose", action="store_true", help="Verbose logging"
    )
    parser.add_argument(
        "-q",
        "--quiet",
        dest="quiet",
        action="store_true",
        help="Quiet logging (suppress typical output)",
    )

    # jobs
    default_jobs = os.cpu_count() or 1
    parser.add_argument(
        "-jobs",
        "--jobs",
        "-j",
        dest="jobs",
        type=int,
        default=default_jobs,
        help=f"Number of threads to compile with (default: {default_jobs})",
    )

    parsed = parser.parse_args(args)

    # Normalize skip flags into explicit booleans
    skip_list = parsed.skip or []
    # accept full names as well as letters
    skip_tokens = set()
    for token in skip_list:
        if token in ("r", "reconfigure"):
            skip_tokens.add("reconf")
        elif token in ("c", "compile"):
            skip_tokens.add("compile")
        elif token in ("e", "exec"):
            skip_tokens.add("exec")

    parsed.skip_reconf = bool(parsed.skip_reconf_flag) or ("reconf" in skip_tokens)
    parsed.skip_compile = bool(parsed.skip_compile_flag) or ("compile" in skip_tokens)
    parsed.skip_exec = bool(parsed.skip_exec_flag) or ("exec" in skip_tokens)

    # Clean up helper attrs we used only for parsing
    # (leaving them is harmless, but remove for clarity)
    delattr(parsed, "skip_reconf_flag")
    delattr(parsed, "skip_compile_flag")
    delattr(parsed, "skip_exec_flag")

    # Normalize meson args: keep them as raw strings (caller can shlex.split when running)
    # (If you prefer lists, do: parsed.meson_setup_args = shlex.split(parsed.meson_setup_args) when not None)

    return parsed
