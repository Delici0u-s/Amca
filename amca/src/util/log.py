from pathlib import Path
import sys, os, time
from typing import Optional


def supports_color() -> bool:
    return sys.stdout.isatty() and os.environ.get("TERM", "") not in ("dumb", "")


class Logger:
    """
    Lightweight cross-platform logger with flexible output control:
      - Levels: INFO, SUCCESS, WARN, ERROR, FATAL
      - warnings_to_stdio_too: True -> warnings to stdout, False -> warnings to stderr
      - log_prefix_level: "None", "minimal", "simple", "normal", "verbose"
      - Modes: console, file, both, silent
    """

    _PREFIX_LEVELS = {"None": 0, "minimal": 1, "simple": 2, "normal": 3, "verbose": 4}

    _TAGS = {
        "INFO": "[INFO]",
        "SUCCESS": "[SUCCESS]",
        "WARN": "[WARN]",
        "ERROR": "[ERROR]",
        "FATAL": "[FATAL]",
    }

    _LEVEL_PRIORITY = {
        "INFO": 1,
        "SUCCESS": 2,
        "WARN": 3,
        "ERROR": 4,
        "FATAL": 5,
    }

    def __init__(
        self,
        log_path: Optional[str | Path] = None,
        warnings_to_stdio_too: bool = True,
        log_prefix_level: str = "normal",
        console_enabled: bool = True,
        file_enabled: bool = True,
        min_log_level: str = "INFO",
    ) -> None:
        self.warnings_to_stdio_too = warnings_to_stdio_too
        self.prefix_level = self._PREFIX_LEVELS.get(log_prefix_level, 2)
        self.logger_name = Path(sys.argv[0]).stem or "main"

        # Output control
        self.console_enabled = console_enabled
        self.file_enabled = file_enabled
        self.min_level = min_log_level

        # File logging setup (lazy open)
        self.log_file = None
        if log_path and self.file_enabled:
            p = Path(log_path)
            p.parent.mkdir(parents=True, exist_ok=True)
            self.log_file = open(p, "a", encoding="utf-8", buffering=1)

        # Color support
        self._use_color = supports_color()
        self._colors = {
            "INFO": "",
            "SUCCESS": "\033[32m" if self._use_color else "",
            "WARN": "\033[33m" if self._use_color else "",
            "ERROR": "\033[31m" if self._use_color else "",
            "FATAL": "\033[1;31m" if self._use_color else "",
        }
        self._reset = "\033[0m" if self._use_color else ""

        # Fast references
        self._stdout_write = sys.stdout.write
        self._stderr_write = sys.stderr.write

    # Timestamp helpers
    @staticmethod
    def _ts_normal() -> str:
        return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    @staticmethod
    def _ts_simple() -> str:
        return time.strftime("%H:%M:%SZ", time.gmtime())

    def _format(self, level: str, msg: Optional[str]) -> tuple[str, str]:
        message = "" if msg is None else str(msg)
        tag = self._TAGS[level]
        col_tag = f"{self._colors[level]}{tag}{self._reset}"

        if self.prefix_level == 0:  # None
            return f"{message}\n", f"{message}\n"
        elif self.prefix_level == 1:  # minimal
            prefix_col, prefix_plain = col_tag, tag
        elif self.prefix_level == 2:  # simple
            ts = self._ts_simple()
            prefix_col, prefix_plain = f"{ts} {col_tag}", f"{ts} {tag}"
        elif self.prefix_level == 3:  # normal
            ts = self._ts_normal()
            prefix_col, prefix_plain = f"{ts} {col_tag}", f"{ts} {tag}"
        else:  # verbose
            ts = self._ts_normal()
            ctx = f"(logger={self.logger_name} pid={os.getpid()})"
            prefix_col, prefix_plain = f"{ts} {col_tag} {ctx}", f"{ts} {tag} {ctx}"

        if message:
            return f"{prefix_col} {message}\n", f"{prefix_plain} {message}\n"
        return f"{prefix_col}\n", f"{prefix_plain}\n"

    def _write(self, stream_write, colored: str, plain: str, level: str):
        # Skip messages below min_level
        if self._LEVEL_PRIORITY[level] < self._LEVEL_PRIORITY[self.min_level]:
            return
        # Skip entirely if silent
        if not self.console_enabled and not self.file_enabled:
            return
        if self.console_enabled:
            stream_write(colored)
        if self.file_enabled and self.log_file:
            try:
                self.log_file.write(plain)
            except Exception:
                pass

    # Public API
    def log(self, msg: Optional[str] = None) -> None:
        if not (self.console_enabled or self.file_enabled):
            return
        c, p = self._format("INFO", msg)
        self._write(self._stdout_write, c, p, "INFO")

    def success(self, msg: Optional[str] = None) -> None:
        if not (self.console_enabled or self.file_enabled):
            return
        c, p = self._format("SUCCESS", msg)
        self._write(self._stdout_write, c, p, "SUCCESS")

    def warn(self, msg: Optional[str] = None) -> None:
        if not (self.console_enabled or self.file_enabled):
            return
        c, p = self._format("WARN", msg)
        if self.warnings_to_stdio_too and self.console_enabled:
            self._write(self._stdout_write, c, p, "WARN")
        else:
            self._write(self._stderr_write, c, p, "WARN")

    def error(self, msg: Optional[str] = None) -> None:
        if not (self.console_enabled or self.file_enabled):
            return
        c, p = self._format("ERROR", msg)
        self._write(self._stderr_write, c, p, "ERROR")

    def ERROR(self, msg: Optional[str] = None, code: int = 1) -> None:
        if not (self.console_enabled or self.file_enabled):
            raise SystemExit(code)
        c, p = self._format("FATAL", msg)
        self._write(self._stderr_write, c, p, "FATAL")
        try:
            sys.stdout.flush()
            sys.stderr.flush()
            if self.log_file:
                self.log_file.flush()
                self.log_file.close()
        finally:
            raise SystemExit(code)

    # Mode control API
    def set_mode(self, mode: str = ["console", "file", "both", "silent"][2]):
        mode = mode.lower()
        if mode == "console":
            self.console_enabled, self.file_enabled = True, False
        elif mode == "file":
            self.console_enabled, self.file_enabled = False, True
        elif mode == "both":
            self.console_enabled, self.file_enabled = True, True
        elif mode == "silent":
            self.console_enabled, self.file_enabled = False, False

    def enable_console(self):
        self.console_enabled = True

    def disable_console(self):
        self.console_enabled = False

    def enable_file(self):
        self.file_enabled = True

    def disable_file(self):
        self.file_enabled = False

    def disable_all(self):
        self.console_enabled = False
        self.file_enabled = False

    def set_min_level(self, level: str):
        if level not in self._TAGS:
            raise ValueError(f"Unknown log level: {level}")
        self.min_level = level

    def __del__(self):
        if self.log_file:
            try:
                self.log_file.close()
            except Exception:
                pass


if __name__ == "__main__":
    log = Logger(log_path="app.log")
    log.log("Starting service")
    log.success("Service started successfully")
    log.set_mode("file")
    log.warn("Low memory warning (file only)")
    log.set_mode("console")
    log.error("Connection failed (console only)")
    log.set_mode("silent")
    log.log("This will not appear anywhere")
    log.set_mode("both")
    log.ERROR("Fatal crash", 2)


glog: Logger = Logger(
    log_path=(Path(__file__) / ".." / ".." / ".." / "logs" / "global_log.log")
)
