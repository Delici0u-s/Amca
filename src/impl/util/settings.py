import json
import threading
import tempfile
import shutil
from pathlib import Path
from typing import Any, Dict, Optional, Union, Callable
import logging
import traceback
import datetime

try:
    import yaml

    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False

import pickle


class SettingsError(Exception):
    """Custom exception for configuration errors."""

    pass


backends = ("json", "yaml", "pickle")


class Settings:
    """
    A thread-safe settings manager with JSON, YAML, or Pickle backend.

    New init options:
      - on_error: "raise" | "warn" | "defaults"
          * "raise"   -> raise SettingsError on load/save problems (original strict behavior)
          * "warn"    -> log a warning, fall back to defaults (useful for production)
          * "defaults"-> silently fall back to defaults (quiet)
      - backup_bad_file: bool
          If True and a config file is corrupt it will be moved to a timestamped .corrupt.* backup.
      - error_handler: Optional[Callable[[Exception, str], None]]
          Optional callback called as error_handler(exception, context) where context is "load" or "save".
      - show_traceback: bool
          If True the full traceback will be logged when errors happen (helpful while debugging).
    """

    def __init__(
        self,
        path: Union[str, Path],
        defaults: Optional[Dict[str, Any]] = None,
        auto_save: bool = False,
        backend: str = ("json", "yaml", "pickle")[0],
        on_error: str = "warn",
        backup_bad_file: bool = True,
        error_handler: Optional[Callable[[Exception, str], None]] = None,
        show_traceback: bool = False,
    ) -> None:
        self._path = Path(path)
        self._defaults = defaults or {}
        self._values: Dict[str, Any] = {}
        self._lock = threading.RLock()
        self._auto_save = auto_save
        self._backend = backend.lower()
        self._on_error = on_error  # "raise", "warn", "defaults"
        self._backup_bad_file = bool(backup_bad_file)
        self._error_handler = error_handler
        self._show_traceback = bool(show_traceback)

        if self._backend == "yaml" and not YAML_AVAILABLE:
            raise SettingsError("YAML backend requested but PyYAML not installed.")
        if self._backend == "pickle" and not hasattr(pickle, "dump"):
            raise SettingsError("Pickle backend unavailable.")
        if self._backend not in backends:
            raise SettingsError("Settings backend unavailable")

        # configure a logger for warnings/errors
        self._logger = logging.getLogger(self.__class__.__name__)
        if not self._logger.handlers:
            # avoid adding multiple handlers in interactive sessions
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
            self._logger.addHandler(handler)
        self._logger.setLevel(logging.INFO)

        # attempt load, but handle errors according to on_error
        self.load()

    def __enter__(self) -> "Settings":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        # Save only if no exception and auto_save disabled
        if exc_type is None and not self._auto_save:
            self.save()

    def _handle_error(self, exc: Exception, context: str) -> None:
        """
        Centralized error handling. context is "load" or "save".
        """
        # call user-supplied handler first
        try:
            if self._error_handler:
                try:
                    self._error_handler(exc, context)
                except Exception as eh:
                    # user handler shouldn't break us
                    self._logger.warning("error_handler raised: %s", eh)
        except Exception:
            # swallow any exceptions from error_handler
            pass

        # log with optional traceback
        if self._show_traceback:
            tb = traceback.format_exc()
            self._logger.error("Exception during %s: %s\n%s", context, exc, tb)
        else:
            self._logger.error("Exception during %s: %s", context, exc)

        # react depending on policy
        if self._on_error == "raise":
            raise SettingsError(f"Error during {context}: {exc}") from exc
        # "warn" and "defaults" both fall through to non-raising behavior

    def load(self) -> None:
        """
        Load configuration from file, merging with defaults.
        On parse/read errors the behavior depends on self._on_error.
        """
        with self._lock:
            if not self._path.exists():
                # Initialize with defaults
                self._values = self._deepcopy(self._defaults)
                return

            try:
                data = self._read_file()
                if not isinstance(data, dict):
                    raise SettingsError("Configuration root must be a mapping.")
                self._values = self._merge(dict(self._defaults), data)
            except Exception as e:
                # Attempt to back up the bad file if configured
                try:
                    if self._backup_bad_file and self._path.exists():
                        timestamp = datetime.datetime.utcnow().strftime(
                            "%Y%m%dT%H%M%SZ"
                        )
                        bad_name = self._path.with_suffix(
                            self._path.suffix + f".corrupt.{timestamp}.bak"
                        )
                        try:
                            shutil.move(str(self._path), str(bad_name))
                            self._logger.info(
                                "Backed up corrupt config to %s", bad_name
                            )
                        except Exception as be:
                            self._logger.warning(
                                "Failed to back up corrupt config: %s", be
                            )
                except Exception:
                    # ensure backup attempts don't mask original error handling
                    pass

                # call centralized error handling
                self._handle_error(e, "load")

                # if policy is "defaults" or "warn", fall back to defaults instead of aborting
                if self._on_error in ("warn", "defaults"):
                    self._values = self._deepcopy(self._defaults)
                    return

    def save(self) -> None:
        """
        Persist current settings to disk atomically, creating parent directories as needed.
        """
        with self._lock:
            # Ensure parent directory exists
            try:
                self._path.parent.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                self._handle_error(e, "save")
                if self._on_error == "raise":
                    return
                # if not raising, proceed no further
                return

            raw = self._values
            # Write to temporary file in same directory and move into place
            mode = "wb" if self._backend == "pickle" else "w"
            temp = None
            try:
                temp = tempfile.NamedTemporaryFile(
                    mode=mode, delete=False, dir=str(self._path.parent)
                )
                try:
                    self._dump_file(raw, temp)
                finally:
                    # ensure file is flushed and closed so move on Windows will succeed
                    try:
                        temp.flush()
                    except Exception:
                        pass
                    try:
                        temp.close()
                    except Exception:
                        pass
                shutil.move(temp.name, str(self._path))
            except Exception as e:
                # cleanup temp file if present
                try:
                    if temp is not None:
                        Path(temp.name).unlink(missing_ok=True)
                except Exception:
                    pass

                self._handle_error(e, "save")
                # if policy=="raise", _handle_error already raised; otherwise just return
                return

    def get(self, key: str, default: Any = None) -> Any:
        """
        Retrieve a setting by dotted key, falling back to provided default or defaults.
        """
        with self._lock:
            parts = key.split(".")
            node = self._values
            for part in parts:
                if isinstance(node, dict) and part in node:
                    node = node[part]
                else:
                    return default
            return node

    def set(self, key: str, value: Any) -> None:
        """
        Set a setting by dotted key, creating nested structure as needed.
        """
        with self._lock:
            parts = key.split(".")
            node = self._values
            for part in parts[:-1]:
                if part not in node or not isinstance(node[part], dict):
                    node[part] = {}
                node = node[part]
            node[parts[-1]] = value
            if self._auto_save:
                # let save handle its own errors according to policy
                self.save()

    def default(self, key: str, value: Any) -> bool:
        """
        Set the value only if key is not already present. Returns True if set.
        """
        with self._lock:
            parts = key.split(".")
            node = self._values
            for part in parts[:-1]:
                if part not in node or not isinstance(node[part], dict):
                    node[part] = {}
                node = node[part]
            leaf = parts[-1]
            if leaf not in node:
                node[leaf] = value
                if self._auto_save:
                    self.save()
                return True
            return False

    def update(self, data: Dict[str, Any]) -> None:
        """
        Bulk-update settings via dict merge.
        """
        with self._lock:
            self._values = self._merge(self._values, data)
            if self._auto_save:
                self.save()

    def reset(self) -> None:
        """
        Reset settings to defaults (in-memory only).
        """
        with self._lock:
            self._values = self._deepcopy(self._defaults)
            if self._auto_save:
                self.save()

    def as_dict(self) -> Dict[str, Any]:
        """
        Export a deep copy of current settings.
        """
        with self._lock:
            return self._deepcopy(self._values)

    def _read_file(self) -> Any:
        """
        Read raw data from disk according to backend.
        """
        if self._backend == "pickle":
            with self._path.open("rb") as f:
                return pickle.load(f)
        text = self._path.read_text(encoding="utf-8")
        if not text:
            return {}
        if self._backend == "json":
            return json.loads(text)
        else:
            return yaml.safe_load(text)

    def _dump_file(self, data: Any, stream) -> None:
        """
        Dump raw data to stream according to backend.
        """
        if self._backend == "pickle":
            # Use highest protocol for speed and efficiency
            pickle.dump(data, stream, protocol=pickle.HIGHEST_PROTOCOL)
        elif self._backend == "json":
            # stream is a text file handle
            json.dump(data, stream, indent=2, ensure_ascii=False)
        else:
            yaml.safe_dump(data, stream)

    @staticmethod
    def _merge(a: Dict[str, Any], b: Dict[str, Any]) -> Dict[str, Any]:
        """
        Recursively merge dict b into a.
        """
        for key, val in b.items():
            if key in a and isinstance(a[key], dict) and isinstance(val, dict):
                a[key] = Settings._merge(a[key], val)
            else:
                a[key] = val
        return a

    @staticmethod
    def _deepcopy(obj: Any) -> Any:
        """
        Perform a deep copy of nested dicts/lists.
        """
        if isinstance(obj, dict):
            return {k: Settings._deepcopy(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [Settings._deepcopy(v) for v in obj]
        else:
            return obj


if __name__ == "__main__":
    # fixed the string quoting here (was previously invalid)
    s: Settings = Settings(
        Path(__file__).parent / "settings_test" / "settings.json",
        backend="json",
        on_error="warn",  # 'raise'|'warn'|'defaults'
        backup_bad_file=True,
        show_traceback=True,
    )
    s.load()
    s.default(
        "Last_Session.Input", "No previous input"
    )  # if omitted s.get would return None
    print("Previous input:", s.get("Last_Session.Input"))
    s.set("Last_Session.Input", input("Next output:    "))
    s.save()
