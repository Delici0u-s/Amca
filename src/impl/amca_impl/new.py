from pathlib import Path
from impl.util.config.config import general_settings


def create_amca_root(path: Path):
    (path / str(general_settings.get("amca_root_folder_name"))).mkdir(
        parents=True, exist_ok=True
    )


def load(args, plugin_args_map): ...
