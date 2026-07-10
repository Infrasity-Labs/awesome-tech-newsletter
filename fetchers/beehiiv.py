#!/usr/bin/env python3

import json
import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
# In utils.py i have made a function that Fetches Random Chrome User Agent
try:
    from fetchers.utils import get_random_user_agent
except ModuleNotFoundError:
    from utils import get_random_user_agent
JSON_PATH = f"newsletters_{os.path.basename(__file__)}.json"

def fetch_beehiiv_data(url):
    try:
        parsed_url = urlparse(url)
        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
        #I have Replaced the single user agent with the function that gets random user agent for avoiding Error
        headers = {
            'User-Agent': get_random_user_agent()
        }
        response = requests.get(base_url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        title_meta = soup.find('meta', property='og:title')
        title = title_meta.get('content', '') if title_meta else ''
        if not title:
            title_tag = soup.find('title')
            title = title_tag.text if title_tag else 'Unknown Title'
            
        title = title.replace(' | Beehiiv', '').replace('Home | ', '').strip()

        desc_meta = soup.find('meta', attrs={'property': 'og:description'})
        if not desc_meta:
            desc_meta = soup.find('meta', attrs={'name': 'description'})
        description = desc_meta.get('content', 'No description available.') if desc_meta else 'No description available.'
        
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

def discover_beehiiv():
    print("Starting Beehiiv discovery via HackerNews Algolia...")
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
            "query": f"beehiiv.com {query}",
            "hitsPerPage": 10
        }
        try:
            #I have also added here 
            headers = {'User-Agent': get_random_user_agent()}
            r = requests.get(url, params=params, timeout=10,headers=headers)
            if r.status_code == 200:
                hits = r.json().get("hits", [])
                for hit in hits:
                    article_url = hit.get("url")
                    if article_url and "beehiiv.com" in article_url:
                        parsed = urlparse(article_url)
                        base_url = f"{parsed.scheme}://{parsed.netloc}"
                        
                        if not any(d['url'] == base_url for d in discovered):
                            print(f"Discovered Beehiiv: {base_url}")
                            data = fetch_beehiiv_data(base_url)
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
            
        print(f"Successfully dumped {len(discovered)} Beehiiv newsletters to {JSON_PATH}")
    else:
        print("No new Beehiiv newsletters discovered.")

if __name__ == "__main__":
    discover_beehiiv()
