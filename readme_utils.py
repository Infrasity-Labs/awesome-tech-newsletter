import re


def normalize_title(title: str) -> str:
    """Normalize a newsletter title for comparison: strip bold/italic
    markers, collapse whitespace, and lowercase."""
    return re.sub(r'\s+', ' ', re.sub(r'[*_]', '', title)).strip().lower()


def table_sort_key(row: str) -> str:
    """Extract sort key from the first column (Name) of a Markdown table row,
    case-insensitive, stripping bold/italic markers."""
    parts = re.split(r'(?<!\\)\|', row)
    if len(parts) > 1:
        return normalize_title(parts[1])
    return ''
