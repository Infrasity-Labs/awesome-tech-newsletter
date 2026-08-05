import json
import os
import re
import glob
import logging
from urllib.parse import urlparse, unquote_plus
from readme_utils import table_sort_key

README_PATH = "README.md"
CONFIG_PATH = "config.json"

logger = logging.getLogger(__name__)

try:
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        CATEGORIES = json.load(f)
except Exception as e:
    logger.warning(
        "Could not load %s, using empty categories. Error: %s", CONFIG_PATH, e
    )
    CATEGORIES = {}

RESTRICTED_DOMAINS = [
    "draft.dev",
    "hackmamba.io",
    "catchyagency.com",
    "tripledart.com",
    "reo.dev",
    "growthx.ai",
    "peppercontent.io",
    "poweredbysearch.com",
    "nogood.io",
    "everydeveloper.com",
    "kalungi.com",
    "growthspreeofficial.com",
    "hoopy.io",
    "graphite.io",
]


def get_existing_urls(lines):
    existing_urls = set()
    for line in lines:
        if line.strip().startswith("|"):
            matches = re.findall(r"\]\((https?://[^)]+)\)", line)
            for m in matches:
                existing_urls.add(unquote_plus(m.rstrip("/").lower()))
    return existing_urls


def normalize_title(title):
    """Normalize newsletter titles for duplicate comparison."""
    return re.sub(r"\s+", " ", title).strip().lower()


def get_existing_titles(lines):
    existing_titles = set()

    for line in lines:
        if line.strip().startswith("|"):
            # Extract the newsletter title from: | **Title** | ...
            match = re.match(r"\|\s*\*\*(.*?)\*\*\s*\|", line)

            if match:
                title = normalize_title(match.group(1))
                existing_titles.add(title)

    return existing_titles


def normalize_title(title):
    """Normalize newsletter titles for duplicate comparison."""
    return re.sub(r"\s+", " ", title).strip().lower()


def get_existing_titles(lines):
    existing_titles = set()

    for line in lines:
        if line.strip().startswith("|"):
            # Extract the newsletter title from: | **Title** | ...
            match = re.match(r"\|\s*\*\*(.*?)\*\*\s*\|", line)

            if match:
                title = normalize_title(match.group(1))
                existing_titles.add(title)

    return existing_titles


