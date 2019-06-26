# Abstract class for sessions

from abc import ABC, abstractmethod

class Mediator(ABC):

    @abstractmethod
    def solve(self):
        pass
