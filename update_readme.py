#!/usr/bin/env python3
import argparse
import re
import sys
import os
from fetchers.substack import fetch_substack_data
from fetchers.inboxreads import fetch_inboxreads_data

README_PATH = 'README.md'

RESTRICTED_DOMAINS = [
    "draft.dev", "hackmamba.io", "catchyagency.com", "tripledart.com",
    "reo.dev", "growthx.ai", "peppercontent.io", "poweredbysearch.com",
    "nogood.io", "everydeveloper.com", "kalungi.com", "growthspreeofficial.com",
    "hoopy.io", "graphite.io"
]

def get_existing_entries(readme_content):
    entries = set()
    row_pattern = re.compile(r'\\|\\s*\\*\\*([^*]+)\\*\\*\\s*\\|\\s*\\[[^\\]]+\\]\\(([^)]+)\\)')
    for match in row_pattern.finditer(readme_content):
        title = match.group(1).strip().lower()
        url = match.group(2).strip().lower().rstrip('/')
        entries.add(title)
        entries.add(url)
    return entries

def update_readme(urls, category):
    if not os.path.exists(README_PATH):
        print(f"Error: {README_PATH} not found.")
        return

    with open(README_PATH, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    content = "".join(lines)
    existing_entries = get_existing_entries(content)
    
    new_rows = []
    for url in urls:
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
            
        if any(b in url.lower() for b in RESTRICTED_DOMAINS):
            print(f"Skipping {url}: Domain is restricted.")
            continue
            
        normalized_url = url.lower().rstrip('/')
        if normalized_url in existing_entries:
            print(f"Skipping {url}: URL already in README.")
            continue
            
        print(f"Fetching data for {url}...")
        if 'substack.com' in url:
            data = fetch_substack_data(url)
        elif 'inboxreads.co' in url:
            data = fetch_inboxreads_data(url)
        else:
            print(f"Unsupported URL domain for {url}. Assuming it's a general link.")
            data = {
                'title': 'Unknown Title',
                'url': url,
                'display_link': f"{url.split('//')[-1].split('/')[0]} [↗]",
                'description': 'No description available.',
                'frequency': 'Varies'
            }
            
        if not data:
            print(f"Failed to fetch data for {url}")
            continue
            
        if data['title'].lower() in existing_entries:
            print(f"Skipping {url}: Title '{data['title']}' already in README.")
            continue
            
        row = f"| **{data['title']}** | [{data['display_link']}]({data['url']}) | {data['description']} | {data['frequency']} |"
        new_rows.append(row)
        existing_entries.add(url.lower())
        existing_entries.add(data['title'].lower())
    
    if not new_rows:
        print("No new entries to add.")
        return

    cat_header = f"## {category}"
    cat_idx = -1
    for i, line in enumerate(lines):
        if line.strip().lower() == cat_header.lower():
            cat_idx = i
            break
            
    if cat_idx == -1:
        print(f"Error: Category '{category}' not found.")
        return
        
    table_header_idx = -1
    for i in range(cat_idx + 1, len(lines)):
        if lines[i].strip().startswith('##'):
            break
        if '|------|' in lines[i].replace(' ', ''):
            table_header_idx = i
            break
            
    if table_header_idx == -1:
        print(f"Error: Table not found under category '{category}'.")
        return
        
    insert_idx = table_header_idx + 1
    for i in range(table_header_idx + 1, len(lines)):
        stripped = lines[i].strip()
        if stripped == '' or stripped.startswith('##') or stripped.startswith('---'):
            insert_idx = i
            break
        insert_idx = i + 1
            
    for row in reversed(new_rows):
        lines.insert(insert_idx, row + '\n')
        
    with open(README_PATH, 'w', encoding='utf-8') as f:
        f.writelines(lines)
        
    print(f"Successfully added {len(new_rows)} entries to '{category}' category.")

CATEGORIZED_URLS = {
    "General Software Engineering": [],
    "Backend Development": [],
    "System Design & Architecture": [],
    "Language Specific": [],
    "DevOps & Cloud": [],
    "GTM": [],
    "Developer Marketing": [],
    "Technical Content Marketing": []
}

if __name__ == "__main__":
    for category, urls in CATEGORIZED_URLS.items():
        if urls:
            print(f"Processing {len(urls)} URLs for category '{category}'")
            update_readme(urls, category)
