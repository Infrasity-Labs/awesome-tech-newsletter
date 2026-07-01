import json
import os
import re

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
                existing_urls.add(m.rstrip('/').lower())
    return existing_urls

def classify_newsletter(title, description, default_category):
    text = f"{title} {description}".lower()
    
    # Keyword map to categories
    categories = {
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

    for nl in newsletters:
        url = nl.get("url", "").rstrip('/').lower()
        
        # 1. Deduplication Check
        if not url or url in existing_urls:
            print(f"Skipping {url}: Already exists in directory.")
            continue
            
        # 2. Blacklist Check
        from urllib.parse import urlparse
        domain = urlparse(nl.get("url", "")).netloc.lower()
        if any(domain == b or domain.endswith('.' + b) for b in RESTRICTED_DOMAINS):
            print(f"Skipping {url}: Domain is restricted.")
            continue
        
        # 3. Format and Inject
        raw_category = nl.get("category", "General Software Engineering")
        category = classify_newsletter(nl.get('title', ''), nl.get('description', ''), raw_category)
        
        row = f"| **{nl['title']}** | [{nl['display_link']}]({nl['url']}) | {nl['description']} | {nl['frequency']} |"
        
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
            print(f"Error: Category {category} not found in README")

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
