from abc import ABC, abstractmethod
from pathlib import Path
from typing import override


class Plugin(ABC):
    def __init__(self):
        pass

    @abstractmethod
    def matches(
        self,
        filepath: Path,
        filenames: set[str],
        dirnames: set[str],
    ) -> bool:
        pass

    @abstractmethod
    def load(
        self,
        filepath: Path,
        filenames: set[str],
        dirnames: set[str],
    ) -> None:
        pass
