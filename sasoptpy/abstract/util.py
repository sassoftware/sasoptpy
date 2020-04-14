import sasoptpy


def is_abstract(arg):
    return any(isinstance(arg, i) for i in sasoptpy.abstract_classes)


def is_abstract_set(arg):
    return isinstance(arg, sasoptpy.abstract.Set)


def is_key_abstract(arg):
    return isinstance(arg, sasoptpy.abstract.SetIterator) or\
           isinstance(arg, sasoptpy.abstract.SetIteratorGroup)


def is_conditional_value(arg):
    return isinstance(arg, sasoptpy.abstract.Conditional)


def is_solve_statement(i):
    if type(i) == sasoptpy.abstract.SolveStatement:
        return True
    elif isinstance(i, sasoptpy.abstract.Statement):
        if 'solve' in sasoptpy.to_definition(i)[:5]:
            return True
    return False


def is_print_statement(i):
    if type(i) == sasoptpy.abstract.PrintStatement:
        return True
    elif isinstance(i, sasoptpy.abstract.Statement):
        if 'print' in sasoptpy.to_definition(i)[:5]:
            return True
    return False


def is_create_data_statement(i):
    if type(i) == sasoptpy.abstract.CreateDataStatement:
        return True
    return False


def get_key_from_name(name):
    name = name.replace('\'', '').replace('"', '')
    keys = name.split('[')[1].split(']')[0]
    keys = keys.split(',')
    keys = tuple(int(k) if k.isdigit() else k
                 for k in keys)
    return keys
