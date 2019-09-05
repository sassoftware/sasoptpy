import re

def get_generic_form(string):
    """
    Replaces temporary object names (in the form of o1, o2, ...) for
    comparison purposes
    """
    matches = re.findall(r'o[\d]+', string, re.MULTILINE)
    unique_matches = sorted(set(matches), key=lambda x: int(x[1:]))
    temp_ctr = 0
    for i in unique_matches:
        temp_ctr += 1
        string = string.replace(i, 'TEMP{}'.format(temp_ctr))
    return string


def assert_equal_wo_temps(tester, left, right):
    left_wo_temp = get_generic_form(left)
    right_wo_temp = get_generic_form(right)
    return tester.assertEqual(left_wo_temp, right_wo_temp)
