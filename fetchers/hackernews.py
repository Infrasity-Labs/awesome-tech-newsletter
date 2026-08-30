#!/usr/bin/env python3
import json
import os
import requests
import logging
import concurrent.futures
# from bs4 import BeautifulSoup (shouldn't need it now)
from urllib.parse import urlparse

try:
    from fetchers.utils import get_random_user_agent, get_search_queries, extract_metadata 
except ModuleNotFoundError:
    from utils import get_random_user_agent, get_search_queries, extract_metadata

JSON_PATH = f"newsletters_{os.path.basename(__file__)}.json"

logger = logging.getLogger(__name__)

EXCLUDED_DOMAINS = [
    "substack.com", "beehiiv.com", "hashnode.dev", "buttondown.email", 
    "mailchi.mp", "campaign-archive.com", "ck.page", "curated.co", 
    "mailerlite.com", "mailerpage.io", "flodesk.com", "ghost.io", 
    "medium.com", "dev.to", "github.com", "ycombinator.com", "youtube.com"
]

def fetch_hn_metadata(url, fallback_title):
    try:
        '''headers = {
            'User-Agent': get_random_user_agent()
        }
        # Only timeout 5s to skip slow sites
        response = requests.get(url, headers=headers, timeout=5)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        desc_meta = soup.find('meta', attrs={'property': 'og:description'})
        if not desc_meta:
            desc_meta = soup.find('meta', attrs={'name': 'description'})
        description = (desc_meta.get('content') if desc_meta else None) or fallback_title '''
        meta = extract_metadata(url)
        description = meta['description']
        
        return description.strip()
    except Exception:
        logger.error("Failed to fetch metadata for %s", url)
        return fallback_title

def process_query(query_data):
    query, category = query_data
    results = []
    url = "https://hn.algolia.com/api/v1/search"
    params = {
        "query": query,
        "hitsPerPage": 20
    }
    try:
        headers_algolia = {'User-Agent': get_random_user_agent()}
        r = requests.get(url, params=params, headers=headers_algolia, timeout=10)
        if r.status_code == 200:
            hits = r.json().get("hits", [])
            for hit in hits:
                article_url = hit.get("url")
                title = hit.get("title") or "Unknown Title"
                
                if not article_url:
                    continue
                    
                parsed = urlparse(article_url)
                domain = parsed.netloc.lower()
                
                # Ensure it's not one of our already covered platforms
                if any(domain == d or domain.endswith('.' + d) for d in EXCLUDED_DOMAINS):
                    continue
                    
                logger.info("Discovered HackerNews Custom Domain: %s", article_url)
                description = fetch_hn_metadata(article_url, fallback_title=title)
                
                results.append({
                    'title': title,
                    'url': article_url,
                    'display_link': f"{domain} [↗]",
                    'description': description,
                    'frequency': 'Varies',
                    'category': category
                })
    except Exception as e:
        logger.error("Error querying HN for %s", query)
    return results

def discover_hackernews():
    logger.info("Starting HackerNews standalone newsletter discovery via Algolia...")
    queries = get_search_queries(append_newsletter=True)
    
    discovered = []
    seen_urls = set()
    
    # Process queries using a thread pool of 20 workers
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        future_to_query = {executor.submit(process_query, q): q for q in queries}
        for future in concurrent.futures.as_completed(future_to_query):
            results = future.result()
            for r in results:
                if r['url'] not in seen_urls:
                    seen_urls.add(r['url'])
                    discovered.append(r)

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
            "Successfully dumped %d HackerNews newsletters to %s",
            len(discovered),
            JSON_PATH,
        )
    else:
        logger.warning("No new HackerNews newsletters discovered.")

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s"
    )
    discover_hackernews()
