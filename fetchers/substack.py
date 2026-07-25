#!/usr/bin/env python3
import json
import os
import sys
import requests
import logging
import xml.etree.ElementTree as ET
from urllib.parse import urlparse

#Same Here Added random User Agent
try:
    from fetchers.utils import get_random_user_agent, get_search_queries
except ModuleNotFoundError:
    from utils import get_random_user_agent, get_search_queries

JSON_PATH = f"newsletters_{os.path.basename(__file__)}.json"

logger = logging.getLogger(__name__)

def fetch_substack_data(url):
    try:
        parsed_url = urlparse(url)
        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
        feed_url = f"{base_url}/feed"
        
        headers = {
            #Same here added randomized user agent
            'User-Agent': get_random_user_agent(),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
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
    except requests.exceptions.RequestException as e:
        if e.response is not None and e.response.status_code == 403:
            logger.warning("Substack/Cloudflare blocked access to %s (403 Forbidden). Falling back to basic data.", url)
            domain = parsed_url.netloc
            title = domain.split('.')[0].replace('-', ' ').title()
            return {
                'title': title,
                'url': base_url,
                'display_link': f"{domain} [↗]",
                'description': 'Description unavailable (Blocked by Cloudflare).',
                'frequency': 'Varies'
            }
        return None
    except Exception:
        return None

def discover_substack():
    logger.info("Starting Substack discovery via HackerNews Algolia...")
    queries = get_search_queries(append_newsletter=True)
    
    discovered = []
    
    for query, category in queries:
        url = f"https://hn.algolia.com/api/v1/search?query=substack.com+{query}&hitsPerPage=10"
        try:
            #Added Randomized user agent
            headers_algolia = {'User-Agent': get_random_user_agent()}
            r = requests.get(url, headers=headers_algolia, timeout=10)
            if r.status_code == 200:
                hits = r.json().get("hits", [])
                for hit in hits:
                    article_url = hit.get("url")
                    if article_url and "substack.com" in article_url:
                        parsed = urlparse(article_url)
                        base_url = f"{parsed.scheme}://{parsed.netloc}"
                        
                        if not any(d['url'] == base_url for d in discovered):
                            logger.info("Discovered Substack: %s", base_url)
                            data = fetch_substack_data(base_url)
                            if data:
                                data['category'] = category
                                discovered.append(data)
        except Exception as e:
            logger.error("Error querying HN for %s: %s", query, e)

    if discovered:
        existing = []
        if os.path.exists(JSON_PATH):
            try:
                with open(JSON_PATH, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        existing = data
            except Exception:
                logger.error("Error reading existing JSON data from %s", JSON_PATH)
                pass
        
        existing.extend(discovered)
        with open(JSON_PATH, "w", encoding="utf-8") as f:
            json.dump(existing, f, indent=2)
            
        logger.info(
            "Successfully dumped %d Substack newsletters to %s",
            len(discovered),
            JSON_PATH,
        )
    else:
        logger.warning("No new Substack newsletters discovered.")

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s"
    )
    discover_substack()
