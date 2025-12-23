import sys
import subprocess
from pathlib import Path
import tempfile


# create venv
def create_venv():  # -> Path | None
    try:

        python_exec = sys.executable
        venv_path = (Path(__file__).parent / "src" / ".venv").resolve()

        if venv_path.exists():
            print(
                f"Virtual environment already exists at {venv_path}\n    Remove it to create a new one"
            )
            return venv_path
        subprocess.run([python_exec, "-m", "venv", str(venv_path)], check=True)
        print(f"Virtual environment created at {venv_path}")

        pip_path = venv_path / (
            "Scripts/pip.exe" if sys.platform == "win32" else "bin/pip"
        )

        subprocess.run([str(pip_path), "install", "--upgrade", "pip"], check=True)
        return venv_path
    except:
        return None


def create_runners(venv_path: Path) -> Path:
    runner_str_code: str = """
#include <stdio.h>

#ifdef _WIN32
#include <process.h> 
# define execvp _execvp
#else
#include <unistd.h> // execvp
#endif

int main(int argc, char *argv[]) {{

    // +2 because argv[0] = program name, argv[1] = script, plus NULL terminator
    char *exec_argv[argc + 2];

    exec_argv[0] = PYTHON_EXEC;   // Python interpreter
    exec_argv[1] = PYTHON_FILE;   // Script to run

    // Pass through any extra arguments
    for (int i = 1; i < argc; ++i) {{
        exec_argv[i + 1] = argv[i];
    }}

    exec_argv[argc + 1] = NULL;

    //return execvp(PYTHON_EXEC, exec_argv);
#ifdef _WIN32
    return _spawnvp(_P_WAIT, PYTHON_EXEC, exec_argv);
#else
    return execvp(PYTHON_EXEC, exec_argv);
#endif
}}
    """

    possible_paths = [
        venv_path / "bin" / "pytho3n",
        venv_path / "bin" / "python",
        venv_path / "Scripts" / "python3.exe",
        venv_path / "Scripts" / "python.exe",
    ]

    venv_python_location = Path()
    for path in possible_paths:
        if path.exists():
            venv_python_location = path
            break

    if venv_python_location is None:
        print("Could not find venv python executable")
        SystemExit(1)

    # Source and output directories
    src_path: Path = (Path(__file__).parent / "src").resolve()
    compiled_path: Path = (Path(__file__).parent / "runners").resolve()
    compiled_path.mkdir(exist_ok=True)

    # Scripts to create runners for
    amca_scripts = ["amca.py", "amcapl.py"]
    for script in amca_scripts:
        script_path = src_path / script

        # Define the macros for this compilation
        macros = f'#define PYTHON_EXEC "{venv_python_location}"\n#define PYTHON_FILE "{script_path}"\n'

        # Path to write the C source code (inside compiled_path)
        c_file_path = compiled_path / f"{script_path.stem}.c"

        # Write C code to file
        with open(c_file_path, "w") as f:
            f.write(macros)
            f.write(runner_str_code)

        # Compile the C code
        output_path = compiled_path / script_path.stem
        subprocess.run(["cc", str(c_file_path), "-o", str(output_path)], check=True)

    return venv_python_location


def main():
    # venv_path: Path | None = create_venv()
    venv_path = create_venv()

    if venv_path is not None:
        create_runners(venv_path)


if __name__ == "__main__":
    main()
