"""
management_src/_helpers.py
Shared utilities for install / update / uninstall.
Standard library ONLY — no third-party dependencies.
"""

from __future__ import annotations

import json
import os
import shutil
import sys
from pathlib import Path
from typing import Optional

# ── Version ───────────────────────────────────────────────────────────────────

AMCA_VERSION = "2.0.2"

# ── Shell-profile marker tags ─────────────────────────────────────────────────

PATH_MARKER_START   = "# >>> amca PATH >>>"
PATH_MARKER_END     = "# <<< amca PATH <<<"
# Legacy tags from the old INSTALL.sh — kept only for cleanup purposes.
_ALIAS_MARKER_START = "# >>> amca ALIAS >>>"
_ALIAS_MARKER_END   = "# <<< amca ALIAS <<<"

# Candidate shell profiles in preference order.
POSIX_PROFILES: list[Path] = [
    Path.home() / ".profile",
    Path.home() / ".bashrc",
    Path.home() / ".zprofile",
    Path.home() / ".zshrc",
    Path.home() / ".config" / "fish" / "config.fish",
]

# ── Repository / file layout ──────────────────────────────────────────────────

# management_src/ lives at REPO_ROOT/management_src/
def repo_root() -> Path:
    return Path(__file__).parent.parent

def config_py_path() -> Path:
    """Absolute path to src/config_path.py."""
    return repo_root() / "src" / "config_path.py"

# ── src/config_path.py read / write ──────────────────────────────────────────

def read_config_path_py() -> Optional[Path]:
    """
    Parse src/config_path.py and return the stored config-root Path,
    or None if the file is absent or the value is empty/placeholder.
    """
    p = config_py_path()
    if not p.exists():
        return None
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line.startswith("config_path"):
            val = line.split("=", 1)[1].strip().strip("\"'")
            return Path(val) if val else None
    return None


def write_config_path_py(conf_path: Path) -> None:
    p = config_py_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    # Forward slashes everywhere — works in frozen binaries on all platforms.
    p.write_text(
        f'config_path = "{conf_path.as_posix()}"\n'
        "\n"
        "# Written by the Amca installer — do not edit manually.\n",
        encoding="utf-8",
    )


def reset_config_path_py() -> None:
    """Write a safe empty placeholder so stale imports don't crash."""
    p = config_py_path()
    if p.exists():
        p.write_text('config_path = ""\n', encoding="utf-8")


# ── Platform helpers ──────────────────────────────────────────────────────────

def get_platform() -> str:
    """Return 'windows', 'darwin', or 'linux'."""
    s = sys.platform
    if s.startswith("win"):    return "windows"
    if s.startswith("darwin"): return "darwin"
    if s.startswith("linux"):  return "linux"
    raise OSError(f"Unsupported platform: {s}")


def exe(name: str) -> str:
    """Append .exe on Windows."""
    return name + ".exe" if get_platform() == "windows" else name


def default_conf_base() -> Path:
    """Platform-standard base for the Amca config folder."""
    p = get_platform()
    if p == "windows":
        base = os.environ.get("USERPROFILE") or str(Path.home())
        return Path(base) / "Documents"
    if p == "darwin":
        return Path.home() / "Library" / "Application Support"
    xdg = os.environ.get("XDG_CONFIG_HOME", "")
    return Path(xdg) if xdg else Path.home() / ".config"


def default_bin_dir() -> Path:
    """Platform-standard directory for Amca's compiled binaries."""
    p = get_platform()
    if p == "windows":
        la = os.environ.get("LOCALAPPDATA") or str(Path.home() / "AppData" / "Local")
        return Path(la) / "amca" / "bin"
    return Path.home() / ".local" / "bin"


def old_amca_base() -> Path:
    """Data directory used by the OLD C-runner version of amca."""
    p = get_platform()
    if p == "windows":
        la = os.environ.get("LOCALAPPDATA") or str(Path.home() / "AppData" / "Local")
        return Path(la) / "amca"
    if p == "darwin":
        return Path.home() / "Library" / "Application Support" / "amca"
    xdg = os.environ.get("XDG_DATA_HOME", "")
    base = Path(xdg) if xdg else Path.home() / ".local" / "share"
    return base / "amca"


# ── Old-install detection ─────────────────────────────────────────────────────

