from re import compile as re_comp

def is_valid_json_number(s):
    res = re_comp(r"^-?\d+(\.\d+)?([eE][+\-]?\d+)?$").match(s)
    if res is None:
        return False
    return res.string == s
