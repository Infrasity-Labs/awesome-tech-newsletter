#!/usr/bin/env python3
import json
import os
import logging
from urllib.parse import urlparse
#Same Here
try:
    from fetchers.utils import get_random_user_agent, get_search_queries, request_with_retry
except ModuleNotFoundError:
    from utils import get_random_user_agent, get_search_queries, request_with_retry

JSON_PATH = f"newsletters_{os.path.basename(__file__)}.json"

logger = logging.getLogger(__name__)

def discover_producthunt():
    token = os.environ.get('PRODUCTHUNT_TOKEN')
    if not token:
        logger.warning("Warning: PRODUCTHUNT_TOKEN is not set. Skipping Product Hunt API crawler.")
        return

    logger.info("Starting Product Hunt discovery via GraphQL API v2...")
    
    url = "https://api.producthunt.com/v2/api/graphql"
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
        #Added for Randomized headers
        "User-Agent": get_random_user_agent(),
    }
    
    # Query for recent posts, retrieving their topics to filter for newsletters
    query = """
    query {
      posts(first: 100, topic: "newsletters") {
        edges {
          node {
            name
            description
            url
            website
            topics {
              edges {
                node {
                  name
                }
              }
            }
          }
        }
      }
    }
    """
    
    discovered = []
    
    try:
        r = request_with_retry("POST", url, headers=headers, json={'query': query}, timeout=10)
        if r.status_code == 200:
            data = r.json()
            posts = data.get('data', {}).get('posts', {}).get('edges', [])
            
            for post_edge in posts:
                node = post_edge.get('node', {})
                name = node.get('name', 'Unknown Title')
                desc = node.get('description', 'No description available.')
                website = node.get('website')
                ph_url = node.get('url')
                topics = [t['node']['name'].lower() for t in node.get('topics', {}).get('edges', [])]
                
                text_corpus = f"{name} {desc} {' '.join(topics)}".lower()
                
                category = "General Software Engineering"
                is_tech = False
                
                queries = get_search_queries(append_newsletter=False)
                for query, cat in queries:
                    if query in text_corpus:
                        is_tech = True
                        category = cat
                        break
                
                target_url = website if website else ph_url
                
                if is_tech and target_url:
                    domain = urlparse(target_url).netloc
                    
                    if not any(d['url'] == target_url for d in discovered):
                        logger.info("Discovered Product Hunt: %s", target_url)
                        discovered.append({
                            'title': name,
                            'url': target_url,
                            'display_link': f"{domain} [↗]",
                            'description': desc,
                            'frequency': 'Varies',
                            'category': category
                        })
        else:
            logger.error("Product Hunt API Error: HTTP %d", r.status_code)
    except Exception as e:
        logger.error("Error querying Product Hunt API: %s", e)

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
            
        logger.info(
            "Successfully dumped %d Product Hunt newsletters to %s",
            len(discovered),
            JSON_PATH,
        )
    else:
        logger.warning("No new Product Hunt newsletters discovered.")

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s"
    )
    discover_producthunt()
