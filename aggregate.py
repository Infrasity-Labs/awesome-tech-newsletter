import json
import os
import re
from urllib.parse import urlparse, unquote_plus

README_PATH = "README.md"
JSON_PATH = "newsletters.json"

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
    
    # Keyword map to categories
    categories = {
        "Data Science & AI": ["ai", "machine learning", "data science", "llm", "neural network", "deep learning", "artificial intelligence", "data engineer"],
        "Frontend Development": ["frontend", "react", "vue", "angular", "css", "html", "web dev", "web development"],
        "Backend Development": ["backend", "api", "database", "sql", "nosql", "node.js", "django", "spring boot", "ruby on rails", "graphql"],
        "System Design & Architecture": ["system design", "architecture", "scalability", "distributed systems", "microservices", "high scalability"],
        "DevOps & Cloud": ["devops", "cloud", "aws", "azure", "gcp", "kubernetes", "docker", "ci/cd", "infrastructure", "sre", "site reliability"],
        "Language Specific": ["python", "golang", "rust", "javascript", "typescript", "java", "c++", "ruby", "php", "swift", "kotlin", "ios engineering"],
        "GTM": ["gtm", "go-to-market", "startup growth", "founder", "vc", "venture capital"],
        "Developer Marketing": ["developer marketing", "devrel", "developer relations", "developer advocacy", "dev marketing"],
        "Technical Content Marketing": ["technical content", "content marketing", "technical writing"]
    }
    
    for category, keywords in categories.items():
        if any(keyword in text for keyword in keywords):
            return category
            
    return default_category

def aggregate():
    if not os.path.exists(JSON_PATH):
        print(f"No {JSON_PATH} found. Nothing to aggregate.")
        return

    with open(JSON_PATH, "r", encoding="utf-8") as f:
        try:
            newsletters = json.load(f)
        except json.JSONDecodeError:
            print(f"Error parsing {JSON_PATH}.")
            return

    if not newsletters:
        print("No newsletters in JSON queue.")
        return

    with open(README_PATH, "r", encoding="utf-8") as f:
        lines = f.readlines()

    existing_urls = get_existing_urls(lines)
    changes_made = 0

    if not isinstance(newsletters, list):
        print(f"Error: {JSON_PATH} must contain a list of newsletters.")
        return
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
        with open(README_PATH, "w", encoding="utf-8") as f:
            f.writelines(lines)
        print(f"\nSuccessfully aggregated {changes_made} new newsletters into README.")
    else:
        print("\nNo new newsletters were aggregated.")
        
    # Always clear the queue after running so we don't process them again
    with open(JSON_PATH, "w", encoding="utf-8") as f:
        json.dump([], f)

if __name__ == "__main__":
    aggregate()
