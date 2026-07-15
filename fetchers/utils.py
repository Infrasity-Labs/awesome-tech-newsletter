#!/usr/bin/env python3
import random
import json
import os

def get_random_user_agent():
    """Returns a random popular user agent string to avoid scraping blocks."""
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Safari/605.1.15",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_3_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Mobile/15E148 Safari/604.1"
    ]
    return random.choice(user_agents)

def get_search_queries(append_newsletter=True):
    """
    Reads config.json and returns a list of tuples: (query, category).
    If append_newsletter is True, appends words like 'newsletter' to the queries.
    """
    config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config.json")
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            categories = json.load(f)
    except Exception:
        return []

    queries = []
    suffixes = ["newsletter", "digest", "weekly"] if append_newsletter else [""]
    
    for category, keywords in categories.items():
        for kw in keywords:
            for suffix in suffixes:
                query = f"{kw} {suffix}".strip()
                queries.append((query, category))
    
    return queries