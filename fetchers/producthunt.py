#!/usr/bin/env python3
import json
import os
import requests
from urllib.parse import urlparse

JSON_PATH = "newsletters.json"

def discover_producthunt():
    token = os.environ.get('PRODUCTHUNT_TOKEN')
    if not token:
        print("Warning: PRODUCTHUNT_TOKEN is not set. Skipping Product Hunt API crawler.")
        return

    print("Starting Product Hunt discovery via GraphQL API v2...")
    
    url = "https://api.producthunt.com/v2/api/graphql"
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
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
        r = requests.post(url, headers=headers, json={'query': query}, timeout=10)
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
                
                is_tech = any(keyword in text_corpus for keyword in [
                    'developer', 'software', 'api', 'tech', 'programming', 'code', 
                    'devops', 'backend', 'frontend', 'ai', 'machine learning', 
                    'data science', 'cloud', 'security', 'web3', 'crypto', 'saas', 
                    'open source', 'engineering'
                ])
                
                target_url = website if website else ph_url
                
                if is_tech and target_url:
                    domain = urlparse(target_url).netloc
                    
                    if not any(d['url'] == target_url for d in discovered):
                        print(f"Discovered Product Hunt: {target_url}")
                        discovered.append({
                            'title': name,
                            'url': target_url,
                            'display_link': f"{domain} [↗]",
                            'description': desc,
                            'frequency': 'Varies',
                            'category': 'General Software Engineering' # aggregate.py will intelligently re-categorize this!
                        })
        else:
            print(f"Product Hunt API Error: HTTP {r.status_code}")
    except Exception as e:
        print(f"Error querying Product Hunt API: {e}")

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
            
        print(f"Successfully dumped {len(discovered)} Product Hunt newsletters to {JSON_PATH}")
    else:
        print("No new Product Hunt newsletters discovered.")

if __name__ == "__main__":
    discover_producthunt()
