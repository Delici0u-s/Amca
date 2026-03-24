"""
management_src/_core.py
Shared venv, compilation, deployment, and plugin-bootstrap logic.
Standard library ONLY — no third-party dependencies.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional

from .helpers import (
    add_to_posix_path,
    exe,
    get_platform,
    remove_dir,
    remove_file,
    repo_root,
    windows_add_to_path,
)


# ── Venv helpers ──────────────────────────────────────────────────────────────

def _venv_py_candidates(venv: Path) -> list[Path]:
    return [
        venv / "bin"     / "python3",
        venv / "bin"     / "python",
        venv / "Scripts" / "python3.exe",
        venv / "Scripts" / "python.exe",
    ]


def venv_is_healthy(venv: Path) -> bool:
    return any(p.exists() for p in _venv_py_candidates(venv))


def locate_venv_python(venv: Path) -> Path:
    for p in _venv_py_candidates(venv):
        if p.exists():
            return p
    raise SystemExit(f"ERROR: Python not found inside venv: {venv}")


def create_venv(venv_path: Path, force: bool = False) -> Path:
    """
    Create (or reuse) a venv at *venv_path*.
    *force=True* destroys and rebuilds an existing venv.
    Returns the absolute path to the venv's Python interpreter.
    """
    if force and venv_path.exists():
        print("  Removing existing venv …")
        remove_dir(venv_path)

    if venv_path.exists():
        print(f"  Reusing venv at {venv_path}")
    else:
        print(f"  Creating venv at {venv_path} …")
        subprocess.run(
            [sys.executable, "-m", "venv", str(venv_path)],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        print("  Venv created.")

    py = locate_venv_python(venv_path)

    # Ensure pip is present.
    subprocess.run(
        [str(py), "-m", "ensurepip", "--upgrade"],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return py


def pip_install(py: Path, package: str, version: str = "", verbose: bool = False) -> bool:
    spec = f"{package}=={version}" if version else package
    print(f"  pip install {spec}")
    r = subprocess.run(
        [str(py), "-m", "pip", "install", "--upgrade", spec],
        stdout=None if verbose else subprocess.DEVNULL,
        stderr=None if verbose else subprocess.DEVNULL,
    )
    if r.returncode != 0:
        print(f"  ERROR: failed to install {spec}")
        return False
    return True


def install_runtime_deps(py: Path) -> None:
    """Install all packages that Amca itself needs at runtime."""
    pip_install(py, "pip")
    pip_install(py, "InquirerPy")
    pip_install(py, "requests")
    # pip_install(py, "argcomplete") #this gonna be wyld in future if it works


# ── PyInstaller compilation ───────────────────────────────────────────────────

def create_compiled(py: Path) -> Path:
    """
    Compile src/amca.py and src/amcapl.py into standalone binaries.
    Returns the directory where the binaries were placed (repo/compiled/).
    PyInstaller is installed into the venv automatically.
    """
    src_path      = (repo_root() / "src").resolve()
    compiled_path = (repo_root() / "compiled").resolve()
    compiled_path.mkdir(exist_ok=True)

    if not pip_install(py, "pyinstaller"):
        raise SystemExit("ERROR: Could not install PyInstaller.")

    scripts = ["amca.py", "amcapl.py"]
    for script in scripts:
        script_path = src_path / script
        if not script_path.exists():
            print(f"  WARNING: {script_path} not found — skipping.")
            continue
        name = script_path.stem
        print(f"  Compiling {name} …")
        r = subprocess.run([
            str(py), "-m", "PyInstaller",
            str(script_path),
            "--distpath", str(compiled_path),
            "--onefile",
            "--strip",
            "--noconfirm",
            "--clean",
        ])
        if r.returncode != 0:
            raise SystemExit(f"ERROR: PyInstaller failed for {script}.")
        print(f"  {name} compiled.")

    # Clean up PyInstaller artefacts.
    remove_dir(repo_root() / "build")
    for script in scripts:
        remove_file(repo_root() / (Path(script).stem + ".spec"))

    return compiled_path


# ── Binary deployment ─────────────────────────────────────────────────────────

def deploy_binaries(compiled_path: Path, bin_dir: Path) -> list[Path]:
    """
    Copy compiled executables from *compiled_path* to *bin_dir*.
    Marks them executable on POSIX.  Returns list of deployed paths.
    """
    bin_dir.mkdir(parents=True, exist_ok=True)
    deployed: list[Path] = []
    for name in ["amca", "amcapl"]:
        src = compiled_path / exe(name)
        if not src.exists():
            print(f"  WARNING: compiled binary not found: {src}")
            continue
        dst = bin_dir / src.name
        shutil.copy2(src, dst)
        if get_platform() != "windows":
            dst.chmod(dst.stat().st_mode | 0o111)
        deployed.append(dst)
        print(f"  {src.name} → {dst}")
    return deployed


# ── PATH configuration ────────────────────────────────────────────────────────

def setup_path(bin_dir: Path) -> Optional[str]:
    """
    Add *bin_dir* to the user's PATH.
    Returns a human-readable description of what was modified, or None.
    """
    if get_platform() == "windows":
        ok = windows_add_to_path(bin_dir)
        return "Windows user PATH registry" if ok else None
    profile = add_to_posix_path(bin_dir)
    return str(profile) if profile else None


# ── Preset plugin bootstrap ───────────────────────────────────────────────────

def bootstrap_preset_plugins(conf_path: Path, overwrite: bool = True) -> list[str]:
    # dont install any plugins
    return []
    """
    Copy every folder under repo/preset_plugins/ into the installed_plugins
    directory inside the config tree.
    *overwrite=True* replaces existing same-name plugin dirs.
    Returns the list of plugin names that were installed/updated.
    """
    preset_src = repo_root() / "preset_plugins"
    if not preset_src.is_dir():
        print("  WARNING: preset_plugins/ not found in repo root — skipping.")
        return []

    plugins_dst = conf_path / "Amca_config" / "plugins" / "installed_plugins"
    plugins_dst.mkdir(parents=True, exist_ok=True)

    installed: list[str] = []
    for item in preset_src.iterdir():
        if not item.is_dir():
            continue
        dst = plugins_dst / item.name
        if dst.exists():
            if not overwrite:
                print(f"  Plugin kept (already exists): {item.name}")
                continue
            remove_dir(dst)
        shutil.copytree(item, dst)
        installed.append(item.name)
        print(f"  Plugin: {item.name}")

    # Write / update plugin_conf.json — only set defaults, never overwrite
    # user choices that are already present.
    plugin_conf_dir  = conf_path / "Amca_config" / "plugins"
    plugin_conf_file = plugin_conf_dir / "plugin_conf.json"

    existing: dict = {}
    if plugin_conf_file.exists():
        try:
            existing = json.loads(plugin_conf_file.read_text(encoding="utf-8"))
        except Exception:
            existing = {}

    existing.setdefault(
        "enabled_plugins",
        ["meson"] if "meson" in installed else (installed[:1] if installed else [])
    )
    existing.setdefault("generic", {}).setdefault("plugin_path", str(plugins_dst))
    existing.setdefault("plugin_sources", [
        "https://api.github.com/repos/Delici0u-s/Amca/contents/preset_plugins?ref=rewrite"
    ])

    plugin_conf_file.write_text(
        json.dumps(existing, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return installed