class OldInstall:
    """Describes a detected old-style (C-runner) Amca installation."""

    def __init__(self, amca_base: Path) -> None:
        self.amca_base = amca_base
        self.bin_dir   = amca_base / "bin"
        self.snakes    = amca_base / "snakes"    # Python scripts
        self.templates = amca_base / "templates" # old blueprints

    def binary(self) -> Path:
        return self.bin_dir / exe("amca")

    def exists(self) -> bool:
        # Old install has a C-runner binary AND a snakes/ directory alongside it.
        return self.binary().exists() and self.snakes.is_dir()

    def __repr__(self) -> str:
        return f"OldInstall({self.amca_base})"


def detect_old_install() -> Optional[OldInstall]:
    """
    Return an OldInstall if an old-style (C-runner) amca is present.
    An install is 'old' when the runner binary + snakes/ dir both exist.
    We still return it even if a new install is also present so the user
    can be warned about the leftover and offered to clean it up.
    """
    candidate = OldInstall(old_amca_base())
    if candidate.exists():
        return candidate
    return None


def detect_new_install() -> Optional[Path]:
    """
    Return the config-root Path if a current-version amca is properly
    installed (src/config_path.py points to a dir that contains
    general_conf.json), otherwise None.
    """
    conf = read_config_path_py()
    if conf and conf.exists():
        if (conf / "Amca_config" / "general_conf.json").exists():
            return conf
    return None


# ── general_conf.json ─────────────────────────────────────────────────────────

def _general_conf_file(conf_path: Path) -> Path:
    return conf_path / "Amca_config" / "general_conf.json"


def read_general_conf(conf_path: Path) -> dict:
    p = _general_conf_file(conf_path)
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def write_general_conf(conf_path: Path, data: dict) -> None:
    p = _general_conf_file(conf_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def get_stored_bin_dir(conf_path: Path) -> Optional[Path]:
    val = read_general_conf(conf_path).get("install", {}).get("bin_dir")
    return Path(val) if val else None


def store_install_state(
    conf_path: Path, bin_dir: Path, version: str = AMCA_VERSION
) -> None:
    """Persist install metadata so update/uninstall can find everything later."""
    data = read_general_conf(conf_path)
    data.setdefault("install", {})
    data["install"]["bin_dir"]         = str(bin_dir)
    data["install"]["version"]         = version
    data["install"]["python_platform"] = get_platform()
    write_general_conf(conf_path, data)


def get_stored_version(conf_path: Path) -> Optional[str]:
    return read_general_conf(conf_path).get("install", {}).get("version")


# ── Shell-profile PATH blocks (POSIX) ─────────────────────────────────────────

def _strip_block(text: str, start: str, end: str) -> str:
    lines  = text.splitlines(keepends=True)
    result = []
    inside = False
    for line in lines:
        s = line.rstrip("\r\n")
        if s == start:  inside = True;  continue
        if s == end:    inside = False; continue
        if not inside:  result.append(line)
    return "".join(result)


def _profile_has_marker(profile: Path) -> bool:
    if not profile.exists():
        return False
    return PATH_MARKER_START in profile.read_text(encoding="utf-8", errors="replace")


def write_path_block(profile: Path, bin_dir: Path) -> None:
    """Insert (or replace) the amca PATH block in *profile*."""
    profile.parent.mkdir(parents=True, exist_ok=True)
    profile.touch()
    text = profile.read_text(encoding="utf-8", errors="replace")
    text = _strip_block(text, PATH_MARKER_START,   PATH_MARKER_END)
    text = _strip_block(text, _ALIAS_MARKER_START, _ALIAS_MARKER_END)

    is_fish = (profile.name == "config.fish")
    if is_fish:
        block = (
            f"\n{PATH_MARKER_START}\n"
            f"# Added by amca installer — do not remove unless you uninstall amca\n"
            f'fish_add_path "{bin_dir}"\n'
            f"{PATH_MARKER_END}\n"
        )
    else:
        block = (
            f"\n{PATH_MARKER_START}\n"
            f"# Added by amca installer — do not remove unless you uninstall amca\n"
            f'if ! echo "$PATH" | grep -qE "(^|:){bin_dir}(:|$)"; then\n'
            f'  export PATH="$PATH:{bin_dir}"\n'
            f"fi\n"
            f"{PATH_MARKER_END}\n"
        )
    profile.write_text(text.rstrip("\n") + "\n" + block, encoding="utf-8")


def add_to_posix_path(bin_dir: Path) -> Optional[Path]:
    """
    Write the PATH block to the first appropriate shell profile.
    If a profile already has the marker, it is updated in-place.
    Returns the profile that was written to, or None.
    """
    for profile in POSIX_PROFILES:
        if _profile_has_marker(profile):
            write_path_block(profile, bin_dir)
            return profile
    for profile in POSIX_PROFILES:
        if profile.exists():
            write_path_block(profile, bin_dir)
            return profile
    write_path_block(POSIX_PROFILES[0], bin_dir)
    return POSIX_PROFILES[0]


def remove_from_posix_path() -> list[Path]:
    """Strip amca PATH (and legacy ALIAS) blocks from ALL candidate profiles."""
    cleaned: list[Path] = []
    for profile in POSIX_PROFILES:
        if not profile.exists():
            continue
        text = profile.read_text(encoding="utf-8", errors="replace")
        if PATH_MARKER_START not in text and _ALIAS_MARKER_START not in text:
            continue
        text = _strip_block(text, PATH_MARKER_START,   PATH_MARKER_END)
        text = _strip_block(text, _ALIAS_MARKER_START, _ALIAS_MARKER_END)
        profile.write_text(text, encoding="utf-8")
        cleaned.append(profile)
    return cleaned


# ── Windows registry PATH ─────────────────────────────────────────────────────

def windows_add_to_path(bin_dir: Path) -> bool:
    try:
        import winreg
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, "Environment", 0, winreg.KEY_ALL_ACCESS
        )
        try:    old, _ = winreg.QueryValueEx(key, "PATH")
        except FileNotFoundError: old = ""
        s = str(bin_dir)
        entries = [e for e in old.split(";") if e]
        if s not in entries:
            entries.append(s)
            winreg.SetValueEx(key, "PATH", 0, winreg.REG_EXPAND_SZ, ";".join(entries))
        winreg.CloseKey(key)
        _broadcast_env_windows()
        return True
    except Exception as exc:
        print(f"  Warning: could not update Windows PATH registry: {exc}")
        return False


