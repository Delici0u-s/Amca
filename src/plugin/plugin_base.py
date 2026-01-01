import abc
from dirparse import DirInfo, DirParser
from typing import override


class Plugin(abc.ABC):
    @abc.abstractmethod
    def __init__(self, plugin_root_dir: DirInfo, dir_parser: DirParser):
        pass

    @abc.abstractmethod
    def should_load(
        self,
        amca_root_dir: DirInfo,
        working_dir: DirInfo,
        dir_parser: DirParser,
    ) -> bool:
        pass

    @abc.abstractmethod
    def load(
        self,
        amca_root_dir: DirInfo,
        working_dir: DirInfo,
        dir_parser: DirParser,
        args: list[str],
    ) -> None:
        pass
