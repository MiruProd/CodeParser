from abc import ABC, abstractmethod


class ITokenCounter(ABC):

    @abstractmethod
    def count_tokens(self, text: str) -> int:
        pass