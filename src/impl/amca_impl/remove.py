from pathlib import Path
from impl.util.config.config import general_settings
from impl.util.globals import amca_root_dir_info
from impl.util.input import query_yes_no
import shutil as sh


def load(args, plugin_args_map):
    if amca_root_dir_info is not None:
        root_folder_name = str(general_settings.get("amca_root.folder_name"))
        if query_yes_no(
            f"Would you like to delete: {amca_root_dir_info.path / root_folder_name}?"
        ):
            sh.rmtree(amca_root_dir_info.path / root_folder_name)
