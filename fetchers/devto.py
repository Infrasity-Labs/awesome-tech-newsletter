#!/usr/bin/env python3
import json
import os
import re
import requests
from urllib.parse import urlparse

JSON_PATH = "newsletters.json"

def discover_devto():
    print("Starting Dev.to discovery via public API...")
    
    tags = [
        "newsletter", "newsletters", "programming", "software", 
        "webdev", "python", "javascript", "devops", "ai", 
        "machinelearning", "datascience", "backend", "frontend",
        "react", "rust", "golang", "devrel"
    ]
    
    discovered = []
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    
    # Regex to find known newsletter platforms. Removed ghost.io due to CDN false positives, added buttondown
    newsletter_regex = r'https?://[a-zA-Z0-9.-]+\.(?:substack\.com|beehiiv\.com|hashnode\.dev|buttondown\.email)'
    
    for tag in tags:
        url = f"https://dev.to/api/articles?tag={tag}&per_page=30"
        try:
            r = requests.get(url, headers=headers, timeout=10)
            if r.status_code == 200:
                articles = r.json()
                
                for article in articles:
                    article_id = article.get('id')
                    canonical_url = article.get('canonical_url', '')
                    
                    target_url = None
                    
                    if canonical_url and re.search(newsletter_regex, canonical_url):
                        target_url = re.search(newsletter_regex, canonical_url).group(0)
                    else:
                        # Fetch the full article to run regex against body_markdown
                        try:
                            detail_r = requests.get(f"https://dev.to/api/articles/{article_id}", headers=headers, timeout=10)
                            if detail_r.status_code == 200:
                                body = detail_r.json().get('body_markdown', '')
                                matches = re.findall(newsletter_regex, body)
                                if matches:
                                    target_url = matches[0]
                        except Exception:
                            pass
                    
                    if target_url:
                        parsed = urlparse(target_url)
                        base_url = f"{parsed.scheme}://{parsed.netloc}"
                        domain = parsed.netloc
                        
                        if not any(d['url'] == base_url for d in discovered):
                            print(f"Discovered via Dev.to (Tag: {tag}): {base_url}")
                            discovered.append({
                                'title': article.get('title', 'Unknown Title'),
                                'url': base_url,
                                'display_link': f"{domain} [↗]",
                                'description': article.get('description', 'No description'),
                                'frequency': 'Varies',
                                'category': 'General Software Engineering' # Aggregate.py handles category mapping automatically
                            })
            else:
                print(f"Dev.to API Error for tag {tag}: HTTP {r.status_code}")
        except Exception as e:
            print(f"Error querying Dev.to API for tag {tag}: {e}")

    if discovered:
        existing = []
        if os.path.exists(JSON_PATH):
            try:
                with open(JSON_PATH, "r", encoding="utf-8") as f:
                    existing = json.load(f)
            except:
                pass
        
        existing.extend(discovered)
        with open(JSON_PATH, "w", encoding="utf-8") as f:
            json.dump(existing, f, indent=2)
            
        print(f"Successfully dumped {len(discovered)} Dev.to newsletters to {JSON_PATH}")
    else:
        print("No new Dev.to newsletters discovered.")

if __name__ == "__main__":
    discover_devto()
