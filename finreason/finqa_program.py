"""Execute FinQA's gold reasoning programs, e.g. 'subtract(5829, 5735), divide(#0, 5735)'."""
import re

from .answers import find_numbers

STEP_RE = re.compile(r"(\w+)\(([^)]*)\)")


def parse_program(program):
    """Split a program into steps: [('subtract', ['5829', '5735']), ('divide', ['#0', '5735'])]."""
    return [(op, [a.strip() for a in args.split(",")]) for op, args in STEP_RE.findall(program)]


def to_number(arg, results):
    """Resolve one argument: '#0' -> result of step 0, 'const_100' -> 100, 'const_m1' -> -1,
    '8.75%' -> 0.0875, '1,234' -> 1234."""
    if arg.startswith("#"):
        return results[int(arg[1:])]
    if arg.startswith("const_"):
        return -1.0 if arg == "const_m1" else float(arg[len("const_"):])
    if arg.endswith("%"):
        return float(arg[:-1].replace(",", "")) / 100
    return float(arg.replace(",", ""))


def _table_row(table, name):
    """Numeric cells of the table row whose label equals name."""
    for row in table:
        if row and row[0].strip() == name.strip():
            values = []
            for cell in row[1:]:
                numbers = find_numbers(cell)
                if numbers:   # FinQA treats '4.7%' in a table cell as 0.047
                    first = numbers[0]
                    values.append(first["value"] / 100 if first["percent"] else first["value"])
            return values
    raise ValueError(f"row '{name}' not found in table")


def execute(program, table=None):
    """Run the program step by step and return the last result (a float, or 'yes'/'no')."""
    results = []
    for op, args in parse_program(program):
        if op.startswith("table_"):
            values = _table_row(table, args[0])
            result = {"table_sum": sum, "table_max": max, "table_min": min,
                      "table_average": lambda v: sum(v) / len(v)}[op](values)
        else:
            a, b = to_number(args[0], results), to_number(args[1], results)
            if op == "add":
                result = a + b
            elif op == "subtract":
                result = a - b
            elif op == "multiply":
                result = a * b
            elif op == "divide":
                result = a / b
            elif op == "exp":
                result = a ** b
            elif op == "greater":
                result = "yes" if a > b else "no"
            else:
                raise ValueError(f"unknown operation {op}")
        results.append(result)
    return results[-1]


def numeric_arguments(program):
    """Literal numbers used in the program (the operands the model has to find in the report)."""
    literals = []
    for _, args in parse_program(program):
        for arg in args:
            if not arg.startswith(("#", "const_")) and re.fullmatch(r"-?[\d,]*\.?\d+%?", arg):
                literals.append(arg)
    return literals
