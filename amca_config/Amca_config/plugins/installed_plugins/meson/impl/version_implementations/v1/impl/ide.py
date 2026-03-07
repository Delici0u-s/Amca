import json
import os
from pathlib import Path


def update_launch_json(meson_root: Path, build_dir: Path, output_sub: Path, exe_name: str) -> None:
    launch_file = meson_root / '.vscode' / 'launch.json'
    if not launch_file.exists():
        return
    try:
        data = json.loads(launch_file.read_text(encoding='utf-8'))
        rel_exe = (build_dir / output_sub / exe_name).relative_to(meson_root)
        value = "${workspaceFolder}/" + rel_exe.as_posix()
        for cfg in data.get('configurations', []):
            cfg['program'] = value
        launch_file.write_text(json.dumps(data, indent=4), encoding='utf-8')
    except Exception as e:
        print(f"[v1] Warning: could not update launch.json: {e}")


def update_clangd(meson_root: Path, build_dir: Path) -> None:
    clangd_path = meson_root / '.clangd'
    if not clangd_path.exists():
        return
    try:
        rel_build = build_dir.relative_to(meson_root).as_posix()
        lines = clangd_path.read_text(encoding='utf-8').splitlines()
        new_lines = []
        updated = False
        for line in lines:
            if line.lstrip().startswith('CompilationDatabase:'):
                indent = len(line) - len(line.lstrip())
                new_lines.append(' ' * indent + f"CompilationDatabase: {rel_build}")
                updated = True
            else:
                new_lines.append(line)
        if not updated:
            new_lines.append(f"CompilationDatabase: {rel_build}")
        clangd_path.write_text('\n'.join(new_lines), encoding='utf-8')
    except Exception as e:
        print(f"[v1] Warning: could not update .clangd: {e}")
