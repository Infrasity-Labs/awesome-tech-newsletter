"""Shared helpers for the newsletter directory.

Newsletter rows live in one Markdown file per category under ``directory/``.
README.md is generated from those files by build_readme.py.
"""
import glob
import os
import re

ROOT = os.path.dirname(os.path.abspath(__file__))
DIRECTORY = os.path.join(ROOT, "directory")
README_PATH = os.path.join(ROOT, "README.md")
LAST_RUN_PATH = os.path.join(ROOT, "last_run.json")

TABLE_HEADER = "| Name | Link | Description | Frequency |\n"
TABLE_RULE = "|------|------|-------------|-----------|\n"

# Display order and one-line definitions. A category that is not listed here
# (created automatically by aggregate.py) is appended after these.
CATEGORY_INFO = {
    "General Software Engineering": "Broad engineering newsletters: craft, careers, tools and industry news that cut across stacks.",
    "Backend Development": "Servers, APIs and databases, and the languages and frameworks behind them.",
    "System Design & Architecture": "Distributed systems, scalability and software architecture, from first principles to real-world case studies.",
    "Language Specific": "Newsletters tied to a single programming language or ecosystem, such as Python, Rust, Go, Java or Swift.",
    "DevOps & Cloud": "Infrastructure, CI/CD, containers, observability and the major cloud platforms.",
    "GTM": "Go-to-market for technical products: positioning, sales, growth and revenue.",
    "Developer Marketing": "Marketing to developers: content, community, developer relations and brand for technical audiences.",
    "Technical Content Marketing": "Writing, documentation and content strategy for technical products.",
    "Frontend Development": "Web and UI engineering: JavaScript, frameworks, CSS, design systems and browser platform news.",
    "Data Science & AI": "Machine learning, LLMs, data engineering and applied AI, from research digests to practitioner notes.",
}

def plural(n, word="newsletter"):
    """'1 newsletter', '2 newsletters'."""
    return f"{n:,} {word}" + ("" if n == 1 else "s")

def slugify(category):
    """File/anchor slug: 'Data Science & AI' -> 'data-science-ai'."""
    return re.sub(r"[^a-z0-9]+", "-", category.lower()).strip("-")

def category_path(category):
    return os.path.join(DIRECTORY, slugify(category) + ".md")

def category_files():
    return sorted(glob.glob(os.path.join(DIRECTORY, "*.md")))

def table_sort_key(row: str) -> str:
    """Extract sort key from the first column (Name) of a Markdown table row,
    case-insensitive, stripping bold/italic markers."""
    parts = re.split(r'(?<!\\)\|', row)
    if len(parts) > 1:
        return re.sub(r'[*_]', '', parts[1]).strip().lower()
    return ''

def is_row(line):
    """A newsletter row (not the header or the separator)."""
    s = line.strip()
    return s.startswith("|") and not s.startswith("| Name") and not s.startswith("|------")

def read_category(path):
    """Return (title, rows) for one category file. Rows keep their raw text."""
    title, rows = None, []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if title is None and line.startswith("# "):
                title = line[2:].strip()
            elif is_row(line):
                rows.append(line.rstrip("\n"))
    return title or os.path.splitext(os.path.basename(path))[0], rows

def read_all():
    """[(category, rows)] in display order."""
    found = {}
    for path in category_files():
        title, rows = read_category(path)
        found[title] = rows
    ordered = [c for c in CATEGORY_INFO if c in found]
    ordered += sorted(c for c in found if c not in CATEGORY_INFO)
    return [(c, found[c]) for c in ordered]

def row_fields(row):
    """(name, url, description, frequency) from a raw table row."""
    parts = [p.strip() for p in re.split(r'(?<!\\)\|', row)[1:-1]]
    parts += [""] * (4 - len(parts))
    m = re.search(r'\]\((https?://[^)\s]+)\)', parts[1])
    return re.sub(r'^\*\*|\*\*$', '', parts[0]), (m.group(1) if m else ""), parts[2], parts[3]

def write_category(path, category, rows, description=None, back="../README.md"):
    """Write a category file: title, definition, back link, count, sorted table."""
    rows = sorted(rows, key=table_sort_key)
    description = description or CATEGORY_INFO.get(category) or f"Newsletters in {category}."
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"# {category}\n\n{description}\n\n")
        f.write(f"[← Back to the directory]({back}) · **{plural(len(rows))}**\n\n")
        f.write(TABLE_HEADER + TABLE_RULE)
        for r in rows:
            f.write(r + "\n")
