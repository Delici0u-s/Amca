from pathlib import Path


class DirInfo:
    def __init__(self, path: Path, files: set[str], folders: set[str]) -> None:
        self.path = path
        self.files = files
        self.folders = folders


class DirParser:
    def __init__(self) -> None:
        self.parsed_dirs: dict[Path, DirInfo] = {}

    def parse_dir(self, path: Path) -> DirInfo:
        key = path.resolve(strict=False)

        if key in self.parsed_dirs:
            return self.parsed_dirs[key]

        files: set[str] = set()
        folders: set[str] = set()

        for entry in key.iterdir():
            if entry.is_file():
                files.add(entry.name)
            elif entry.is_dir():
                folders.add(entry.name)

        info = DirInfo(key, files, folders)
        self.parsed_dirs[key] = info
        return info


global_dir_parser = DirParser()
