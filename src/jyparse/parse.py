from re import compile as re_comp

# Exceptions
class JyparseUnexpectedToken(Exception):
    def __init__(self, char, string, token = ""):
        self.char = char
        self.string = string
        self.token = token 

    def __str__(self):
        return f"Unexpected character at {self.string}-{self.char}: {self.token}"

class JyparseTrailingComma(Exception):
    def __init__(self, char, string):
        self.char = char
        self.string = string

    def __str__(self):
        return f"Trailing comma before {self.string}-{self.char}"

class JyparseNoSeperation(Exception):
    def __init__(self, char, string, token):
        self.char = char
        self.string = string
        self.token = token

    def __str__(self):
        return f"Expected comma before {self.token}: at {self.string}-{self.char}"

class JyparseContainerLeftOpen(Exception):
    def __init__(self, char, string, typ):
        self.type = typ
        self.char = char
        self.string = string

    def __str__(self):
        typ = "Object" if self.type == "OBJ" else "Array"
        return f"{typ} left open at {self.string}-{self.char}"

# Nodes
class ContainerNode:
    def __init__(self, typ, parent):
        self.values = []
        self.type = typ
        self.parent = parent
        self.closed = False

    def __repr__(self):
        return f"{self.values}"

class Objectnode:
    value = None
    has_value = False
    
    def __init__(self, key):
        self.key = key

    def __repr__(self):
        return f"<{self.key}: {self.value} : {type(self.value)}>"

def is_valid_json_number(string:str):
    res = re_comp(r"^-?\d+(\.\d+)?([eE][+\-]?\d+)?$").match(string)
    if res is None:
        return False
    return res.string == string

def is_valid_json_string(string:str):
    res = re_comp(r"^\"([^\"\\]?(\\[\"\\\/bfnrt])?(\\u[0-9a-fA-F]{4})?)*\"$").match(string)
    if res is None:
        return False
    return res.string == string

def is_valid_json_keyword(string:str):
    return string == "false" or string == "true" or string == "null"

def convert_keyword(string:str):
    match string:
        case "true":
            return True
        case "false":
            return False
        case "null":
            return None

def convert_number(string:str):
    try:
        return int(string)
    except ValueError:
        try:
            return float(string)
        except ValueError:
            return complex(string)

def parse_container_node(node:ContainerNode):
    res = None
    
    if node.type == "ARR":
        res = []
        for el in node.values:
            if isinstance(el, ContainerNode):
                res.append(parse_container_node(el))
            else:
                res.append(el)
    else:
        res = {}
        for el in node.values:
            if not isinstance(el, Objectnode):
                return None
            if isinstance(el, ContainerNode):
                res[el.key] = parse_container_node(el.value)
            else:
                res[el.key] = el.value

    return res

