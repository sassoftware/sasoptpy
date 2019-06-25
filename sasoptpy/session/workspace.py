
class Workspace:

    def __init__(self):
        self.value = 0

    def __str__(self):
        return 'Workspace[ID={}]'.format(id(self))

    def __repr__(self):
        return 'sasoptpy.Workspace()'

    def __enter__(self):
        print('Enter!')
        return self

    def __exit__(self, type, value, traceback):
        print('Exit')


if __name__ == '__main__':
    w = Workspace()
    print(id(w))
    print(str(w))
    print(repr(w))

    with Workspace() as x:
        print(x)
        print(id(x))
