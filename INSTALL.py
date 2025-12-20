import sys
import subprocess
from pathlib import Path

# create venv


def main():
    python_path = sys.executable
    venv_path = (Path(__file__).parent / "src" / ".venv").resolve()

    if venv_path.exists():
        print(f"Virtual environment already exists at {venv_path}")
        return

    subprocess.run([python_path, "-m", "venv", str(venv_path)], check=True)
    print(f"Virtual environment created at {venv_path}")

    pip_path = venv_path / ("Scripts/pip.exe" if sys.platform == "win32" else "bin/pip")

    subprocess.run([str(pip_path), "install", "--upgrade", "pip"], check=True)


if __name__ == "__main__":
    main()
