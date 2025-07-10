from re import compile as re_comp

def is_valid_json_number(s):
    res = re_comp(r"^-?\d+(\.\d+)?([eE][+\-]?\d+)?$").match(s)
    if res is None:
        return False
    return res.string == s

def is_valid_json_string(s):
    res = re_comp(r"^\"([^\"\\]?(\\[\"\\\/bfnrt])?(\\u[0-9a-fA-F]{4})?)*\"$").match(s)
    if res is None:
        return False
    return res.string == s
