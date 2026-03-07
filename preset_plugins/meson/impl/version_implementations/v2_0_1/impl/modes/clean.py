from ..parse_args import MesonArgs
from typing import Optional
from pathlib import Path
from .....amca.dirparse import DirInfo, DirParser
from .... import meson_get_val
import shutil

def run(
    opts: MesonArgs,
    meson_file: Path,
    meson_root_dir_info: DirInfo,
    amca_root_plugin_dir: Optional[Path],
    working_dir: DirInfo,
    dir_parser: DirParser,
) -> bool:
    if not opts.clear and not opts.s:
        return True

    # --- Resolve build dir ---
    build_var_name = "amca_var__meson__build_dir"
    build_dir_name: Optional[str] = meson_get_val(meson_file, build_var_name)

    if build_dir_name is None:
        print(f"[clean] Error: '{build_var_name}' is missing or misconfigured in {meson_file}")
        return False

    meson_build_dir: Path = (meson_root_dir_info.path / build_dir_name).resolve()

    # --- Resolve install dir BEFORE deleting build dir ---
    install_var_name = "amca_var__meson__install_dir"
    executable_var_name = "amca_var__meson__executable_name"

    install_dir_name: Optional[str] = meson_get_val(meson_file, install_var_name)
    executable_name: Optional[str] = meson_get_val(meson_file, executable_var_name)

    if install_dir_name is None:
        print(f"[clean] Error: '{install_var_name}' is missing or misconfigured in {meson_file}")
        return False
    if executable_name is None:
        print(f"[clean] Error: '{executable_var_name}' is missing or misconfigured in {meson_file}")
        return False

    # install_dir is relative to build_dir, resolve before build_dir is removed
    executable_dir: Path = (meson_build_dir / install_dir_name).resolve()
    executable_path: Path = executable_dir / executable_name

    # --- Clean build dir ---
    if meson_build_dir.exists():
        if opts.dry_run:
            print(f"[dry-run] rm -rf {meson_build_dir}")
        else:
            if opts.verbose:
                print(f"[clean] Removing build dir: {meson_build_dir}")
            shutil.rmtree(meson_build_dir)
    else:
        if opts.verbose:
            print(f"[clean] Build dir not found, skipping: {meson_build_dir}")

    # --- Clean installed executable ---
    if executable_path.exists():
        if opts.dry_run:
            print(f"[dry-run] rm {executable_path}")
        else:
            if opts.verbose:
                print(f"[clean] Removing executable: {executable_path}")
            executable_path.unlink()
    elif opts.verbose:
        print(f"[clean] Executable not found, skipping: {executable_path}")

    # --- Remove executable dir if empty ---
    if executable_dir.exists() and executable_dir != meson_build_dir:
        if not any(executable_dir.iterdir()):
            if opts.dry_run:
                print(f"[dry-run] rmdir {executable_dir}")
            else:
                if opts.verbose:
                    print(f"[clean] Removing empty install dir: {executable_dir}")
                executable_dir.rmdir()

    return True
