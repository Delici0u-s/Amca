from pathlib import Path
from impl.util.config.config import general_settings
import os


def create_amca_root(path: Path):
    (path / str(general_settings.get("amca_root.folder_name"))).resolve().mkdir(
        parents=True, exist_ok=True
    )


def load(args, plugin_args_map):
    create_amca_root((Path(os.getcwd())).resolve())
