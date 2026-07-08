import json
import os
import re
import glob
from urllib.parse import urlparse, unquote_plus

README_PATH = "README.md"

RESTRICTED_DOMAINS = [
    "draft.dev", "hackmamba.io", "catchyagency.com", "tripledart.com",
    "reo.dev", "growthx.ai", "peppercontent.io", "poweredbysearch.com",
    "nogood.io", "everydeveloper.com", "kalungi.com", "growthspreeofficial.com",
    "hoopy.io", "graphite.io"
]

def get_existing_urls(lines):
    existing_urls = set()
    for line in lines:
        if line.strip().startswith('|'):
            matches = re.findall(r'\]\((https?://[^)]+)\)', line)
            for m in matches:
                existing_urls.add(unquote_plus(m.rstrip('/').lower()))
    return existing_urls

def classify_newsletter(title, description, default_category):
    text = f"{title} {description}".lower()
    title_lower = title.lower()
    
    categories = {
        "Data Science & AI": ["ai", "machine learning", "data science", "llm", "neural network", "deep learning", "artificial intelligence", "data engineer"],
        "Frontend Development": ["frontend", "react", "vue", "angular", "css", "html", "web dev", "web development"],
        "Backend Development": ["backend", "api", "database", "sql", "nosql", "node.js", "django", "spring boot", "ruby on rails", "graphql"],
        "System Design & Architecture": ["system design", "architecture", "scalability", "distributed systems", "microservices", "high scalability"],
        "DevOps & Cloud": ["devops", "cloud", "aws", "azure", "gcp", "kubernetes", "docker", "ci/cd", "infrastructure", "sre", "site reliability"],
        "Language Specific": ["python", "golang", "rust", "javascript", "typescript", "java", "c++", "ruby", "php", "swift", "kotlin", "ios engineering"],
        "GTM": ["gtm", "go-to-market", "startup growth", "founder", "vc", "venture capital", "marketing", "mql", "sql getting"],
        "Developer Marketing": ["developer marketing", "devrel", "developer relations", "developer advocacy", "dev marketing"],
        "Technical Content Marketing": ["technical content", "content marketing", "technical writing"]
    }
    
    best_score = 0
    best_category = default_category
    
    for category, keywords in categories.items():
        score = 0
        for kw in keywords:
            # Word boundaries prevent partial matches (e.g., 'api' matching 'capital')
            pattern = r'(?<!\w)' + re.escape(kw) + r'(?!\w)'
            if re.search(pattern, title_lower):
                score += 3  # Higher weight for title matches
            elif re.search(pattern, text):
                score += 1
                
        if score > best_score:
            best_score = score
            best_category = category
            
    return best_category

def aggregate():
    json_files = glob.glob("newsletters*.json")
    if not json_files:
        print("No newsletters*.json found. Nothing to aggregate.")
        return

    newsletters = []
    successfully_parsed_files = []
    for jpath in json_files:
        try:
            with open(jpath, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    newsletters.extend(data)
            successfully_parsed_files.append(jpath)
        except Exception as e:
            print(f"Error parsing {jpath}: {e}")

    if not newsletters:
        print("No newsletters in JSON queues.")
        return

    with open(README_PATH, "r", encoding="utf-8") as f:
        lines = f.readlines()

    existing_urls = get_existing_urls(lines)
    changes_made = 0


    for nl in newsletters:

        raw_url = nl.get("url") or ""
        url = unquote_plus(raw_url.rstrip('/').lower())
        
        # 1. Deduplication Check
        if not url or url in existing_urls:
            print(f"Skipping {url}: Already exists in directory.")
            continue
            
        # 2. Blacklist Check
        domain = urlparse(raw_url).netloc.lower()
        if not domain:
            print(f"Skipping {raw_url}: Invalid URL or missing domain.")
            continue
        if any(domain == b or domain.endswith('.' + b) for b in RESTRICTED_DOMAINS):
            print(f"Skipping {url}: Domain is restricted.")
            continue
        
        # 3. Format and Inject
        raw_category = nl.get("category") or "General Software Engineering"
        title = nl.get("title") or "Unknown Title"
        description = nl.get("description") or "No description available."
        
        # Sanitize newlines and extra spaces to prevent breaking Markdown tables
        clean_title = re.sub(r'\s+', ' ', title).strip().replace('|', '\\|')
        clean_desc = re.sub(r'\s+', ' ', description).strip().replace('|', '\\|')
        
        category = classify_newsletter(clean_title, clean_desc, raw_category)
        
        display_link = "↗"
        frequency = nl.get("frequency") or "Varies"
        row = f"| **{clean_title}** | [{display_link}]({raw_url}) | {clean_desc} | {frequency} |"
        
        cat_header = f"## {category}"
        cat_idx = -1
        for i, l in enumerate(lines):
            if l.strip().lower() == cat_header.lower():
                cat_idx = i
                break
                
        if cat_idx != -1:
            table_header_idx = -1
            for i in range(cat_idx + 1, len(lines)):
                if lines[i].strip().startswith('##'):
                    break
                if '|------|' in lines[i].replace(' ', ''):
                    table_header_idx = i
                    break
            
            if table_header_idx != -1:
                insert_idx = table_header_idx + 1
                lines.insert(insert_idx, row + '\n')
                existing_urls.add(url)
                changes_made += 1
                print(f"Aggregated: {nl['title']} -> {category}")
            else:
                print(f"Error: Table not found for category {category}")
        else:
            # Category not found! Let's dynamically create it right above the footer
            footer_idx = -1
            for i, l in enumerate(lines):
                if '<!-- FOOTER -->' in l:
                    footer_idx = i
                    break
            
            if footer_idx != -1:
                # Insert the new section
                new_lines = [
                    f"\n",
                    f"## {category}\n",
                    f"\n",
                    f"| Name | Link | Description | Frequency |\n",
                    f"|------|------|-------------|-----------|\n",
                    f"{row}\n",
                    f"\n"
                ]
                for offset, new_line in enumerate(new_lines):
                    lines.insert(footer_idx + offset, new_line)
                existing_urls.add(url)
                changes_made += 1
                print(f"Aggregated (New Category Created): {nl['title']} -> {category}")
            else:
                print(f"Error: Category {category} not found and no <!-- FOOTER --> tag found in README to append to.")
    if changes_made > 0:
        cleaned_lines = []
        for i in range(len(lines)):
            if lines[i].strip() == '':
                prev_is_table = (len(cleaned_lines) > 0 and cleaned_lines[-1].strip().startswith('|'))
                next_is_table = False
                for j in range(i+1, len(lines)):
                    if lines[j].strip() != '':
                        if lines[j].strip().startswith('|'):
                            next_is_table = True
                        break
                if prev_is_table and next_is_table:
                    continue
            cleaned_lines.append(lines[i])

        # Alphabetize tables
        final_lines = []
        in_table = False
        table_rows = []
        header_rows = []
        
        for line in cleaned_lines:
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
                    # Sort by the first column (Name), case-insensitive, stripping bold markdown
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
        print(f"\nSuccessfully aggregated {changes_made} new newsletters into README.")
    else:
        print("\nNo new newsletters were aggregated.")
        
    # Only clear the queues that were successfully parsed to prevent data loss on corrupted files
    for jpath in successfully_parsed_files:
        if os.path.exists(jpath):
            os.remove(jpath)

if __name__ == "__main__":
    aggregate()
