#!/usr/bin/env python3

import json
import os
import requests
import logging
from urllib.parse import urlparse
# In utils.py i have made a function that Fetches Random Chrome User Agent
try:
    from fetchers.utils import get_random_user_agent, get_search_queries, extract_metadata
except ModuleNotFoundError:
    from utils import get_random_user_agent, get_search_queries, extract_metadata
JSON_PATH = f"newsletters_{os.path.basename(__file__)}.json"

logger = logging.getLogger(__name__)

def fetch_beehiiv_data(url):
    try:
        parsed_url = urlparse(url)
        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
        
        meta = extract_metadata(base_url)    
        title = meta['title'].replace(' | Beehiiv', '').replace('Home | ', '').strip()
        description = meta['description']
        
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
        logger.error("Failed to fetch Beehiiv metadata for %s", url)
        return None

def discover_beehiiv():
    logger.info("Starting Beehiiv discovery via HackerNews Algolia...")
    queries = get_search_queries(append_newsletter=True)
    
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
                            logger.info("Discovered Beehiiv: %s", base_url)
                            data = fetch_beehiiv_data(base_url)
                            if data:
                                data['category'] = category
                                discovered.append(data)
        except Exception as e:
            logger.error("Error querying HN for %s", query)

    if discovered:
        existing = []
        if os.path.exists(JSON_PATH):
            try:
                with open(JSON_PATH, "r", encoding="utf-8") as f:
                    existing = json.load(f)
            except:
                logger.error("Error reading existing JSON data from %s", JSON_PATH)
                pass
        
        existing.extend(discovered)
        with open(JSON_PATH, "w", encoding="utf-8") as f:
            json.dump(existing, f, indent=2)
            
        logger.info(
            "Successfully dumped %d Beehiiv newsletters to %s",
            len(discovered),
            JSON_PATH,
        )
    else:
        logger.warning("No new Beehiiv newsletters discovered.")

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s"
    )
    discover_beehiiv()
