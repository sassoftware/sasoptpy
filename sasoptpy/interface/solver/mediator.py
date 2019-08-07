# Abstract class for sessions

from abc import ABC, abstractmethod

class Mediator(ABC):

    @abstractmethod
    def solve(self):
        pass

    @abstractmethod
    def submit(self):
        pass
