"""
parse_args.py
Convert a string to a list of tokens using console/shell parameter behaviour.

Two implementations are provided:
  - parse_args_shlex  : wraps shlex.split — O(n), handles POSIX quoting & escapes
  - parse_args_manual : hand-rolled finite-state parser — same semantics, zero deps
"""

import shlex
from typing import Union


# ── Option A: shlex.split wrapper ────────────────────────────────────────────

def parse_args_shlex(s: str, posix: bool = True) -> list[str]:
    """
    Tokenise *s* exactly as a POSIX shell would.

    Rules
    -----
    - Tokens are delimited by unquoted whitespace.
    - Single-quoted strings are taken literally  ('it\\'s' → it\\'s).
    - Double-quoted strings honour backslash escapes  ("hello\\nworld" → hello\\nworld).
    - Backslash outside quotes escapes the next character.

    Parameters
    ----------
    s     : Raw command string, e.g.  'cp -r "my dir" dest'
    posix : Use POSIX mode (default True). Set False to keep surrounding quotes.

    Returns
    -------
    List of token strings.

    Raises
    ------
    ValueError : on unterminated quotes or trailing backslash.

    Complexity: O(n) time and space in the length of *s*.
    """
    try:
        return shlex.split(s, posix=posix)
    except ValueError as exc:
        raise ValueError(f"Malformed argument string: {exc}") from exc


# ── Option B: manual finite-state parser ─────────────────────────────────────

def parse_args_manual(s: str) -> list[str]:
    """
    Tokenise *s* with shell-like rules, implemented as a single-pass FSM.

    States
    ------
    DEFAULT      : between tokens; skip whitespace, open quotes, or start token
    IN_TOKEN     : accumulating an unquoted token
    IN_SINGLE    : inside '...' (no escape processing)
    IN_DOUBLE    : inside "..." (backslash escapes \\ and \")

    Advantages over shlex
    ---------------------
    - No stdlib dependency.
    - Explicit state machine is easier to audit or extend.
    - Identical O(n) complexity.

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
                # Escaped char starts a new token
                i += 1
                if i >= len(s):
                    raise ValueError("Trailing backslash")
                buf.append(s[i])
                state = IN_TOKEN
            elif ch.isspace():
                pass  # skip inter-token whitespace
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
                state = IN_TOKEN  # stay in token, just left the quote
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


# ── Quick demo ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    cases = [
        r'cp -r "my folder" /dest',
        r"echo 'don'\''t panic'",
        r'git commit -m "fix: handle \"edge\" case"',
        r'python script.py --name=Alice --verbose',
        r'',
    ]

    for raw in cases:
        a = parse_args_shlex(raw)
        b = parse_args_manual(raw)
        match = "✓" if a == b else "✗ MISMATCH"
        print(f"{match}  input : {raw!r}")
        print(f"       tokens: {a}\n")
