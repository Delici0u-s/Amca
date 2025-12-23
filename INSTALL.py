import sys
import subprocess
from pathlib import Path
import tempfile


# create venv
def create_venv() -> Path | None:
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
    runner_str_code = r"""
#include <stdio.h>
#include <stdlib.h>
#ifdef _WIN32
#include <process.h> // _execvp
#define execvp _execvp
#else
#include <unistd.h> // execvp
#endif

int main(int argc, char *argv[]) {{
    char *exec_argv[argc + 2];
    exec_argv[0] = "{python}";
    exec_argv[1] = "{script}";

    for (int i = 1; i < argc; ++i) {{
        exec_argv[i + 1] = argv[i];
    }}

    exec_argv[argc + 1] = NULL;

    execvp(exec_argv[0], exec_argv);

    perror("execvp failed");
    return 1;
}}
"""

    # Platform-specific Python executable
    venv_python = venv_path / (
        "Scripts/python.exe" if sys.platform == "win32" else "bin/python3"
    )

    # Paths
    src_path = (Path(__file__).parent / "src").resolve()
    compiled_path = (Path(__file__).parent / "runners").resolve()
    compiled_path.mkdir(exist_ok=True)

    apps = [src_path / i for i in ["amca.py", "amcapl.py"]]

    for app in apps:
        # Fill in placeholders
        code = runner_str_code.format(python=venv_python, script=app)

        # Write C code to a temp file
        with tempfile.NamedTemporaryFile("w", suffix=".c", delete=False) as f:
            f.write(code)
            c_file_path = Path(f.name)

        # Determine compiler
        if sys.platform == "win32":
            compiler = "gcc"  # You can switch to "cl" if MSVC is installed
            output_file = compiled_path / (app.stem + ".exe")
        else:
            compiler = "cc"
            output_file = compiled_path / app.stem

        # Compile the runner
        subprocess.run([compiler, str(c_file_path), "-o", str(output_file)], check=True)
        print(f"Runner created: {output_file}")

    return venv_python


def main():
    venv_path: Path | None = create_venv()

    if venv_path is not None:
        create_runners(venv_path)


if __name__ == "__main__":
    main()
