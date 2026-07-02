#!/usr/bin/env python3
import json
import os
import requests

JSON_PATH = "newsletters.json"

def discover_inboxreads():
    print("Starting InboxReads discovery via internal API...")
    
    # We query InboxReads API directly instead of relying on HackerNews (since nobody posts directory links on HN).
    # These are valid slugs in the InboxReads database.
    queries = [
        ("tech", "General Software Engineering"),
        ("programming", "Backend Development"),
        ("software-engineering", "System Design & Architecture"),
        ("web-development", "Frontend Development"),
        ("data-science", "Data Science & AI")
    ]
    
    discovered = []
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    
    for slug, category in queries:
        url = f"https://api.inboxreads.co/topics/{slug}"
        try:
            r = requests.get(url, headers=headers, timeout=15)
            if r.status_code == 200:
                data = r.json()
                newsletters = data.get("newsletters", [])
                
                # InboxReads returns a large array of newsletters for the topic
                for nl in newsletters:
                    url_name = nl.get("url_name")
                    if not url_name:
                        continue
                        
                    title = nl.get("name", "Unknown Title")
                    description = nl.get("tagline", "No description available.")
                    
                    # InboxReads paywalled/removed their individual newsletter pages, so we use a DuckDuckGo redirect 
                    # to automatically send the user to the newsletter's actual official website!
                    from urllib.parse import quote_plus
                    query = quote_plus(f'"{title}" newsletter')
                    article_url = f"https://duckduckgo.com/?q=!ducky+{query}"
                    
                    if not any(d['url'] == article_url for d in discovered):
                        print(f"Discovered InboxReads: {title}")
                        discovered.append({
                            'title': title,
                            'url': article_url,
                            'display_link': "Website [↗]",
                            'description': description,
                            'frequency': 'Varies',
                            'category': category
                        })
                        
                        # Just grab a few per category to simulate discovery rate limit and prevent flooding
                        if len([d for d in discovered if d['category'] == category]) >= 10:
                            break
        except Exception as e:
            print(f"Error querying InboxReads API for {slug}: {e}")

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
            
        print(f"Successfully dumped {len(discovered)} InboxReads newsletters to {JSON_PATH}")
    else:
        print("No new InboxReads newsletters discovered.")

if __name__ == "__main__":
    discover_inboxreads()
