from impl.util.github import gen_github_api_link
from impl.util.settings import Settings
import sys
from pathlib import Path


class _SettingsManager:
    def __init__(self):
        self._all_settings: dict[str, Settings] = {}

    def get(self, key: str) -> Settings:
        """Lazy-load and return a setting by key"""
        if key not in self._all_settings:
            self._load(key)
        return self._all_settings[key]

    def __getitem__(self, key: str) -> Settings:
        """Allow dictionary-style access: settings_manager['general']"""
        return self.get(key)

    def _load(self, key: str):
        root_path = Path(sys.argv[0]).parent.parent.resolve()
        config_path = root_path / "config"
        config_path.mkdir(exist_ok=True)

        if key == "general":
            general_config = config_path / "general_conf.json"
            s = Settings(str(general_config), auto_save=True, backend="json")
            s.default("extreamly_important.greet_user", True)
            s.default("debug", False)
            s.default("amca_root.folder_name", ".Amca")
            s.default("amca_root.recursive_search_depth", 5)
            s.default("amca_root.ignored_paths", [])
            s.default("default_file_editor", "nano")
            self._all_settings["general"] = s

        elif key == "plugins":
            plugin_path = config_path / "plugins"
            plugin_path.mkdir(exist_ok=True)
            plugin_conf = plugin_path / "plugin_conf.json"
            installed_plugins = plugin_path / "installed_plugins"
            installed_plugins.mkdir(exist_ok=True)
            s = Settings(str(plugin_conf), auto_save=True, backend="json")
            s.default("generic.exit_on_plugin_error", False)
            s.default("generic.exit_on_plugin_not_found", False)
            s.default("generic.plugin_path", str(installed_plugins))
            s.default("enabled_plugins", [])
            s.default("logging.warn_if_plugin_not_found", True)
            s.default("logging.warn_if_plugin_arg_not_enabled", True)
            s.default("logging.print_loaded", True)
            s.default(
                "plugin_sources",
                [
                    gen_github_api_link(
                        "Delici0u-s", "Amca", "rewrite", "preset_plugins"
                    )
                ],
            )
            self._all_settings["plugins"] = s


_settings_manager = _SettingsManager()

general_settings = _settings_manager.get("general")
plugin_settings = _settings_manager["plugins"]
