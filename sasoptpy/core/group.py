
import sasoptpy
from abc import ABC, abstractmethod

class Group(ABC):

    def __init__(self, name):
        self._name = name

    def get_name(self):
        return self._name

    @abstractmethod
    def get_members(self):
        """
        Each Group object should provide a way to access its members as an
        OrderedDict
        """
