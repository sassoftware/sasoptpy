# Abstract class for sessions

from abc import ABC, abstractmethod

class Mediator(ABC):

    @abstractmethod
    def solve(self, **kwargs):
        pass

    @abstractmethod
    def submit(self, **kwargs):
        pass
