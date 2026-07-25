from abc import ABC, abstractmethod


class ITransformerStep(ABC):

    @abstractmethod
    def transform(self, text: str, ext: str) -> str:
        pass