from .statement_base import Statement
import sasoptpy


class FixStatement(Statement):

    def __init__(self, *elements):
        super().__init__()
        self.keyword = 'fix'
        for i in elements:
            self.append(i)

    def append(self, element):
        self.elements.append(element)

    def _defn(self):
        elems = []
        for i in self.elements:
            elems.append('{}={}'.format(
                sasoptpy.to_expression(i[0]),
                sasoptpy.to_expression(i[1])
            ))
        s = self.keyword + ' ' + ' '.join(elems) + ';'
        return s

    @classmethod
    def fix(cls, *items):
        if len(items) == 2 and not any(isinstance(i, tuple) for i in items):
            items = ((items[0], items[1]),)
        fs = FixStatement(*items)
        return fs


class UnfixStatement(Statement):

    def __init__(self, *elements):
        super().__init__()
        self.keyword = 'unfix'
        for i in elements:
            self.append(i)

    def append(self, element):
        self.elements.append(element)

    def _defn(self):
        elems = []
        for i in self.elements:
            if isinstance(i, tuple):
                elems.append('{}={}'.format(
                    sasoptpy.to_expression(i[0]),
                    sasoptpy.to_expression(i[1])
                ))
            else:
                elems.append(sasoptpy.to_expression(i))
        s = self.keyword + ' ' + ' '.join(elems) + ';'
        return s

    @classmethod
    def unfix(cls, *items):
        fs = UnfixStatement(*items)
        return fs
