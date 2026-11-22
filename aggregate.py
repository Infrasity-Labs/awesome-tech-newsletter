import json
import os
import re
import glob
import logging
from datetime import datetime, timezone
from urllib.parse import urlparse, unquote_plus
from readme_utils import LAST_RUN_PATH, category_path, read_all, write_category

CONFIG_PATH = "config.json"

logger = logging.getLogger(__name__)

try:
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        CATEGORIES = json.load(f)
except Exception as e:
    logger.warning("Could not load %s, using empty categories. Error: %s", CONFIG_PATH, e)
    CATEGORIES = {}

RESTRICTED_DOMAINS = [
    "draft.dev", "hackmamba.io", "catchyagency.com", "tripledart.com",
    "reo.dev", "growthx.ai", "peppercontent.io", "poweredbysearch.com",
    "nogood.io", "everydeveloper.com", "kalungi.com", "growthspreeofficial.com",
    "hoopy.io", "graphite.io"
]

def get_existing_urls(categories):
    """Normalized URLs of every row in every category file. `categories` maps name -> rows."""
    existing_urls = set()
    for rows in categories.values():
        for line in rows:
            for m in re.findall(r'\]\((https?://[^)]+)\)', line):
                existing_urls.add(unquote_plus(m.rstrip('/').lower()))
    return existing_urls

def record_run(added_urls):
    """Remember what this run added so the README can tag it NEW and show the run time."""
    data = {
        "when": datetime.now(timezone.utc).strftime("%d %b %Y, %H:%M UTC"),
        "added": len(added_urls),
        "new_urls": sorted(added_urls),
    }
    with open(LAST_RUN_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
        f.write("\n")

def classify_newsletter(title, description, default_category):
    text = f"{title} {description}".lower()
    title_lower = title.lower()
    
    best_score = 0
    best_category = default_category
    
    for category, keywords in CATEGORIES.items():
        score = 0
        for kw in keywords:
            # Word boundaries prevent partial matches (e.g., 'api' matching 'capital')
            pattern = r'(?<!\w)' + re.escape(kw) + r'(?!\w)'
            if re.search(pattern, title_lower):
                score += 3  # Higher weight for title matches
            elif re.search(pattern, text):
                score += 1
                
        if score > best_score:
            best_score = score
            best_category = category
            
    return best_category

def aggregate():
    json_files = glob.glob("newsletters*.json")
    if not json_files:
        logger.info("No newsletters*.json found. Nothing to aggregate.")
        return

    newsletters = []
    successfully_parsed_files = []
    for jpath in json_files:
        try:
            with open(jpath, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    newsletters.extend(data)
            successfully_parsed_files.append(jpath)
        except Exception as e:
            logger.error("Error parsing %s: %s", jpath, e)

    if not newsletters:
        logger.info("No newsletters in JSON queues.")
        return

    # category name -> list of raw table rows, loaded from directory/*.md
    categories = dict(read_all())
    existing_urls = get_existing_urls(categories)
    added_urls = []
    touched = set()

    for nl in newsletters:

        raw_url = nl.get("url") or ""
        url = unquote_plus(raw_url.rstrip('/').lower())

        # 1. Deduplication Check
        if not url or url in existing_urls:
            logger.info("Skipping %s: Already exists in directory.", url)
            continue

        # 2. Blacklist Check
        domain = urlparse(raw_url).netloc.lower()
        if not domain:
            logger.info("Skipping %s: Invalid URL or missing domain.", raw_url)
            continue
        if any(domain == b or domain.endswith('.' + b) for b in RESTRICTED_DOMAINS):
            logger.info("Skipping %s: Domain is restricted.", url)
            continue

        # 3. Format and Inject
        raw_category = nl.get("category") or "General Software Engineering"
        title = nl.get("title") or "Unknown Title"
        description = nl.get("description") or "No description available."

        # Skip scraper junk: placeholder titles and blocked-page descriptions
        if "undefined" in title.lower() or title.strip().lower() == "home" \
                or "blocked by cloudflare" in description.lower():
            logger.info("Skipping %s: Placeholder title or blocked page.", url)
            continue

        # Sanitize newlines and extra spaces to prevent breaking Markdown tables
        clean_title = re.sub(r'\s+', ' ', title).strip().replace('|', '\\|')
        clean_desc = re.sub(r'\s+', ' ', description).strip().replace('|', '\\|')

        category = classify_newsletter(clean_title, clean_desc, raw_category)

        display_link = "↗"
        frequency = nl.get("frequency") or "Varies"
        row = f"| **{clean_title}** | [{display_link}]({raw_url}) | {clean_desc} | {frequency} |"

        # A category with no file yet is created automatically
        categories.setdefault(category, []).append(row)
        touched.add(category)
        existing_urls.add(url)
        added_urls.append(raw_url)
        logger.info("Aggregated: %s -> %s", nl['title'], category)

    for category in touched:
        write_category(category_path(category), category, categories[category])

    record_run(added_urls)
    if added_urls:
        logger.info("Successfully aggregated %d new newsletters into directory/.", len(added_urls))
    else:
        logger.info("No new newsletters were aggregated.")

    # Only clear the queues that were successfully parsed to prevent data loss on corrupted files
    for jpath in successfully_parsed_files:
        if os.path.exists(jpath):
            os.remove(jpath)

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s"
    )
    aggregate()
