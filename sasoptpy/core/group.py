
from abc import ABC, abstractmethod

class Group(ABC):

    @abstractmethod
    def get_members(self):
        pass
