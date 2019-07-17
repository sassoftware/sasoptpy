
class Workspace:

    def __init__(self, name):
        self.name = name
        self._load_workspace_defaults()

    def _load_workspace_defaults(self):
        self.__namedict = dict()
        self.__counters = dict()
        self.__objcnt = 0

    def __str__(self):
        return 'Workspace[ID={}]'.format(id(self))

    def __repr__(self):
        return 'sasoptpy.Workspace({})'.format(name)

    def __enter__(self):
        print('Enter!')
        return self

    def __exit__(self, type, value, traceback):
        print('Exit')

