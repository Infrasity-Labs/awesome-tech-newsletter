#!/usr/bin/env python3
import sys
import argparse
import requests
import xml.etree.ElementTree as ET
from urllib.parse import urlparse

def fetch_substack_data(url):
    try:
        parsed_url = urlparse(url)
        # Extract base url to always target the publication's root feed
        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
        feed_url = f"{base_url}/feed"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(feed_url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # Parse XML Feed
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
        frequency = 'Varies'
        
        return {
            'title': title,
            'url': base_url, # Return the base URL instead of a specific post
            'display_link': display_link,
            'description': description,
            'frequency': frequency
        }

    except requests.exceptions.RequestException as e:
        print(f"Network error fetching data from {url}: {e}", file=sys.stderr)
        return None
    except ET.ParseError as e:
        print(f"Error parsing XML data from {url}: {e}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"Unexpected error processing {url}: {e}", file=sys.stderr)
        return None

if __name__ == "__main__":
    # URLs are now hardcoded directly in the script instead of being passed via CLI
    HARDCODED_URLS = [
        "https://example.substack.com"
    ]
    
    for url in HARDCODED_URLS:
        data = fetch_substack_data(url)
        if data:
            print(f"| **{data['title']}** | [{data['display_link']}]({data['url']}) | {data['description']} | {data['frequency']} |")
