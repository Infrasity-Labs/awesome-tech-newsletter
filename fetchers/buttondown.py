#!/usr/bin/env python3
import json
import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse

JSON_PATH = "newsletters.json"

def fetch_buttondown_data(url):
    try:
        parsed_url = urlparse(url)
        path_parts = [p for p in parsed_url.path.split('/') if p]
        first_path = f"/{path_parts[0]}" if path_parts else ""
        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}{first_path}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36'
        }
        response = requests.get(base_url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        title_meta = soup.find('meta', property='og:title')
        title = title_meta.get('content', '') if title_meta else ''
        if not title:
            title_tag = soup.find('title')
            title = title_tag.text if title_tag else 'Unknown Title'
            
        title = title.replace(' | Buttondown', '').strip()

        desc_meta = soup.find('meta', attrs={'property': 'og:description'})
        if not desc_meta:
            desc_meta = soup.find('meta', attrs={'name': 'description'})
        
        description = 'No description available.'
        if desc_meta:
            content = desc_meta.get('content')
            if content:
                description = content.strip()
        
        domain = parsed_url.netloc
        display_link = f"{domain} [↗]"
        
        return {
            'title': title,
            'url': base_url,
            'display_link': display_link,
            'description': description.strip(),
            'frequency': 'Varies'
        }
    except Exception as e:
        return None

def discover_buttondown():
    print("Starting Buttondown discovery via HackerNews Algolia...")
    queries = [
        ("software engineering", "General Software Engineering"),
        ("backend developer", "Backend Development"),
        ("devops", "DevOps & Cloud"),
        ("system design", "System Design & Architecture"),
        ("frontend", "Frontend Development"),
        ("react", "Frontend Development"),
        ("machine learning", "Data Science & AI"),
        ("data science", "Data Science & AI"),
        ("kubernetes", "DevOps & Cloud"),
        ("python", "Language Specific"),
        ("golang", "Language Specific"),
        ("rust", "Language Specific"),
        ("coding", "General Software Engineering"),
        ("architecture", "System Design & Architecture"),
        ("developer marketing", "Developer Marketing"),
        ("devrel", "Developer Marketing"),
        ("technical content marketing", "Technical Content Marketing")
    ]
    
    discovered = []
    
    for query, category in queries:
        url = "https://hn.algolia.com/api/v1/search"
        params = {
            "query": f"buttondown.email {query}",
            "hitsPerPage": 10
        }
        try:
            r = requests.get(url, params=params, timeout=10)
            if r.status_code == 200:
                hits = r.json().get("hits", [])
                for hit in hits:
                    article_url = hit.get("url")
                    if article_url and "buttondown.email" in article_url:
                        parsed = urlparse(article_url)
                        path_parts = [p for p in parsed.path.split('/') if p]
                        first_path = f"/{path_parts[0]}" if path_parts else ""
                        base_url = f"{parsed.scheme}://{parsed.netloc}{first_path}"
                        
                        if not any(d['url'] == base_url for d in discovered):
                            print(f"Discovered Buttondown: {base_url}")
                            data = fetch_buttondown_data(base_url)
                            if data:
                                data['category'] = category
                                discovered.append(data)
        except Exception as e:
            print(f"Error querying HN for {query}: {e}")

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
            
        print(f"Successfully dumped {len(discovered)} Buttondown newsletters to {JSON_PATH}")
    else:
        print("No new Buttondown newsletters discovered.")

if __name__ == "__main__":
    discover_buttondown()
