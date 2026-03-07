from ..parse_args import MesonArgs
from typing import Optional
from pathlib import Path
from .....amca.dirparse import DirInfo, DirParser
from .... import meson_get_val
from .helper.source_cache import sources_changed
import subprocess
import json
import os


def _update_launch_json(
    meson_root: Path,
    meson_build_dir: Path,
    install_dir_name: str,
    executable_name: str,
) -> None:
    launch_file = meson_root / '.vscode' / 'launch.json'
    if not launch_file.exists():
        return

    exe_name = executable_name + ('.exe' if os.name == 'nt' else '')
    rel_exe = (meson_build_dir / install_dir_name / exe_name).relative_to(meson_root)
    program_value = "${workspaceFolder}/" + rel_exe.as_posix()

    try:
        data = json.loads(launch_file.read_text(encoding='utf-8'))
        for cfg in data.get('configurations', []):
            cfg['program'] = program_value
        launch_file.write_text(json.dumps(data, indent=4), encoding='utf-8')
    except Exception as e:
        print(f"[reconfigure] Warning: could not update launch.json: {e}")


def run(
    opts: MesonArgs,
    meson_file: Path,
    meson_root_dir_info: DirInfo,
    amca_root_plugin_dir: Optional[Path],
    working_dir: DirInfo,
    dir_parser: DirParser,
) -> bool:
    if opts.skip_reconf:
        return True

    # --- Resolve build directory ---
    build_var_name      = "amca_var__meson__build_dir"
    install_var_name    = "amca_var__meson__install_dir"
    executable_var_name = "amca_var__meson__executable_name"

    build_dir_name:   Optional[str] = meson_get_val(meson_file, build_var_name)
    install_dir_name: Optional[str] = meson_get_val(meson_file, install_var_name)
    executable_name:  Optional[str] = meson_get_val(meson_file, executable_var_name)

    if build_dir_name is None:
        print(f"[reconfigure] Error: '{build_var_name}' is missing or misconfigured in {meson_file}")
        return False

    meson_build_dir: Path = (meson_root_dir_info.path / build_dir_name).resolve()

    if not meson_build_dir.exists():
        return True

    # --- IDE config sync (runs regardless of source changes) ---
    if install_dir_name is not None and executable_name is not None:
        _update_launch_json(
            meson_root_dir_info.path,
            meson_build_dir,
            install_dir_name,
            executable_name,
        )

    # --- Source-change detection ---
    exclude = frozenset({meson_build_dir})

    if not sources_changed(meson_root_dir_info.path, amca_root_plugin_dir, exclude):
        if opts.verbose:
            print("[reconfigure] Sources unchanged, skipping.")
        return True

    if not opts.quiet:
        print("[reconfigure] New sources detected, reconfiguring...")

    cmd = ['meson', 'setup', '--reconfigure', str(meson_build_dir)]

    if opts.dry_run:
        print(f"[dry-run] {' '.join(cmd)}  (cwd: {meson_root_dir_info.path})")
        return True

    return subprocess.call(cmd, cwd=meson_root_dir_info.path) == 0
