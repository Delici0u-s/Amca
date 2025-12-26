import json
import threading
import tempfile
import shutil
from pathlib import Path
from typing import Any, Dict, Optional, Union

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

    Supports nested keys via dot notation, default values, atomic writes,
    optional auto-save on modification, and binary serialization for pickle.
    """

    def __init__(
        self,
        path: Union[str, Path],
        defaults: Optional[Dict[str, Any]] = None,
        auto_save: bool = False,
        backend: str = ("json", "yaml", "pickle")[0],
    ) -> None:
        self._path = Path(path)
        self._defaults = defaults or {}
        self._values: Dict[str, Any] = {}
        self._lock = threading.RLock()
        self._auto_save = auto_save
        self._backend = backend.lower()
        if self._backend == "yaml" and not YAML_AVAILABLE:
            raise SettingsError("YAML backend requested but PyYAML not installed.")
        if self._backend == "pickle" and not hasattr(pickle, "dump"):
            raise SettingsError("Pickle backend unavailable.")
        if self._backend not in backends:
            raise SettingsError("Settings backend unavailable")

        self.load()

    def __enter__(self) -> "Settings":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        # Save only if no exception and auto_save disabled
        if exc_type is None and not self._auto_save:
            self.save()

    def load(self) -> None:
        """
        Load configuration from file, merging with defaults.
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
            except (json.JSONDecodeError, yaml.YAMLError, pickle.UnpicklingError) as e:
                raise SettingsError(f"Invalid configuration file: {e}")

    def save(self) -> None:
        """
        Persist current settings to disk atomically, creating parent directories as needed.
        """
        with self._lock:
            # Ensure parent directory exists
            try:
                self._path.parent.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                raise SettingsError(f"Failed to create config directory: {e}")

            raw = self._values
            # Write to temporary file in same directory and move into place
            mode = "wb" if self._backend == "pickle" else "w"
            temp = tempfile.NamedTemporaryFile(
                mode, delete=False, dir=str(self._path.parent)
            )
            try:
                self._dump_file(raw, temp)
                temp.flush()
                temp.close()
                shutil.move(temp.name, str(self._path))
            finally:
                # Cleanup temp file if still present
                try:
                    Path(temp.name).unlink()
                except Exception:
                    pass

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
    s: Settings = Settings(
        f"{Path(__file__).parent / "settings_test/settings"}", backend="json"
    )
    s.load()
    s.default(
        "Last_Session.Input", "No previous input"
    )  # if ommitted s.get would return None
    print("Previous input:", s.get("Last_Session.Input"))
    s.set("Last_Session.Input", input("Next output:    "))
    s.save()
