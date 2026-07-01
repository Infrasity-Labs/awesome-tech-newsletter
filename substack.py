
#!/usr/bin/env python3
import sys
import argparse
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse

def fetch_substack_data(url):
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        title_meta = soup.find('meta', property='og:title')
        title = title_meta['content'] if title_meta else ''
        if not title:
            title_tag = soup.find('title')
            title = title_tag.text if title_tag else 'Unknown Title'
            
        title = title.split(' | ')[0].strip()

        desc_meta = soup.find('meta', property='og:description')
        if not desc_meta:
            desc_meta = soup.find('meta', name='description')
        description = desc_meta['content'] if desc_meta else 'No description available.'
        
        parsed_url = urlparse(url)
        domain = parsed_url.netloc
        display_link = f"{domain} [↗]"
        
        frequency = 'Varies'
        
        return {
            'title': title,
            'url': url,
            'display_link': display_link,
            'description': description,
            'frequency': frequency
        }

    except requests.exceptions.RequestException as e:
        print(f"Network error fetching data from {url}: {e}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"Error parsing data from {url}: {e}", file=sys.stderr)
        return None

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch Substack newsletter details.")
    parser.add_argument("url", help="URL of the Substack newsletter")
    args = parser.parse_args()
    
    data = fetch_substack_data(args.url)
    if data:
        print(f"| **{data['title']}** | [{data['display_link']}]({data['url']}) | {data['description']} | {data['frequency']} |")
