"""Serialize a table (list of rows) into the text formats we compare: markdown, json, html, text."""
import html
import json


def _normalize(table):
    """Pad every row to the same width and make every cell a clean string."""
    width = max(len(row) for row in table)
    return [[str(cell).strip() for cell in row] + [""] * (width - len(row)) for row in table]


def _column_names(header):
    """Give empty or repeated header cells a unique name so they can be JSON keys."""
    names, seen = [], {}
    for i, name in enumerate(header):
        name = name or ("item" if i == 0 else f"column_{i}")
        seen[name] = seen.get(name, 0) + 1
        names.append(name if seen[name] == 1 else f"{name}_{seen[name]}")
    return names


def to_markdown(table):
    header, *rows = _normalize(table)
    clean = lambda cell: cell.replace("|", "/")
    lines = ["| " + " | ".join(clean(c) for c in header) + " |",
             "|" + "---|" * len(header)]
    lines += ["| " + " | ".join(clean(c) for c in row) + " |" for row in rows]
    return "\n".join(lines)


def to_json(table):
    header, *rows = _normalize(table)
    names = _column_names(header)
    records = [dict(zip(names, row)) for row in rows]
    return json.dumps(records, ensure_ascii=False)


def to_html(table):
    header, *rows = _normalize(table)
    out = ["<table>", "<tr>" + "".join(f"<th>{html.escape(c)}</th>" for c in header) + "</tr>"]
    out += ["<tr>" + "".join(f"<td>{html.escape(c)}</td>" for c in row) + "</tr>" for row in rows]
    out.append("</table>")
    return "\n".join(out)


def row_to_text(header, row):
    """One row as a sentence, e.g. 'sales: 2014 = $ 5720; 2013 = $ 6205.'"""
    names = _column_names(header)
    label = row[0] or "row"
    cells = [f"{names[j]} = {row[j]}" for j in range(1, len(row)) if row[j]]
    return f"{label}: " + "; ".join(cells) + "."


def to_text(table):
    header, *rows = _normalize(table)
    return "\n".join(row_to_text(header, row) for row in rows)


FORMATS = {"markdown": to_markdown, "json": to_json, "html": to_html, "text": to_text}


def serialize(table, fmt="markdown"):
    if not table:
        return "(no table)"
    return FORMATS[fmt](table)
