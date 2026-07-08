#!/usr/bin/env python3
import json
import os
import sys
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse

JSON_PATH = f"newsletters_{os.path.basename(__file__)}.json"

def fetch_medium_data(url):
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        title_meta = soup.find('meta', property='og:title')
        title = title_meta.get('content', '') if title_meta else ''
        if not title:
            title_tag = soup.find('title')
            title = title_tag.text if title_tag else 'Unknown Title'
            
        title = title.replace(" – Medium", "").replace(" - Medium", "").strip()

        desc_meta = soup.find('meta', attrs={'property': 'og:description'})
        if not desc_meta:
            desc_meta = soup.find('meta', attrs={'name': 'description'})
        description = desc_meta.get('content', 'No description available.') if desc_meta else 'No description available.'
        
        parsed_url = urlparse(url)
        domain = parsed_url.netloc
        if domain == "medium.com":
            path_parts = [p for p in parsed_url.path.split('/') if p]
            if path_parts:
                display_link = f"medium.com/{path_parts[0]} [↗]"
            else:
                display_link = f"{domain} [↗]"
        else:
            display_link = f"{domain} [↗]"
        
        return {
            'title': title,
            'url': url,
            'display_link': display_link,
            'description': description.strip(),
            'frequency': 'Varies'
        }
    except requests.exceptions.RequestException as e:
        print(f"Network error fetching Medium data for {url}: {e}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"Error parsing Medium data for {url}: {e}", file=sys.stderr)
        return None

def discover_medium():
    print("Starting Medium discovery via HackerNews Algolia...")
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
    existing_urls = set()    
    if os.path.exists(JSON_PATH):        
        try:           
            with open(JSON_PATH, "r", encoding="utf-8") as f:                
                for item in json.load(f):                    
                 if "url" in item:                       
                  existing_urls.add(item["url"].rstrip("/").lower())     
        except Exception:            
            pass   
        if os.path.exists("README.md"):      
         try:          
            import re            
            with open("README.md", "r", encoding="utf-8") as f:              
             for line in f:                   
                 matches = re.findall(r"\]\((https?://[^)]+)\)", line)                   
                 for m in matches:                       
                    existing_urls.add(m.rstrip("/").lower())        
         except Exception:            
          pass
    
    for query, category in queries:
        url = "https://hn.algolia.com/api/v1/search"
        params = {
            "query": f"medium.com {query}",
            "hitsPerPage": 10
        }
        try:
            r = requests.get(url, params=params, timeout=15)
            if r.status_code == 200:
                hits = r.json().get("hits", [])
                for hit in hits:
                    article_url = hit.get("url")
                    if article_url and "medium.com" in article_url:
                        parsed = urlparse(article_url)
                        netloc = parsed.netloc
                        path_parts = [p for p in parsed.path.split('/') if p]
                        
                        reserved_paths = {"p", "tag", "m", "search", "about", "policy", "membership", "plans", "creators", "topic", "topics", "jobs", "press"}
                        
                        if netloc.endswith(".medium.com"):
                            username = netloc.replace(".medium.com", "")
                            base_url = f"https://medium.com/@{username}"
                        elif netloc == "medium.com" and path_parts:
                            first_part = path_parts[0]
                            if first_part in reserved_paths:
                                continue
                            base_url = f"https://medium.com/{first_part}"
                        else:
                            continue
                        
                        if base_url.rstrip("/").lower() not in existing_urls and not any(d['url'] == base_url for d in discovered):
                            print(f"Discovered Medium: {base_url}")
                            data = fetch_medium_data(base_url)
                            if data:
                                data['category'] = category
                                discovered.append(data)
        except requests.exceptions.RequestException as e:
            print(f"Network error querying HN for {query}: {e}", file=sys.stderr)
        except Exception as e:
            print(f"Error querying HN for {query}: {e}", file=sys.stderr)

    if discovered:
        existing = []
        if os.path.exists(JSON_PATH):
            try:
                with open(JSON_PATH, "r", encoding="utf-8") as f:
                    existing = json.load(f)
            except (json.JSONDecodeError, OSError):
                pass
        
        existing.extend(discovered)
        with open(JSON_PATH, "w", encoding="utf-8") as f:
            json.dump(existing, f, indent=2)
            
        print(f"Successfully dumped {len(discovered)} Medium newsletters to {JSON_PATH}")
    else:
        print("No new Medium newsletters discovered.")

if __name__ == "__main__":
    discover_medium()