def windows_remove_from_path(bin_dir: Path) -> bool:
    try:
        import winreg
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, "Environment", 0, winreg.KEY_ALL_ACCESS
        )
        try:    old, _ = winreg.QueryValueEx(key, "PATH")
        except FileNotFoundError:
            winreg.CloseKey(key); return False
        s = str(bin_dir)
        entries = [e for e in old.split(";") if e and e.lower() != s.lower()]
        winreg.SetValueEx(key, "PATH", 0, winreg.REG_EXPAND_SZ, ";".join(entries))
        winreg.CloseKey(key)
        _broadcast_env_windows()
        return True
    except Exception as exc:
        print(f"  Warning: could not update Windows PATH registry: {exc}")
        return False


def _broadcast_env_windows() -> None:
    try:
        import ctypes
        ctypes.windll.user32.SendMessageW(0xFFFF, 0x001A, 0, "Environment")
    except Exception:
        pass


# ── Filesystem helpers ────────────────────────────────────────────────────────

def remove_dir(path: Path) -> None:
    if path.exists() and path.is_dir():
        shutil.rmtree(path)


def remove_file(path: Path) -> None:
    if path.exists() and path.is_file():
        path.unlink()


# ── Pure-stdlib CLI helpers ───────────────────────────────────────────────────

def query_yes_no(question: str, default: str = "yes") -> bool:
    valid   = {"yes": True, "y": True, "ye": True, "no": False, "n": False}
    prompts = {"yes": " [Y/n] ", "no": " [y/N] "}
    prompt  = prompts.get(default, " [y/n] ")
    while True:
        sys.stdout.write(question + prompt)
        sys.stdout.flush()
        choice = input().lower().strip()
        if default and choice == "":
            return valid[default]
        if choice in valid:
            return valid[choice]
        print("  Please answer yes or no.")


def ask_input(prompt: str, default: Optional[str] = None) -> str:
    display = f"{prompt} [{default}]: " if default else f"{prompt}: "
    sys.stdout.write(display)
    sys.stdout.flush()
    val = input().strip()
    return val if val else (default or "")


def hr(char: str = "─", width: int = 60) -> str:
    return char * width