def classify_newsletter(title, description, default_category):
    text = f"{title} {description}".lower()
    title_lower = title.lower()

    best_score = 0
    best_category = default_category

    for category, keywords in CATEGORIES.items():
        score = 0
        for kw in keywords:
            # Word boundaries prevent partial matches (e.g., 'api' matching 'capital')
            pattern = r"(?<!\w)" + re.escape(kw) + r"(?!\w)"
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

    with open(README_PATH, "r", encoding="utf-8") as f:
        lines = f.readlines()

    existing_urls = get_existing_urls(lines)
    existing_titles = get_existing_titles(lines)

    changes_made = 0

    for nl in newsletters:

        raw_url = nl.get("url") or ""
        url = unquote_plus(raw_url.rstrip("/").lower())

        # 1. Deduplication Check
        if not url:
            logger.info("Skipping: Missing URL.")
            continue

        if url in existing_urls:
            logger.info("Skipping %s: URL already exists.", url)
            continue

        if normalized_title in existing_titles:
            logger.info("Skipping %s: Title already exists.", title)
            continue

        # 2. Blacklist Check
        domain = urlparse(raw_url).netloc.lower()
        if not domain:
            logger.info("Skipping %s: Invalid URL or missing domain.", raw_url)
            continue
        if any(domain == b or domain.endswith("." + b) for b in RESTRICTED_DOMAINS):
            logger.info("Skipping %s: Domain is restricted.", url)
            continue

        # 3. Format and Inject
        raw_category = nl.get("category") or "General Software Engineering"
        title = nl.get("title") or "Unknown Title"
        description = nl.get("description") or "No description available."

        normalized_title = normalize_title(title)

        # Sanitize newlines and extra spaces to prevent breaking Markdown tables
        clean_title = re.sub(r"\s+", " ", title).strip().replace("|", "\\|")
        clean_desc = re.sub(r"\s+", " ", description).strip().replace("|", "\\|")

        category = classify_newsletter(clean_title, clean_desc, raw_category)

        display_link = "↗"
        frequency = nl.get("frequency") or "Varies"
        row = f"| **{clean_title}** | [{display_link}]({raw_url}) | {clean_desc} | {frequency} |"

        cat_header = f"## {category}"
        cat_idx = -1
        for i, l in enumerate(lines):
            if l.strip().lower() == cat_header.lower():
                cat_idx = i
                break

        if cat_idx != -1:
            table_header_idx = -1
            for i in range(cat_idx + 1, len(lines)):
                if lines[i].strip().startswith("##"):
                    break
                if "|------|" in lines[i].replace(" ", ""):
                    table_header_idx = i
                    break

            if table_header_idx != -1:
                insert_idx = table_header_idx + 1
                lines.insert(insert_idx, row + "\n")
                existing_urls.add(url)
                existing_titles.add(normalized_title)
                changes_made += 1
                logger.info("Aggregated: %s -> %s", nl["title"], category)
            else:
                logger.error("Error: Table not found for category %s", category)
        else:
            # Category not found! Let's dynamically create it right above the footer
            footer_idx = -1
            for i, l in enumerate(lines):
                if "<!-- FOOTER -->" in l:
                    footer_idx = i
                    break

            if footer_idx != -1:
                # Insert the new section
                new_lines = [
                    f"\n",
                    f"## {category}\n",
                    f"\n",
                    f"<details>\n",
                    f"<summary>View Newsletters</summary>\n",
                    f"\n",
                    f"| Name | Link | Description | Frequency |\n",
                    f"|------|------|-------------|-----------|\n",
                    f"{row}\n",
                    f"\n",
                    f"</details>\n",
                    f"\n",
                ]
                for offset, new_line in enumerate(new_lines):
                    lines.insert(footer_idx + offset, new_line)
                existing_urls.add(url)
                existing_titles.add(normalized_title)
                changes_made += 1
                logger.info(
                    "Aggregated (New Category Created): %s -> %s", nl["title"], category
                )
            else:
                logger.error(
                    "Error: Category %s not found and no <!-- FOOTER --> tag found in README to append to.",
                    category,
                )
    if changes_made > 0:
        cleaned_lines = []
        for i in range(len(lines)):
            if lines[i].strip() == "":
                prev_is_table = len(cleaned_lines) > 0 and cleaned_lines[
                    -1
                ].strip().startswith("|")
                next_is_table = False
                for j in range(i + 1, len(lines)):
                    if lines[j].strip() != "":
                        if lines[j].strip().startswith("|"):
                            next_is_table = True
                        break
                if prev_is_table and next_is_table:
                    continue
            cleaned_lines.append(lines[i])

        # Alphabetize tables
        final_lines = []
        in_table = False
        table_rows = []
        header_rows = []

        for line in cleaned_lines:
            if line.strip().startswith("|"):
                if not in_table:
                    in_table = True
                    table_rows = []
                    header_rows = [line]
                elif len(header_rows) < 2:
                    header_rows.append(line)
                else:
                    table_rows.append(line)
            else:
                if in_table:
                    # Sort and flush table
                    # Sort by the first column (Name), case-insensitive, stripping bold markdown
                    table_rows.sort(key=table_sort_key)

                    seen_titles = set()
                    unique_rows = []

                    for row in table_rows:
                        match = re.match(r"\|\s*\*\*(.*?)\*\*\s*\|", row)

                        if not match:
                            unique_rows.append(row)
                            continue

                        title = normalize_title(match.group(1))

                        if title in seen_titles:
                            continue

                        seen_titles.add(title)
                        unique_rows.append(row)

                    final_lines.extend(header_rows)
                    final_lines.extend(unique_rows)
                    in_table = False
                final_lines.append(line)

        if in_table:
            table_rows.sort(key=table_sort_key)

            seen_titles = set()
            unique_rows = []

        for row in table_rows:
            match = re.match(r"\|\s*\*\*(.*?)\*\*\s*\|", row)
            if not match:
                unique_rows.append(row)
                continue

            title = normalize_title(match.group(1))

            if title in seen_titles:
                continue

            seen_titles.add(title)
            unique_rows.append(row)

        final_lines.extend(header_rows)
        final_lines.extend(unique_rows)

        with open(README_PATH, "w", encoding="utf-8") as f:
            f.writelines(final_lines)
        logger.info(
            "Successfully aggregated %d new newsletters into README.", changes_made
        )
    else:
        logger.info("No new newsletters were aggregated.")

    # Only clear the queues that were successfully parsed to prevent data loss on corrupted files
    for jpath in successfully_parsed_files:
        if os.path.exists(jpath):
            os.remove(jpath)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
    )
    aggregate()
