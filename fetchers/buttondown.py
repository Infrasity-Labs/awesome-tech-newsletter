#!/usr/bin/env python3
import json
import os
import requests
import logging
from urllib.parse import urlparse
# random user-agent import 
try:
    from fetchers.utils import get_random_user_agent, get_search_queries, extract_metadata
except ModuleNotFoundError:
    from utils import get_random_user_agent, get_search_queries, extract_metadata

JSON_PATH = f"newsletters_{os.path.basename(__file__)}.json"

logger = logging.getLogger(__name__)

def fetch_buttondown_data(url):
    try:
        parsed_url = urlparse(url)
        path_parts = [p for p in parsed_url.path.split('/') if p]
        first_path = f"/{path_parts[0]}" if path_parts else ""
        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}{first_path}"

        meta = extract_metadata(base_url)
        title = meta['title'].replace(' | Buttondown', '').strip()
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
        return None

def discover_buttondown():
    logger.info("Starting Buttondown discovery via HackerNews Algolia...")
    queries = get_search_queries(append_newsletter=True)
    
    discovered = []
    
    for query, category in queries:
        url = "https://hn.algolia.com/api/v1/search"
        params = {
            "query": f"buttondown.email {query}",
            "hitsPerPage": 10
        }
        try:
            #Also Added randomized headers
            headers = {'User-Agent': get_random_user_agent()}
            r = requests.get(url, params=params, timeout=10, headers=headers)
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
                            logger.info("Discovered Buttondown: %s", base_url)
                            data = fetch_buttondown_data(base_url)
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
            "Successfully dumped %d Buttondown newsletters to %s",
            len(discovered),
            JSON_PATH,
        )
    else:
        logger.warning("No new Buttondown newsletters discovered.")

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s"
    )
    discover_buttondown()
