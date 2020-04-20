
import re
import sasoptpy

def parse_optmodel_table(table):
    parsed_df = table[['Label1', 'cValue1']]
    parsed_df.columns = ['Label', 'Value']
    parsed_df = parsed_df.set_index(['Label'])
    return parsed_df

def wrap_long_lines(code, max_length=30000):
    long_line_regex = r".{" + str(max_length) + r",}\n?"
    partition_regex = r"(?=.{" + str(max_length) + r",}\n?)(.{" + \
                      str(round(max_length / 3)) + r",}?)([\,\ ]+)(.+)"
    subst = "\\1\\2\\n\\3"

    hits = re.findall(long_line_regex, code)
    line_lengths = [len(i) for i in hits]
    while len(hits) > 0:
        code = re.sub(partition_regex, subst, code)
        hits = re.findall(long_line_regex, code)
        new_line_lengths = [len(i) for i in hits]
        if line_lengths == new_line_lengths:
            break
        else:
            line_lengths = new_line_lengths
    return code

def replace_long_names(code):
    conversion = dict()
    matches = re.findall(r'[a-zA-Z\_\d]{32,}', code)
    if len(matches) > 0:
        print('NOTE: Some object names are longer than 32 characters, '
              'they will be replaced when submitting')
        unique_matches = list(set(matches))
        for i in unique_matches:
            new_name = sasoptpy.util.get_next_name()
            conversion[new_name] = i
            code = re.sub(
                r'\b' + i + r'\b', new_name, code)

    return code, conversion
