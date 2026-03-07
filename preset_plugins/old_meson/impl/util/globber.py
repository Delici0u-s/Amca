import os
import sys
from pathlib import Path


def parse_directory(directory: str, filetype: str) -> list:
    filelist: list = list()

    for file in Path(directory).rglob(filetype):
        file_directory: str = file.__str__()
        if "subprojects" in file_directory:
            continue
        if "build" in file_directory:
            continue
        filelist.append(file)

    return filelist


def glob(args: list) -> None:
    directory: str = args[1]
    filetypes: list = [i for i in args[2:] if i != ""]
    files: list = list()

    for filetype in filetypes:
        files.extend(parse_directory(directory, filetype))

    for file in files:
        print(file)


def main():
    args: int = len(sys.argv)
    if args < 3:
        print("not enough arguments supplied!")
        print(f"usage: python {os.path.basename(__file__)} path_to_glob file_types")
        return 1

    glob(sys.argv)

    return 0


if __name__ == "__main__":
    main()
