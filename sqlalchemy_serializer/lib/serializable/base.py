from abc import abstractmethod


class Base:
    @abstractmethod
    def __call__(self, value) -> str: ...
