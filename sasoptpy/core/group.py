
from abc import ABC, abstractmethod

class Group(ABC):

    @abstractmethod
    def get_members(self):
        """
        Each Group object should provide a way to access its members as an
        OrderedDict
        """
