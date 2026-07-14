#!/usr/bin/env python3
#imported time
import time
import json
import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
#Same here 
try:
    from fetchers.utils import get_random_user_agent
except ModuleNotFoundError:
    from utils import get_random_user_agent

JSON_PATH = f"newsletters_{os.path.basename(__file__)}.json"

def discover_thebilig():
    print("Starting TheBilig discovery...")
    url = "https://www.thebilig.com/newsletters/editors-picks/best-tech-newsletters"
    #Added Randomized user agent
    headers = {'User-Agent': get_random_user_agent()}
    
    discovered = []
    
    try:
        r = requests.get(url, headers=headers, timeout=15)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, 'html.parser')
            
            # Find all newsletter cards
            cards = soup.find_all('a', href=lambda h: h and h.startswith('/newsletters/'))
            
            for card in cards:
                href = card.get('href')
                
                # Title
                h2 = card.find('h2')
                if not h2:
                    continue
                title = h2.text.strip()
                if title in ["More Editor's Picks", "Read tech newsletters without inbox clutter"]:
                    continue
                
                # Frequency and description
                p_tags = card.find_all('p')
                frequency = "Varies"
                description = "No description available."
                
                for p in p_tags:
                    if 'font-semibold' in p.get('class', []):
                        frequency = p.text.strip()
                    elif 'leading-7' in p.get('class', []):
                        description = p.text.strip()
                
                print(f"Fetching details for {title}...")
                #Adding a delay of 2 seconds between requests
                time.sleep(2)
                # Fetch external URL from internal page
                detail_url = f"https://www.thebilig.com{href}"
                try:
                    detail_r = requests.get(detail_url, headers=headers, timeout=10)
                    if detail_r.status_code == 200:
                        detail_soup = BeautifulSoup(detail_r.text, 'html.parser')
                        visit_link = detail_soup.find('a', string=lambda s: s and 'Visit official site' in s)
                        if visit_link:
                            external_url = visit_link.get('href')
                            if external_url:
                                parsed = urlparse(external_url)
                                if parsed.scheme and parsed.netloc:
                                    base_url = f"{parsed.scheme}://{parsed.netloc}"
                                    domain = parsed.netloc
                                    
                                    # Only add if we haven't discovered it in this session
                                    if not any(d['url'] == base_url for d in discovered):
                                        print(f"Discovered via TheBilig: {base_url}")
                                        discovered.append({
                                            'title': title,
                                            'url': base_url,
                                            'display_link': f"{domain} [↗]",
                                            'description': description,
                                            'frequency': frequency,
                                            'category': 'General Software Engineering' # Aggregate.py handles category mapping automatically
                                        })
                except Exception as e:
                    print(f"Error fetching details for {title}: {e}")
                    
        else:
            print(f"TheBilig Error: HTTP {r.status_code}")
    except Exception as e:
        print(f"Error querying TheBilig: {e}")

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
            
        print(f"Successfully dumped {len(discovered)} TheBilig newsletters to {JSON_PATH}")
    else:
        print("No new TheBilig newsletters discovered.")

if __name__ == "__main__":
    discover_thebilig()
