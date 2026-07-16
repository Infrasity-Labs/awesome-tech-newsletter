#!/usr/bin/env python3
import re
import sys
import os
import subprocess
import requests
import concurrent.futures

README_PATH = "README.md"

def get_urls_to_check():
    # Check if there are uncommitted changes in README.md (e.g. after aggregate.py runs)
    result = subprocess.run(["git", "diff", "--unified=0", README_PATH], capture_output=True, text=True)
    
    urls = []
    if result.stdout.strip():
        print("Detected uncommitted changes. Checking ONLY newly added URLs...")
        added_urls = set()
        for line in result.stdout.splitlines():
            # Only look at lines that were added
            if line.startswith('+') and not line.startswith('+++'):
                matches = re.findall(r'\]\((https?://[^\s)]+)\)', line)
                added_urls.update(matches)
                
        if not added_urls:
            return []
            
        # Map these new URLs to their exact line numbers in the current README.md
        with open(README_PATH, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                if line.strip().startswith('|'):
                    matches = re.findall(r'\]\((https?://[^\s)]+)\)', line)
                    for match in matches:
                        if match in added_urls:
                            urls.append((line_num, match))
    else:
        print("No uncommitted changes detected. Checking ALL URLs in README.md...")
        with open(README_PATH, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                if line.strip().startswith('|'):
                    matches = re.findall(r'\]\((https?://[^\s)]+)\)', line)
                    for match in matches:
                        urls.append((line_num, match))
                        
    return urls

def check_url(item):
    line_num, url = item
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        # Use HEAD first for speed, fallback to GET if forbidden or method not allowed
        try:
            r = requests.head(url, headers=headers, timeout=10, allow_redirects=True)
            if r.status_code >= 400:
                r = requests.get(url, headers=headers, timeout=10)
        except requests.RequestException:
            r = requests.get(url, headers=headers, timeout=10)
        
        # 403, 401, 406, 429, and 50x are often returned by firewalls, rate limits, or temporary downtime. Allow them.
        if r.status_code >= 400 and r.status_code not in [401, 403, 406, 429, 500, 502, 503, 504]: 
            return (line_num, url, False, f"HTTP {r.status_code}")
        return (line_num, url, True, "OK")
    except requests.exceptions.Timeout:
        # Don't delete on timeout, the site might just be slow
        return (line_num, url, True, "Timeout (Allowed)")
    except requests.exceptions.ConnectionError:
        # Don't delete on connection error (could be transient DNS or SSL issues)
        return (line_num, url, True, "ConnectionError (Allowed)")
    except Exception as e:
        return (line_num, url, False, str(e))

def remove_failed(failed_items):
    failed_line_nums = {res[0] for res in failed_items}
    
    with open(README_PATH, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    with open(README_PATH, 'w', encoding='utf-8') as f:
        for i, line in enumerate(lines, 1):
            if i not in failed_line_nums:
                f.write(line)

def main():
    urls = get_urls_to_check()
    
    if not urls:
        print(f"No URLs found to check.")
        sys.exit(0)
        
    print(f"Pinging {len(urls)} URLs...")
    
    failed = []
    # Use threads to check URLs concurrently for speed
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        results = executor.map(check_url, urls)
        
        for res in results:
            line_num, url, success, msg = res
            if not success:
                failed.append(res)
                print(f"❌ Line {line_num}: {url} - {msg}")
            else:
                pass # Silent on success to avoid cluttering PR logs

    if failed:
        print(f"\nFound {len(failed)} dead URLs. Removing them from {README_PATH}...")
        remove_failed(failed)
        print(f"Successfully removed broken links.")
        sys.exit(0)
    else:
        print(f"\n✅ All {len(urls)} checked URLs are healthy!")
        sys.exit(0)

if __name__ == "__main__":
    main()
