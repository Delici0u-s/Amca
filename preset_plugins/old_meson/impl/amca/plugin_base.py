import abc
from plugin.dirparse import DirInfo, DirParser
from typing import Optional, override


class Plugin(abc.ABC):
    def __init__(self, plugin_root_dir: DirInfo, dir_parser: DirParser):
        pass

    @abc.abstractmethod
    def should_load(
        self,
        amca_root_dir: Optional[DirInfo],
        working_dir: DirInfo,
        dir_parser: DirParser,
    ) -> bool: ...

    @abc.abstractmethod
    def load(
        self,
        amca_root_dir: Optional[DirInfo],
        working_dir: DirInfo,
        dir_parser: DirParser,
        args: list[str],
    ) -> None: ...
