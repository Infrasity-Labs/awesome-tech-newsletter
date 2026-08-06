#!/usr/bin/env python3
import json
import os
import logging
from bs4 import BeautifulSoup
from urllib.parse import urlparse

try:
    from fetchers.utils import get_random_user_agent, get_search_queries, request_with_retry
except ModuleNotFoundError:
    from utils import get_random_user_agent, get_search_queries, request_with_retry

JSON_PATH = f"newsletters_{os.path.basename(__file__)}.json"

logger = logging.getLogger(__name__)

def fetch_convertkit_data(url):
    try:
        parsed_url = urlparse(url)
        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}"
        
        headers = {
            'User-Agent': get_random_user_agent()
        }
        response = request_with_retry("GET", base_url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        title_meta = soup.find('meta', property='og:title')
        title = title_meta.get('content', '') if title_meta else ''
        if not title:
            title_tag = soup.find('title')
            title = title_tag.text if title_tag else 'Unknown Title'
            
        title = title.replace(' | ConvertKit', '').strip()

        desc_meta = soup.find('meta', attrs={'property': 'og:description'})
        if not desc_meta:
            desc_meta = soup.find('meta', attrs={'name': 'description'})
        description = (desc_meta.get('content') if desc_meta else None) or 'No description available.'
        
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

def discover_convertkit():
    logger.info("Starting ConvertKit discovery via HackerNews Algolia...")
    queries = get_search_queries(append_newsletter=True)
    
    discovered = []
    
    for query, category in queries:
        url = "https://hn.algolia.com/api/v1/search"
        params = {
            "query": f"ck.page {query}",
            "hitsPerPage": 10
        }
        try:
            headers_algolia = {'User-Agent': get_random_user_agent()}
            r = request_with_retry("GET", url, params=params, headers=headers_algolia, timeout=10)
            if r.status_code == 200:
                hits = r.json().get("hits", [])
                for hit in hits:
                    article_url = hit.get("url")
                    if article_url and "ck.page" in article_url:
                        parsed = urlparse(article_url)
                        base_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
                        
                        if not any(d['url'] == base_url for d in discovered):
                            logger.info("Discovered ConvertKit: %s", base_url)
                            data = fetch_convertkit_data(base_url)
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
            "Successfully dumped %d ConvertKit newsletters to %s",
            len(discovered),
            JSON_PATH,
        )
    else:
        logger.warning("No new ConvertKit newsletters discovered.")

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s"
    )
    discover_convertkit()
