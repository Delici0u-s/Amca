import sys, os
import subprocess
from pathlib import Path
from typing import Optional, Set, Tuple
import shutil
from src.impl.util.input import query_yes_no

# Track installed packages WITH versions
installed_pip_dependencies: Set[Tuple[str, str]] = set()

# Explicit unset state
python_exec_path: Optional[Path] = None


def remove_dir(path: Path) -> None:
    if path.exists() and path.is_dir():
        shutil.rmtree(path)


def remove_file(path: Path) -> None:
    if path.exists() and path.is_file():
        path.unlink()


def identify_python_path_from_venv(venv_path: Path) -> None:
    """
    Locate the Python executable inside a virtual environment.
    """
    global python_exec_path

    if python_exec_path is not None:
        return

    possible_paths = [
        venv_path / "bin" / "python3",
        venv_path / "Scripts" / "python3.exe",
        venv_path / "bin" / "python",
        venv_path / "Scripts" / "python.exe",
    ]

    for path in possible_paths:
        if path.exists():
            python_exec_path = path
            return

    print(f"Python executable not found in {venv_path}")
    raise SystemExit(1)


def _ensure_python_path() -> None:
    if python_exec_path is None:
        raise RuntimeError("Virtual environment Python path not initialized")


def package_install(package: str, version: str, print_output: bool = False) -> bool:
    """
    Install a specific package version into the venv.
    """
    _ensure_python_path()

    package = package.lower()
    key = (package, version)

    if key in installed_pip_dependencies:
        return True

    try:
        cmd = [
            str(python_exec_path),
            "-m",
            "pip",
            "install",
            f"{package}=={version}",
        ]

        print(f"Installing: {package}, with version {version}")

        subprocess.run(
            cmd,
            check=True,
            stdout=None if print_output else subprocess.DEVNULL,
            stderr=None if print_output else subprocess.DEVNULL,
        )

        installed_pip_dependencies.add(key)
        return True

    except subprocess.CalledProcessError as e:
        print(f"Failed to install {package}=={version}")
        print(e)
        return False


# returns -7765 if execution failed
def package_call(module: str, *args, print_output: bool = False) -> int:
    _ensure_python_path()

    try:
        result = subprocess.run(
            [str(python_exec_path), "-m", module, *map(str, args)],
            check=True,
            stdout=None if print_output else subprocess.DEVNULL,
            stderr=None if print_output else subprocess.DEVNULL,
        )
        return result.returncode

    except subprocess.CalledProcessError as e:
        print(f"Module call failed: {module}")
        print(e)
        return -7765


def create_venv() -> None:
    python_exec = sys.executable
    venv_path = (Path(__file__).parent / "compiled" / ".venv").resolve()

    print_output: bool = False

    if not venv_path.exists():
        subprocess.run(
            [python_exec, "-m", "venv", str(venv_path)],
            check=True,
            stdout=None if print_output else subprocess.DEVNULL,
            stderr=None if print_output else subprocess.DEVNULL,
        )
        print(f"Virtual environment created at {venv_path}")
    else:
        print(f"Using existing venv at {venv_path}")

    identify_python_path_from_venv(venv_path)

    # ALWAYS ensure pip works
    subprocess.run(
        [str(python_exec_path), "-m", "ensurepip", "--upgrade"],
        check=True,
        stdout=None if print_output else subprocess.DEVNULL,
        stderr=None if print_output else subprocess.DEVNULL,
    )

    package_install("pip", "24.0")


def get_conf_path(debug: bool = False) -> Path:
    outp = Path()
    if debug:
        return Path(__file__).parent / "AmcaConfigTest"

    # eval default path:
    if sys.platform.startswith("linux"):
        config_path = Path.home() / ".config"
    elif sys.platform.startswith("win"):
        config_path = Path.home() / "Documents"
    else:
        raise OSError(f"Unsupported operating system: {sys.platform}")

    amca_conf_path = config_path / "Amca"

    print("Default amca_config location: ")
    print(amca_conf_path)

    # override amca_conf_path by user if he wishes
    # 1) Environment variable override
    env_override = os.environ.get("AMCA_CONFIG_PATH") or os.environ.get("AMCA_PATH")
    if env_override:
        try:
            env_path = Path(env_override).expanduser().resolve()
            print(f"Overriding from environment variable: {env_path}")
            amca_conf_path = env_path
        except Exception as e:
            print(f"Warning: invalid path in environment variable: {e}")
    elif sys.stdin and sys.stdin.isatty():
        try:
            inp = input(
                f"Press Enter to accept default or type a custom path to override: "
            ).strip()
            if inp:
                try:
                    user_path = Path(inp).expanduser().resolve()
                    print(f"Using user-provided path: {user_path}")
                    amca_conf_path = user_path
                except Exception as e:
                    print(
                        f"Warning: invalid path supplied: {e}. Falling back to default."
                    )
        except (KeyboardInterrupt, EOFError):
            print("Input cancelled. Using default path.")

    if amca_conf_path.exists():
        if query_yes_no("Amca_root dir already exists, do you wish to remove it?"):
            shutil.rmtree(amca_conf_path)

    amca_conf_path.mkdir(parents=True, exist_ok=True)

    src_fil = Path(__file__).parent / "src" / "config_path.py"

    src_config_file = f"""config_path = \"{str(amca_conf_path)}\"

# yes, i know this dumb as shit, but idk how to avoid symlink stuff lol

# TODO: Implement automatically hard_writing this in INSTALL.py, with a user defined custom config path,
# linux usually ~/.config/Amca
# windows usually HOME/Documents/Amca
    """

    with open(src_fil, "w") as f:
        f.write(src_config_file)

    return outp


def create_compiled():
    if package_install("pyinstaller", "6.10.0"):
        src_path: Path = (Path(__file__).parent / "src").resolve()
        compiled_path: Path = (Path(__file__).parent / "compiled").resolve()
        compiled_path.mkdir(exist_ok=True)

        # Scripts to create compiled for
        amca_scripts = ["amca.py", "amcapl.py"]
        for script in amca_scripts:
            script_path = src_path / script
            print(f"Creating {script.split('.')[0]} executable")
            package_call(
                "PyInstaller",
                script_path,
                "--distpath",
                compiled_path,
                "--onedir",
                "--strip",
                "--noconfirm",
                "--clean",
            )
        root = Path(__file__).parent
        build_path = root / "build"
        remove_dir(build_path)
        for script in amca_scripts:
            remove_file(root / (script.split(".")[0] + ".spec"))
    else:
        print("Could not create executables, failed to install pyinstaller")
        raise SystemExit(1)


def main():
    get_conf_path()
    # venv_path: Path | None = create_venv()
    create_venv()
    package_install("InquirerPy", "0.3.3")
    package_install("requests", "2.31.0")
    create_compiled()


if __name__ == "__main__":
    main()
