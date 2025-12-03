class Counter:
    def __init__(self):
        self.__value: int = -1

    def get(self) -> int:
        self.__value += 1
        return self.__value

    def get_total(self) -> int:
        return self.__value

    def set(self, value: int) -> None:
        self.__value = value


GCounter: Counter = Counter()
