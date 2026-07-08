import re

README_PATH = "README.md"

def format_readme():
    with open(README_PATH, "r", encoding="utf-8") as f:
        lines = f.readlines()

    new_lines = []
    in_category = False
    
    # 1. Enforce headers
    for line in lines:
        if line.startswith('## '):
            in_category = True
        if line.strip().startswith('|'):
            if in_category:
                if '| Name' not in line and '|------' not in line:
                    new_lines.append('| Name | Link | Description | Frequency |\n')
                    new_lines.append('|------|------|-------------|-----------|\n')
                in_category = False
        new_lines.append(line)
        
    # 2. Sort tables
    final_lines = []
    in_table = False
    table_rows = []
    header_rows = []
    
    for line in new_lines:
        if line.strip().startswith('|'):
            if not in_table:
                in_table = True
                table_rows = []
                header_rows = [line]
            elif len(header_rows) < 2:
                header_rows.append(line)
            else:
                table_rows.append(line)
        else:
            if in_table:
                # Sort and flush table
                table_rows.sort(key=lambda x: re.sub(r'[*_]', '', re.split(r'(?<!\\)\|', x)[1]).strip().lower() if len(re.split(r'(?<!\\)\|', x)) > 1 else '')
                final_lines.extend(header_rows)
                final_lines.extend(table_rows)
                in_table = False
            final_lines.append(line)
            
    if in_table:
        table_rows.sort(key=lambda x: re.sub(r'[*_]', '', re.split(r'(?<!\\)\|', x)[1]).strip().lower() if len(re.split(r'(?<!\\)\|', x)) > 1 else '')
        final_lines.extend(header_rows)
        final_lines.extend(table_rows)

    with open(README_PATH, "w", encoding="utf-8") as f:
        f.writelines(final_lines)
    
    print("Successfully formatted and sorted README tables.")

if __name__ == "__main__":
    format_readme()
