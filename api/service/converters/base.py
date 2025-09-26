from abc import ABC, abstractmethod

class BaseConverter(ABC):
    @abstractmethod
    def convert(self, input_path: str, output_path: str, **kwargs):
        pass

    @abstractmethod
    def input_format(self) -> str:
        pass

    @abstractmethod
    def output_format(self) -> str:
        pass
