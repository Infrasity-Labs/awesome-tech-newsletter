#!/usr/bin/env python3
import json
import os
import requests
import xml.etree.ElementTree as ET
from urllib.parse import urlparse

import os
JSON_PATH = f"newsletters_{os.path.basename(__file__)}.json"

def fetch_hashnode_data(url):
    try:
        parsed_url = urlparse(url)
        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
        feed_url = f"{base_url}/rss.xml"
        
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(feed_url, headers=headers, timeout=10)
        response.raise_for_status()
        
        root = ET.fromstring(response.content)
        channel = root.find('channel')
        
        if channel is not None:
            title_node = channel.find('title')
            title = title_node.text.strip() if title_node is not None and title_node.text else 'Unknown Title'
            
            desc_node = channel.find('description')
            description = desc_node.text.strip() if desc_node is not None and desc_node.text else 'No description available.'
        else:
            title = 'Unknown Title'
            description = 'No description available.'
            
        domain = parsed_url.netloc
        display_link = f"{domain} [↗]"
        
        return {
            'title': title,
            'url': base_url,
            'display_link': display_link,
            'description': description,
            'frequency': 'Varies'
        }
    except Exception as e:
        return None

def discover_hashnode():
    print("Starting Hashnode discovery via HackerNews Algolia...")
    queries = [
        ("software engineering", "General Software Engineering"),
        ("backend developer", "Backend Development"),
        ("devops", "DevOps & Cloud"),
        ("system design", "System Design & Architecture"),
        ("developer marketing", "Developer Marketing"),
        ("devrel", "Developer Marketing"),
        ("technical content marketing", "Technical Content Marketing")
    ]
    
    discovered = []
    
    for query, category in queries:
        url = f"https://hn.algolia.com/api/v1/search?query=hashnode.dev+{query}&hitsPerPage=10"
        try:
            r = requests.get(url, timeout=10)
            if r.status_code == 200:
                hits = r.json().get("hits", [])
                for hit in hits:
                    article_url = hit.get("url")
                    if article_url and "hashnode.dev" in article_url:
                        parsed = urlparse(article_url)
                        base_url = f"{parsed.scheme}://{parsed.netloc}"
                        
                        if not any(d['url'] == base_url for d in discovered):
                            print(f"Discovered Hashnode: {base_url}")
                            data = fetch_hashnode_data(base_url)
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
                    data = json.load(f)
                    if isinstance(data, list):
                        existing = data
            except Exception:
                pass
        
        existing.extend(discovered)
        with open(JSON_PATH, "w", encoding="utf-8") as f:
            json.dump(existing, f, indent=2)
            
        print(f"Successfully dumped {len(discovered)} Hashnode newsletters to {JSON_PATH}")
    else:
        print("No new Hashnode newsletters discovered.")

if __name__ == "__main__":
    discover_hashnode()
