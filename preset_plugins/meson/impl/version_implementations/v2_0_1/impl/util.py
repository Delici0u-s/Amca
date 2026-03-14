"""
util.py
Shared utilities for the v2_0_1 meson plugin.
"""

import shlex
import shutil
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .....amca.logger import Logger


# ── Shell argument tokeniser ──────────────────────────────────────────────────

def parse_args_shlex(s: str, posix: bool = True) -> list[str]:
    """
    Tokenise *s* exactly as a POSIX shell would.

    Complexity: O(n) time and space.

    Raises
    ------
    ValueError : on unterminated quotes or trailing backslash.
    """
    try:
        return shlex.split(s, posix=posix)
    except ValueError as exc:
        raise ValueError(f"Malformed argument string: {exc}") from exc


def parse_args_manual(s: str) -> list[str]:
    """
    Tokenise *s* with shell-like rules, implemented as a single-pass FSM.
    Zero stdlib dependency beyond builtins.

    Raises
    ------
    ValueError : on unterminated quotes.
    """
    OUTSIDE, IN_TOKEN, IN_SINGLE, IN_DOUBLE = range(4)

    tokens: list[str] = []
    buf: list[str] = []
    state = OUTSIDE

    i = 0
    while i < len(s):
        ch = s[i]

        if state == OUTSIDE:
            if ch == "'":
                state = IN_SINGLE
            elif ch == '"':
                state = IN_DOUBLE
            elif ch == '\\':
                i += 1
                if i >= len(s):
                    raise ValueError("Trailing backslash")
                buf.append(s[i])
                state = IN_TOKEN
            elif ch.isspace():
                pass
            else:
                buf.append(ch)
                state = IN_TOKEN

        elif state == IN_TOKEN:
            if ch == "'":
                state = IN_SINGLE
            elif ch == '"':
                state = IN_DOUBLE
            elif ch == '\\':
                i += 1
                if i >= len(s):
                    raise ValueError("Trailing backslash")
                buf.append(s[i])
            elif ch.isspace():
                tokens.append("".join(buf))
                buf.clear()
                state = OUTSIDE
            else:
                buf.append(ch)

        elif state == IN_SINGLE:
            if ch == "'":
                state = IN_TOKEN
            else:
                buf.append(ch)

        elif state == IN_DOUBLE:
            if ch == '"':
                state = IN_TOKEN
            elif ch == '\\' and i + 1 < len(s) and s[i + 1] in ('"', '\\'):
                i += 1
                buf.append(s[i])
            else:
                buf.append(ch)

        i += 1

    if state in (IN_SINGLE, IN_DOUBLE):
        raise ValueError("Unterminated quote")

    if buf:
        tokens.append("".join(buf))

    return tokens


# ── Tool availability checks ──────────────────────────────────────────────────

def check_meson(logger: "Logger") -> bool:
    """
    Verify that `meson` is available in PATH.

    Returns False (without exiting) so callers can propagate pipeline failure
    through the normal bool return convention.
    """
    if shutil.which("meson") is not None:
        return True

    logger.error(
        "'meson' not found in PATH.\n"
        "  Fedora/RHEL : sudo dnf install meson\n"
        "  Debian/Ubuntu: sudo apt install meson\n"
        "  pip (any OS) : pip install meson\n"
        "  https://mesonbuild.com/Getting-meson.html"
    )
    return False


def check_ninja(logger: "Logger") -> bool:
    """
    Verify that a ninja backend is available in PATH.
    Accepts `ninja`, `ninja-build`, or `samu`.
    """
    for name in ("ninja", "ninja-build", "samu"):
        if shutil.which(name) is not None:
            return True

    logger.error(
        "No ninja-compatible backend found in PATH (tried: ninja, ninja-build, samu).\n"
        "  Fedora/RHEL : sudo dnf install ninja-build\n"
        "  Debian/Ubuntu: sudo apt install ninja-build\n"
        "  pip (any OS) : pip install ninja\n"
        "  https://ninja-build.org"
    )
    return False
