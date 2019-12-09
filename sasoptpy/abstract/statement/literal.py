from .statement_base import Statement

import sasoptpy
from sasoptpy.util.package_utils import _to_sas_string, _to_python_string


class LiteralStatement(Statement):

    @sasoptpy.class_containable
    def __init__(self, literal=None, **kwargs):
        super().__init__()
        self.append(literal)

    def append(self, literal):
        self.elements.append(literal)

    def _expr(self):
        expr = '\n'.join(self.elements)
        return expr

    def _defn(self):
        defn = '\n'.join(self.elements)
        return defn

    @classmethod
    def expand(cls):
        es = LiteralStatement('expand;', internal=True)
        return es

    @classmethod
    def union(cls, *args):
        ss = [_to_sas_string(i) for i in args]
        ls = LiteralStatement(' union '.join(ss), internal=True)
        ls.set_internal(True)
        return ls

    @classmethod
    def diff(cls, *args):
        ss = [_to_sas_string(i) for i in args]
        ls = LiteralStatement(' diff '.join(ss), internal=True)
        ls.set_internal(True)
        return ls

    @classmethod
    def substring(cls, main_string, first_pos, last_pos):
        ss = sasoptpy.Auxiliary(base='{}, {}, {}'.format(
            _to_python_string(main_string), first_pos, last_pos
        ), operator='substr')
        return ss

    @classmethod
    def unfix(cls, item):
        us = LiteralStatement('unfix {};'.format(
            _to_python_string(item)
        ))
