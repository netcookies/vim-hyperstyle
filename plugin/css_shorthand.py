import re
from definitions import properties, expressions, full_properties

line_expr = re.compile(r'^(\s*)(.*?)$')
value_expr = re.compile(r'^([^\.\d-]*)(-?\d*\.?\d+)(p|x|m|px|em|s|ms|%|)$')
rule_expr = re.compile(r'^((?:[a-z]+-)*[a-z]+): *([^\s].*);?$')

"""
Expands a snippet expression. If `semi` is a blank string, then treat the
language as an indented syntax (like Sass).

>>> expand_expression("db")
"display: block;"

>>> expand_expression("db", '')
"display: block"

>>> expand_expression("m3m")
"margin: 3em;"
"""
def expand_expression(line, semi = ';'):
    indent, snippet = split_indent(line)

    # Check if its a simple expression
    # (db => display: block)
    def expand_simple_expression():
        expansion = expressions.get(snippet)
        if not expansion: return

        key, value, _ = expansion
        return "%s%s: %s%s" % (indent, key, value, semi)

    # Check if its a property with value
    # (m10em => margin: 10em)
    def expand_property_with_value():
        short, value, unit = split_value(snippet) # "m", "10", "em"
        expansion = properties.get(short) # ("margin", {"unit": "px"})
        if not expansion: return

        prop, options = expansion
        default_unit = options.get('unit')
        if not default_unit: return

        value = expand_value(value, unit, default_unit)
        return "%s%s: %s%s" % (indent, prop, value, semi)

    # (margin: 3 => margin: 3px)
    def expand_unit_value():
        m = rule_expr.match(snippet)
        if not m: return

        prop = m.group(1)
        options = full_properties.get(m.group(1))
        if not options: return

        short, value, unit = split_value(m.group(2))
        if not value: return

        default_unit = options.get('unit')
        if not default_unit: return

        value = expand_value(value, unit, default_unit)
        return "%s%s: %s%s" % (indent, prop, value, semi)

    # add semicolon if needed
    def expand_semicolon():
        if semi == ';' and is_balanced_rule(snippet):
            return "%s%s;" % (indent, snippet)

    return \
        expand_simple_expression() or \
        expand_property_with_value() or \
        expand_unit_value() or \
        expand_semicolon()

"""
Splits a snippet into property, value and unit

# margin: 10px
>>> split_value("m10p")
("m", "10", "p")
"""
def split_value(snippet):
    m = value_expr.match(snippet)
    if m:
        return (m.group(1), m.group(2), m.group(3))
    else:
        return (None, None, None)

"""
Expands a property.

The 2nd argument is there to keep the API same with expand_expression(). Vim
might pass a semicolon for it.

>>> expand_property("m")
"margin:"
"""
def expand_property(line, semi=';'):
    indent, snippet = split_indent(line)

    tuple = properties.get(snippet)
    if tuple:
        prop, options = tuple
        return "%s%s:" % (indent, prop)

    # expr = expand_expression(line, semi)
    # if expr:
    #     return expr

"""
Expands a value

>>> expand_value("10", "")
"10px"

>>> expand_value("10", "m")
"10em"
"""
def expand_value(value, unit, default_unit = None):
    if value == "0":
        return value

    if unit == "p" or unit == "x":
        unit = "px"
    if unit == "m":
        unit = "em"
    if unit == "":
        if default_unit == "_":
            unit = ""
        else:
            unit = (default_unit or px)

    return value + unit

"""
(Private) splits a line into its indentation and meat.

>>> (indent, snippet) = split_indent("  db")
("  ", "db")
"""
def split_indent(line):
    match = line_expr.match(line)
    return (match.group(1), match.group(2))

"""
Checks if a line is a balanced rule that can be auto-terminated with a
semicolon.

>>> is_balanced_rule("margin: 0")
True
>>> is_balanced_rule("margin: scaleX(3)")
True
>>> is_balanced_rule("margin: linear-gradient(to-bottom")
True
"""
def is_balanced_rule(str):
    if str and str[-1] == ';':
        return False

    m = rule_expr.match(str)
    if not m:
        return False

    value = m.group(2)
    return value.count('(') == value.count(')')
