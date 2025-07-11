from re import compile as re_comp

# Exceptions
class JyparseUnexpectedToken(Exception):
    def __init__(self, char, line, token = ""):
        self.char = char
        self.line = line
        self.token = token

    def __str__(self):
        return f"Unexpected character at {self.line}-{self.char}: {self.token}"

class JyparseTrailingComma(Exception):
    def __init__(self, char, line):
        self.char = char
        self.line = line

    def __str__(self):
        return f"Trailing comma before {self.line}-{self.char}"

class JyparseNoSeperation(Exception):
    def __init__(self, char, line, token):
        self.char = char
        self.line = line
        self.token = token

    def __str__(self):
        return f"Expected comma before {self.token}: at {self.line}-{self.char}"

# Nodes
class ContaiderNode:
    def __init__(self, typ, parent):
        self.values = []
        self.type = typ
        self.parent = parent

    def __repr__(self):
        return f"{self.values}"

class Objectnode:
    def __init__(self, key, value):
        self.key = key
        self.value = value

def is_valid_json_number(string):
    res = re_comp(r"^-?\d+(\.\d+)?([eE][+\-]?\d+)?$").match(string)
    if res is None:
        return False
    return res.string == string

def is_valid_json_string(string):
    res = re_comp(r"^\"([^\"\\]?(\\[\"\\\/bfnrt])?(\\u[0-9a-fA-F]{4})?)*\"$").match(string)
    if res is None:
        return False
    return res.string == string

def is_valid_json_keyword(string):
    return string == "false" or string == "true" or string == "null"

def convert_keyword(string):
    match string:
        case "true":
            return True
        case "false":
            return False
        case "null":
            return None

def convert_number(string):
    try:
        return int(string)
    except ValueError:
        try:
            return float(string)
        except ValueError:
            return complex(string)

def parse(string):
    # Scanners
    string_re = re_comp(r"\"([^\"\\]?(\\[\"\\\/bfnrt])?(\\u[0-9a-fA-F]{4})?)*?\"")
    true_re = re_comp(r"true")
    false_re = re_comp(r"false")
    null_re = re_comp(r"null")
    number_re = re_comp(r"-?\d+(\.\d+)?([eE][+\-]?\d+)?")

    root = None
    curr = None
    curr_value = None
    seperated = False

    whitespace = ["\r", " ", "\t"]
    ln = 1
    ch = 0

    for line in string.split("\n"):
        while ch < len(line):
            # Whitespace
            if line[ch] in whitespace:
                ch += 1
                continue

            match line[ch]:
                # Object
                case "{":
                    curr = ContaiderNode("OBJ", curr)
                    if root is None:
                        root = curr
                case "}":
                    if curr is None or curr.type != "OBJ":
                        raise JyparseUnexpectedToken(ch + 1, ln, line[ch])
                    if (seperated and curr_value is None):
                        raise JyparseTrailingComma(ch + 1, ln)
                    curr = curr.parent
                # Array
                case "[":
                    curr = ContaiderNode("ARR", curr)
                    seperated = False
                    curr_value = None
                    if root is None:
                        root = curr
                case "]":
                    if curr is None or curr.type != "ARR":
                        raise JyparseUnexpectedToken(ch + 1, ln, line[ch])
                    if (seperated and curr_value is None):
                        raise JyparseTrailingComma(ch + 1, ln)
                    if curr.parent is not None:
                        curr.parent.values.append(curr)
                    curr = curr.parent
                # String
                case "\"":
                    if curr is None:
                        raise JyparseUnexpectedToken(ch + 1, ln, line[ch])
                    
                    string_match = string_re.match(line[ch:])
                    if string_match is None:
                        raise JyparseUnexpectedToken(ch + 1, ln, line[ch])
                    
                    # Append to Array
                    if curr.type == "ARR":
                        curr.values.append(line[ch + 1:ch + string_match.end() - 1])
                        if curr_value is not None:
                            raise JyparseNoSeperation(ch + 1, ln, line[ch])
                        curr_value = string_match

                    ch += string_match.end() - 1
                # Keywords
                case "t" | "f" | "n":
                    match = true_re.match(line[ch:]) or false_re.match(line[ch:]) or null_re.match(line[ch:])
                    if match is None:
                        raise JyparseUnexpectedToken(ch + 1, ln, line[ch])

                    # Append to Array
                    if curr.type == "ARR":
                        curr.values.append(convert_keyword(line[ch:ch + match.end()]))
                        if curr_value is not None:
                            raise JyparseNoSeperation(ch + 1, ln, line[ch])
                        curr_value = match
                    
                    ch += match.end() - 1
                # Number
                case "0" | "1" | "2" | "3" | "4" | "5" | "6" | "7" | "8" | "9":
                    match = number_re.match(line[ch:])
                    if match is None:
                        raise JyparseUnexpectedToken(ch + 1, ln, line[ch])

                    # Append to Array
                    if curr.type == "ARR":
                        curr.values.append(convert_number(line[ch:ch + match.end()]))
                        if curr_value is not None:
                            raise JyparseNoSeperation(ch + 1, ln, line[ch])
                        curr_value = match

                    ch += match.end() - 1
                # Seperator
                case ",":
                    seperated = True
                    if curr_value is None:
                        raise JyparseUnexpectedToken(ch + 1, ln, line[ch])
                    curr_value = None
                # Invalid
                case _:
                    raise JyparseUnexpectedToken(ch + 1, ln, line[ch])

            ch += 1

        ln += 1
    print(root.values)

parse("[\"name\", [132, false], [null,]]")
