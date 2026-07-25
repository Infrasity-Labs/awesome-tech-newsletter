import re


def table_sort_key(row: str) -> str:
    """Extract sort key from the first column (Name) of a Markdown table row,
    case-insensitive, stripping bold/italic markers."""
    parts = re.split(r'(?<!\\)\|', row)
    if len(parts) > 1:
        return re.sub(r'[*_]', '', parts[1]).strip().lower()
    return ''
