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
