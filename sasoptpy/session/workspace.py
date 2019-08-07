
import sasoptpy

class Workspace:

    def __init__(self, name, session=None):
        self.name = name
        self._load_workspace_defaults()
        self._session = session

    def _load_workspace_defaults(self):
        self._elements = []

    def get_elements(self):
        return self._elements

    def __str__(self):
        return 'Workspace[ID={}]'.format(id(self))

    def __repr__(self):
        return 'sasoptpy.Workspace({})'.format(name)

    def __enter__(self):
        self.original = sasoptpy.container
        sasoptpy.container = self
        return self

    def __exit__(self, type, value, traceback):
        sasoptpy.container = self.original

    def append(self, element):
        self._elements.append(element)

    def add_variables(self, *args, **kwargs):
        vg = sasoptpy.VariableGroup(*args, **kwargs)
        self.append(vg)
        return vg

    def get_session(self):
        return self._session

    def submit(self, **kwargs):
        return sasoptpy.util.submit(self, **kwargs)
