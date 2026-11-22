#!/usr/bin/env python3
import re
import sys
import os
import subprocess
import requests
import concurrent.futures
import glob

DIRECTORY = "directory"
URL_RE = re.compile(r'\]\((https?://[^\s)]+)\)')

def directory_files():
    return sorted(glob.glob(os.path.join(DIRECTORY, "*.md")))

def get_urls_to_check():
    """Return [(path, line_number, url)] to ping.

    If directory/ has uncommitted changes (e.g. right after aggregate.py ran) only the
    newly added URLs are checked; otherwise every URL in every category file is.
    """
    result = subprocess.run(["git", "diff", "--unified=0", "--", DIRECTORY], capture_output=True, text=True)

    only_new = None
    if result.stdout.strip():
        print("Detected uncommitted changes. Checking ONLY newly added URLs...")
        only_new = set()
        for line in result.stdout.splitlines():
            # Only look at lines that were added
            if line.startswith('+') and not line.startswith('+++'):
                only_new.update(URL_RE.findall(line))
        if not only_new:
            return []
    else:
        print("No uncommitted changes detected. Checking ALL URLs in directory/...")

    urls = []
    for path in directory_files():
        with open(path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                if line.strip().startswith('|'):
                    for match in URL_RE.findall(line):
                        if only_new is None or match in only_new:
                            urls.append((path, line_num, match))
    return urls

def check_url(item):
    path, line_num, url = item
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
        if r.status_code >= 400 and not (r.status_code in [401, 403, 406, 429] or 500 <= r.status_code < 600):
            return (path, line_num, url, False, f"HTTP {r.status_code}")
        return (path, line_num, url, True, "OK")
    except requests.exceptions.Timeout:
        # Don't delete on timeout, the site might just be slow
        return (path, line_num, url, True, "Timeout (Allowed)")
    except requests.exceptions.ConnectionError:
        # Don't delete on connection error (could be transient DNS or SSL issues)
        return (path, line_num, url, True, "ConnectionError (Allowed)")
    except Exception as e:
        return (path, line_num, url, False, str(e))

def remove_failed(failed_items):
    by_file = {}
    for path, line_num, *_ in failed_items:
        by_file.setdefault(path, set()).add(line_num)

    for path, failed_line_nums in by_file.items():
        with open(path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        with open(path, 'w', encoding='utf-8') as f:
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
            path, line_num, url, success, msg = res
            if not success:
                failed.append(res)
                print(f"❌ {path}:{line_num}: {url} - {msg}")
            else:
                pass # Silent on success to avoid cluttering PR logs

    if failed:
        print(f"\nFound {len(failed)} dead URLs. Removing them from directory/...")
        remove_failed(failed)
        print(f"Successfully removed broken links.")
        sys.exit(0)
    else:
        print(f"\n✅ All {len(urls)} checked URLs are healthy!")
        sys.exit(0)

if __name__ == "__main__":
    main()
