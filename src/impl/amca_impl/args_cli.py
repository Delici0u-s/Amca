import subprocess
from impl.util.globals import global_dir_parser as gdp, amca_root_dir_info
from impl.util.config.config import general_settings, plugin_settings
from pathlib import Path
from InquirerPy import inquirer


def load(args, plugin_args_map):
    if amca_root_dir_info is not None:
        amca_root_folder = amca_root_dir_info.path / general_settings.get(
            "amca_root.folder_name"
        )
        amca_root_folder_info = gdp.parse_dir(amca_root_folder)

        plugin_path = Path(plugin_settings.get("generic.plugin_path"))
        path_info = gdp.parse_dir(plugin_path)
        available_plugins = [str(p) for p in path_info.folders]

        choice = inquirer.select(
            message="Pick a plugin to edit args:",
            choices=[*available_plugins, "None (exit)"],
        ).execute()

        if choice == "None (exit)":
            return

        arg_fol = amca_root_folder_info.path / "args"
        arg_fol.mkdir(parents=True, exist_ok=True)

        plugin_args_file = arg_fol / f"{choice}.args"
        editor = general_settings.get("default_file_editor")

        subprocess.call([editor, plugin_args_file])
    else:
        print(
            "No amca root was detected, ensure one exists, refer to --help (create one with amca n)"
        )