def parse(string:str):
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
    is_value_ready = False

    whitespace = ["\r", " ", "\t", "\n"]
    ln = 1
    ch = 0
    lsch = 0

    while ch < len(string):
        # Whitespace
        if string[ch] in whitespace:
            if string[ch] == "\n":
                ln += 1
                lsch = ch + 1
            ch += 1
            continue

        match string[ch]:
            # Object
            case "{":
                curr = ContainerNode("OBJ", curr)
                if root is None:
                    root = curr
                if curr.parent and curr.parent.type == "OBJ":
                    if curr_value is None:
                        raise JyparseUnexpectedToken(ch - lsch + 1, ln, string[ch])
                    else:
                        if not is_value_ready or curr_value.has_value:
                            raise JyparseUnexpectedToken(ch - lsch + 1, ln, string[ch])
                        curr_value.value = curr
                        curr_value.has_value = True
                        is_value_ready = False
                        curr.parent.values.append(curr_value)
                        curr_value = None
                else:
                    curr_value = None
                seperated = False
            case "}": 
                if curr is None or curr.type != "OBJ":
                    raise JyparseUnexpectedToken(ch - lsch + 1, ln, string[ch])
                if (seperated and curr_value is None):
                    raise JyparseTrailingComma(ch - lsch + 1, ln)
                if curr.type == "OBJ" and curr_value and not curr_value.has_value:
                    raise JyparseUnexpectedToken(ch - lsch + 1, ln, string[ch])
                if curr.parent is not None:
                    # Object as array element
                    if curr.parent.type == "ARR":
                        curr.parent.values.append(curr)
                        curr_value = curr
                    else:
                        curr_value = curr.parent.values[-1]
                curr.closed = True
                curr = curr.parent
            # Array
            case "[":
                curr = ContainerNode("ARR", curr)
                if root is None:
                    root = curr
                if curr.parent and curr.parent.type == "OBJ":
                    if curr_value is None:
                        raise JyparseUnexpectedToken(ch - lsch + 1, ln, string[ch])
                    else:
                        if not is_value_ready or curr_value.has_value:
                            raise JyparseUnexpectedToken(ch - lsch + 1, ln, string[ch])
                        curr_value.value = curr
                        curr_value.has_value = True
                        is_value_ready = False
                        curr.parent.values.append(curr_value)
                    curr_value = None
                seperated = False
            case "]":
                if curr is None or curr.type != "ARR":
                    raise JyparseUnexpectedToken(ch - lsch + 1, ln, string[ch])
                if (seperated and curr_value is None):
                    raise JyparseTrailingComma(ch - lsch + 1, ln)
                if curr.parent is not None:
                    # Multi dimentional arrays
                    if curr.parent.type == "ARR":
                        curr.parent.values.append(curr)
                        curr_value = curr
                    else:
                        curr_value = curr.parent.values[-1]
                curr.closed = True
                curr = curr.parent
            # String
            case "\"":
                if curr is None:
                    raise JyparseUnexpectedToken(ch - lsch + 1, ln, string[ch])
                
                string_match = string_re.match(string[ch:])
                if string_match is None:
                    raise JyparseUnexpectedToken(ch - lsch + 1, ln, string[ch])
                
                # Append to Array
                if curr.type == "ARR":
                    curr.values.append(string[ch + 1:ch + string_match.end() - 1])
                    if curr_value is not None:
                        raise JyparseNoSeperation(ch - lsch + 1, ln, string[ch])
                    curr_value = string[ch + 1:ch + string_match.end() - 1]

                # Append to Object
                if curr.type == "OBJ":
                    if curr_value is None:
                        curr_value = Objectnode(string[ch + 1:ch + string_match.end() - 1])
                        curr.values.append(curr_value)
                    else:
                        if not is_value_ready or curr_value.has_value: 
                            raise JyparseUnexpectedToken(ch - lsch + 1, ln, string[ch])
                        curr_value.value = string[ch + 1:ch + string_match.end() - 1]
                        curr_value.has_value = True
                        is_value_ready = False

                ch += string_match.end() - 1
            # Keywords
            case "t" | "f" | "n":
                if curr is None:
                    raise JyparseUnexpectedToken(ch - lsch + 1, ln, string[ch])
                match = true_re.match(string[ch:]) or false_re.match(string[ch:]) or null_re.match(string[ch:])
                if match is None:
                    raise JyparseUnexpectedToken(ch - lsch + 1, ln, string[ch])

                # Append to Array
                if curr.type == "ARR":
                    curr.values.append(convert_keyword(string[ch:ch + match.end()]))
                    if curr_value is not None:
                        raise JyparseNoSeperation(ch - lsch + 1, ln, string[ch])
                    curr_value = match

                # Append to Object
                if curr.type == "OBJ":
                    if curr_value is None:
                        raise JyparseUnexpectedToken(ch - lsch + 1, ln, string[ch])
                    else:
                        if not is_value_ready or curr_value.has_value:
                            raise JyparseUnexpectedToken(ch - lsch + 1, ln, string[ch])
                        curr_value.value = convert_keyword(string[ch:ch + match.end()])
                        curr_value.has_value = True
                        is_value_ready = False

                ch += match.end() - 1
            # Number
            case "0" | "1" | "2" | "3" | "4" | "5" | "6" | "7" | "8" | "9":
                if curr is None:
                    raise JyparseUnexpectedToken(ch - lsch + 1, ln, string[ch])
                match = number_re.match(string[ch:])
                if match is None:
                    raise JyparseUnexpectedToken(ch - lsch + 1, ln, string[ch])

                # Append to Array
                if curr.type == "ARR":
                    curr.values.append(convert_number(string[ch:ch + match.end()]))
                    if curr_value is not None:
                        raise JyparseNoSeperation(ch - lsch + 1, ln, string[ch])
                    curr_value = match
                
                # Append to Object
                if curr.type == "OBJ":
                    if curr_value is None:
                        raise JyparseUnexpectedToken(ch - lsch + 1, ln, string[ch])
                    else:
                        if not is_value_ready or curr_value.has_value:
                            raise JyparseUnexpectedToken(ch - lsch + 1, ln, string[ch])
                        curr_value.value = convert_number(string[ch:ch + match.end()])
                        curr_value.has_value = True
                        is_value_ready = False

                ch += match.end() - 1
            # Seperator
            case ",":
                if curr.type == "OBJ" and not curr_value.has_value:
                    raise JyparseUnexpectedToken(ch - lsch + 1, ln, string[ch])
                seperated = True
                if curr_value is None:
                    raise JyparseUnexpectedToken(ch - lsch + 1, ln, string[ch])
                curr_value = None
            # Value assigner
            case ":":
                if curr is None or curr.type != "OBJ" or curr_value is None or is_value_ready:
                    raise JyparseUnexpectedToken(ch - lsch + 1, ln, string[ch])
                is_value_ready = True
            # Invalid
            case _:
                print(string[:ch - lsch + 1])
                raise JyparseUnexpectedToken(ch - lsch + 1, ln, string[ch])

        ch += 1

    if not root.closed:
        raise JyparseContainerLeftOpen(1, 1, root.type)
    
    res = {
        "type": "list" if root.type == "ARR" else "dict",
        "data": parse_container_node(root)
    }

    return res
