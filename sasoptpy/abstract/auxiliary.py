
import sasoptpy

class Auxiliary(sasoptpy.Expression):

    def __init__(self, base, prefix=None, suffix=None, operator=None, value=None):
        super().__init__()
        self._base = base
        self._prefix = prefix
        self._suffix = suffix
        self._operator = None
        self._value = value

    def get_prefix_str(self):
        if self._prefix is None:
            return ''
        return self._prefix

    def get_base_str(self):
        if self._base is None:
            return ''
        return sasoptpy.to_expression(self._base)

    def get_suffix_str(self):
        if self._suffix is None:
            return ''
        return self._suffix

    def wrap_operator_str(self, s):
        if self._operator is None:
            return s
        return '{}({})'.format(
            sasoptpy.to_expression(self._operator), s
        )

    def _expr(self):
        prefix_str = self.get_prefix_str()
        base_str = self.get_base_str()
        suffix_str = self.get_suffix_str()
        s = prefix_str + base_str
        if suffix_str != '':
            s += '.' + suffix_str
        s = self.wrap_operator_str(s)
        return s
