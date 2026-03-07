import os
import re
import sys
import subprocess
import shutil
from pathlib import Path
from typing import Optional

from ...amca.dirparse import DirInfo, DirParser
from .impl.args import parse_args
from .impl import cache, ide, clipboard


# --- Old meson.build var names ---
_VAR_BUILD_DIR  = 'build_dir_where'
_VAR_OUTPUT_DIR = 'output_dir'
_VAR_EXE_NAME   = 'output_name'


def _get_var(meson_file: Path, name: str) -> Optional[str]:
    pat = re.compile(rf"^{name}\s*=\s*['\"](.*)['\"]")
    for line in meson_file.read_text(encoding='utf-8').splitlines():
        m = pat.match(line)
        if m:
            return m.group(1)
    return None


def evaluate(
    meson_file: Path,
    meson_root_dir_info: DirInfo,
    amca_root_plugin_dir: Optional[Path],
    dir_parser: DirParser,
    args: list[str],
    working_dir: DirInfo,
) -> None:
    opts = parse_args(args)

    basedir    = meson_root_dir_info.path
    meson_file = basedir / 'meson.build'

    # --- Resolve meson.build variables ---
    build_dir_name = _get_var(meson_file, _VAR_BUILD_DIR)
    output_sub     = _get_var(meson_file, _VAR_OUTPUT_DIR)
    exe_name_base  = _get_var(meson_file, _VAR_EXE_NAME)

    for name, val in [(_VAR_BUILD_DIR, build_dir_name),
                      (_VAR_OUTPUT_DIR, output_sub),
                      (_VAR_EXE_NAME,   exe_name_base)]:
        if val is None:
            print(f"[v1] '{name}' not found in meson.build")
            sys.exit(1)

    build_dir  = (basedir / build_dir_name).resolve()
    output_sub = Path(output_sub)
    exe_name   = exe_name_base + ('.exe' if os.name == 'nt' else '')

    # --- Handle -clear ---
    if opts.clear:
        exe_path = build_dir / output_sub / exe_name
        if exe_path.exists():
            exe_path.unlink()
        # remove empty install subdir
        exe_dir = (build_dir / output_sub).resolve()
        if exe_dir.exists() and exe_dir != build_dir and not any(exe_dir.iterdir()):
            exe_dir.rmdir()
        if build_dir.exists():
            shutil.rmtree(build_dir)
        cache_file = basedir / '.sources_cache'
        if cache_file.exists():
            cache_file.unlink()
        print("[v1] Cleared artifacts")
        return

    os.chdir(basedir)

    # --- Setup or reconfigure ---
    if opts.force_setup or not build_dir.exists():
        if not build_dir.exists():
            # seed the cache before first setup so the next run won't spuriously reconfigure
            cache.seed(basedir, build_dir)

        ide.update_launch_json(basedir, build_dir, output_sub, exe_name)
        ide.update_clangd(basedir, build_dir)

        cmd = ['meson', 'setup', str(build_dir), '--wipe'] + opts.setup_args
        if subprocess.call(cmd, cwd=basedir):
            sys.exit(1)

    else:
        if cache.changed(basedir, build_dir):
            print("[v1] New sources detected, reconfiguring...")
            if subprocess.call(['meson', 'setup', '--reconfigure', str(build_dir)], cwd=basedir):
                sys.exit(1)

    # --- Compile + install ---
    if not opts.no_compile:
        if subprocess.call(['ninja', '-C', str(build_dir)] + opts.compile_args):
            sys.exit(2)
        if not opts.no_install:
            if subprocess.call(['meson', 'install', '-C', str(build_dir)]):
                sys.exit(3)

    # --- Execute ---
    if not opts.no_exec:
        exe_path = build_dir / output_sub / exe_name

        if not exe_path.exists():
            print(f"[v1] Executable not found: {exe_path}")
            sys.exit(1)

        if opts.clear_console:
            subprocess.call(['cls' if os.name == 'nt' else 'clear'])

        if opts.clipboard:
            text = f"cd {exe_path.parent}\n{exe_path} {' '.join(opts.exec_args)}"
            clipboard.copy(text)
            print("[v1] Commands copied to clipboard.")
            return

        try:
            ret = subprocess.call([str(exe_path)] + opts.exec_args)
            sys.exit(ret)
        except KeyboardInterrupt:
            sys.exit(0)
