import os
import sys

# import modules from the root directory
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from readme_utils import TABLE_HEADER, TABLE_RULE, category_files, is_row, table_sort_key


def format_file(path):
    """Make sure a category file has the standard table header and sorted rows."""
    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    before, rows, after = [], [], []
    for line in lines:
        if is_row(line):
            rows.append(line if line.endswith("\n") else line + "\n")
        elif line.strip().startswith("| Name") or line.strip().startswith("|------"):
            continue                                  # header and rule are re-added below
        elif rows:
            after.append(line)
        else:
            before.append(line)

    rows.sort(key=table_sort_key)
    while before and not before[-1].strip():
        before.pop()
    out = before + ["\n", TABLE_HEADER, TABLE_RULE] + rows + after
    with open(path, "w", encoding="utf-8") as f:
        f.writelines(out)


def format_readme():
    files = category_files()
    for path in files:
        format_file(path)
    print(f"Successfully formatted and sorted {len(files)} category tables in directory/.")


if __name__ == "__main__":
    format_readme()
