#!/usr/bin/env python3
import json
import os
import sys
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse

JSON_PATH = "newsletters.json"

def fetch_inboxreads_data(url):
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        title_meta = soup.find('meta', property='og:title')
        title = title_meta.get('content', '') if title_meta else ''
        if not title:
            title_tag = soup.find('title')
            title = title_tag.text if title_tag else 'Unknown Title'
            
        title = title.replace(' - InboxReads', '').strip()

        desc_meta = soup.find('meta', attrs={'property': 'og:description'})
        if not desc_meta:
            desc_meta = soup.find('meta', attrs={'name': 'description'})
        description = desc_meta.get('content', 'No description available.') if desc_meta else 'No description available.'
        
        domain = urlparse(url).netloc
        display_link = f"{domain} [↗]"
        
        return {
            'title': title,
            'url': url,
            'display_link': display_link,
            'description': description,
            'frequency': 'Varies'
        }
    except Exception as e:
        return None

def discover_inboxreads():
    print("Starting InboxReads discovery via HackerNews Algolia...")
    queries = [
        ("software", "General Software Engineering"),
        ("developer", "Backend Development")
    ]
    
    discovered = []
    
    for query, category in queries:
        url = f"https://hn.algolia.com/api/v1/search?query=inboxreads.co/newsletter+{query}&hitsPerPage=10"
        try:
            r = requests.get(url, timeout=10)
            if r.status_code == 200:
                hits = r.json().get("hits", [])
                for hit in hits:
                    article_url = hit.get("url")
                    if article_url and "inboxreads.co/newsletter/" in article_url:
                        if not any(d['url'] == article_url for d in discovered):
                            print(f"Discovered InboxReads: {article_url}")
                            data = fetch_inboxreads_data(article_url)
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
            
        print(f"Successfully dumped {len(discovered)} InboxReads newsletters to {JSON_PATH}")
    else:
        print("No new InboxReads newsletters discovered.")

if __name__ == "__main__":
    discover_inboxreads()
