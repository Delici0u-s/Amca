import sys
import subprocess
from pathlib import Path
from typing import Optional, Set, Tuple
import shutil

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
    venv_path = (Path(__file__).parent / "src" / ".venv").resolve()

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


def create_runners():
    if package_install("pyinstaller", "6.2.0"):
        src_path: Path = (Path(__file__).parent / "src").resolve()
        compiled_path: Path = (Path(__file__).parent / "runners").resolve()
        compiled_path.mkdir(exist_ok=True)

        # Scripts to create runners for
        amca_scripts = ["amca.py", "amcapl.py"]
        for script in amca_scripts:
            script_path = src_path / script
            print(f"Creating {script.split('.')[0]} executable")
            package_call(
                "PyInstaller",
                script_path,
                "--distpath",
                compiled_path,
                "--onefile",
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
    # venv_path: Path | None = create_venv()
    create_venv()
    create_runners()


if __name__ == "__main__":
    main()
