from typing import Optional
import impl.util.config.config as cf
from pathlib import Path
from impl.util.globals import global_dir_parser as gdp
from impl.util.dirparse import DirInfo
import os, sys
from impl.amca_impl.new import create_amca_root
from impl.util.input import query_yes_no


def _find_amca_root_dir() -> Optional[DirInfo]:
    ori_seach_path = Path(os.getcwd()).resolve()
    seach_path = ori_seach_path

    root_folder_name = str(cf.general_settings.get("amca_root.folder_name"))
    if root_folder_name.count("/") + root_folder_name.count("\\") != 0:
        print(
            f"Ensure amca_root.folder_name in {Path(sys.argv[0]).parent} is a single folders name, not a path"
        )
        sys.exit(1)

    return_val = None
    for _ in range(cf.general_settings.get("amca_root.recursive_search_depth")):
        dir_info = gdp.parse_dir(seach_path)
        if root_folder_name in dir_info.folders:
            return_val = dir_info
            break
        if seach_path == seach_path.parent:
            break
        seach_path = seach_path.parent

    ignored_root_paths: list[str] = cf.general_settings.get("amca_root.ignored_paths")
    if str(ori_seach_path) not in ignored_root_paths:
        if query_yes_no(
            "No amca root was found, would you like to create one in this directory?"
        ):
            create_amca_root(ori_seach_path)
            return_val = gdp.parse_dir(ori_seach_path)
        else:
            ignored_root_paths.append(str(ori_seach_path))
            cf.general_settings.set("amca_root.ignored_paths", ignored_root_paths)

    return return_val


amca_root_dir_info = _find_amca_root_dir()
