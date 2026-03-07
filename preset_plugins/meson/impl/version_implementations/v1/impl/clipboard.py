import os
import shutil
import subprocess


def copy(text: str) -> None:
    if os.name == 'nt':
        os.system(f'echo {text.strip()} | clip')
    elif hasattr(os, 'uname') and os.uname().sysname == 'Darwin':
        p = subprocess.Popen(['pbcopy'], stdin=subprocess.PIPE)
        p.communicate(input=text.encode())
    else:
        if shutil.which('wl-copy'):
            p = subprocess.Popen(['wl-copy'], stdin=subprocess.PIPE)
            p.communicate(input=text.encode())
        elif shutil.which('xclip'):
            p = subprocess.Popen(['xclip', '-selection', 'clipboard'], stdin=subprocess.PIPE)
            p.communicate(input=text.encode())
        else:
            print("[v1] No clipboard utility found (install xclip or wl-clipboard).")
