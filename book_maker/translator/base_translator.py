import itertools
from abc import ABC, abstractmethod


class Base(ABC):
    def __init__(self, key, language) -> None:
        self.keys = itertools.cycle([k.strip() for k in key.split(",") if k.strip()])
        self.language = language

    @abstractmethod
    def rotate_key(self):
        pass

    @abstractmethod
    def translate(self, text):
        pass

    def set_deployment_id(self, deployment_id):
        pass
