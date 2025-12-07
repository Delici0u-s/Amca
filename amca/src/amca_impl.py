import os, sys
from pathlib import Path
from src.util.settings import Settings

import src.plugin_stuff.checker as plugin_checker
import src.plugin_stuff.loader as plugin_loader

from src.util.log import glog


def main() -> int:
    cwd_path: str = os.getcwd()

    filenames: set[str] = set()
    dirnames: set[str] = set()
    for dirpath, dirname, filename in os.walk(cwd_path):
        filenames = set(filename)
        dirnames = set(dirname)
        break

    amca_config_path: Path = (
        Path(__file__) / ".." / ".." / "configs" / "amca_config.json"
    ).resolve()

    default_plugin_path: Path = (Path(__file__) / ".." / ".." / "plugins").resolve()

    sc: Settings = Settings(
        str(amca_config_path),
        backend="json",
        auto_save=True,
    )
    sc.load()

    # default plugin path
    sc.default("plugin_config.plugin_paths", [str(default_plugin_path)])
    sc.default("amca_config.print_info", False)
    sc.default("amca_config.disable_logs", False)

    if bool(sc.get("amca_config.disable_logs")):
        glog.set_mode("silent")
    else:
        if bool(sc.get("amca_config.print_info")):
            glog.set_min_level("INFO")
        else:
            glog.set_min_level("WARN")

    active_plugins = plugin_checker.check_plugins(
        sc, filepath=default_plugin_path, filenames=filenames, dirnames=dirnames
    )

    plugin_loader.load_plugins(
        sc,
        filepath=Path(cwd_path),
        filenames=filenames,
        dirnames=dirnames,
        active_plugins=active_plugins,
    )

    return 0
