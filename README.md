# Jyparse

A JSON parser for python

## jyparse.parse

### is_valid_json_number(num_string)

checks if a number string is valid JSON number

```python
is_valid_json_number("-123.456E+789")
> True
```

### is_valid_json_string(string)

checks if a string is valid JSON string

```python
is_valid_json_number('"Hello there\\\n"')
> True
```

### is_valid_json_keyword(string)

checks if a string is valid JSON keyword

```python
is_valid_json_number("null")
> True
```

### parse(string)

parse JSON string to python data

```python
parse("[1, 2, 3]")
> {'type': 'list', 'data': [1, 2, 3]}
```

### parse_container_node(node)

parse container node (special Jyparse classes to standard data type)

```python
parse_container_node(ContainerNode("ARR", None))
> []
```
