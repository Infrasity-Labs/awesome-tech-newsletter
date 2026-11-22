#!/usr/bin/env python3
"""Rebuild README.md and its graphics from the category files in directory/.

Run after aggregate.py, the link check and format_tables.py. Only the block
between the DIRECTORY markers in README.md is generated; everything else in the
README is hand-written and safe to edit.
"""
import glob
import json
import os
import re
from collections import Counter
from urllib.parse import urlparse

import readme_assets
from readme_utils import (CATEGORY_INFO, LAST_RUN_PATH, README_PATH, ROOT, TABLE_HEADER, TABLE_RULE,
                          category_path, plural, read_all, row_fields, slugify, write_category)

PREVIEW_VISIBLE = 8     # rows shown per category before "Show more"
PREVIEW_HIDDEN = 12     # extra rows behind "Show more"
ASSETS = "./.github/assets"
START, END = "<!-- DIRECTORY:START -->", "<!-- DIRECTORY:END -->"

PLATFORMS = [("Substack", ("substack.com",)), ("Hashnode", ("hashnode.dev", "hashnode.com")),
             ("Beehiiv", ("beehiiv.com",)), ("Ghost", ("ghost.io", "ghost.org")),
             ("Medium", ("medium.com",)), ("DEV", ("dev.to",)),
             ("Kit / ConvertKit", ("kit.com", "convertkit.com", "ck.page")),
             ("Buttondown", ("buttondown.email", "buttondown.com"))]

def gh_anchor(heading):
    """GitHub's heading anchor: lowercase, punctuation dropped, spaces to hyphens."""
    return re.sub(r"[^\w\- ]", "", heading.lower()).replace(" ", "-")

def platform_of(url):
    host = urlparse(url).netloc.lower()
    for name, domains in PLATFORMS:
        if any(host == d or host.endswith("." + d) for d in domains):
            return name
    return "Other"

def load_last_run():
    try:
        with open(LAST_RUN_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("when", "—"), set(data.get("new_urls", []))
    except (OSError, ValueError):
        return "—", set()

def count_platforms():
    files = glob.glob(os.path.join(ROOT, "fetchers", "*.py"))
    return len([f for f in files if os.path.basename(f) not in ("utils.py", "__init__.py")])

def collect_stats(data):
    when, new_urls = load_last_run()
    cats, mix, present_new = [], Counter(), 0
    for category, rows in data:
        new = 0
        for r in rows:
            url = row_fields(r)[1]
            mix[platform_of(url)] += 1
            if url in new_urls:
                new += 1
        present_new += new
        cats.append({"label": category, "slug": slugify(category), "count": len(rows), "new": new})
    top = [(n, c) for n, c in mix.most_common() if n != "Other"][:5]
    other = sum(mix.values()) - sum(c for _, c in top)
    return {
        "total": sum(c["count"] for c in cats), "categories": len(cats), "platforms": count_platforms(),
        "added": present_new if new_urls else None, "when": when, "cats": cats,
        "platform_mix": top + ([("Other", other)] if other else []),
        "new_urls": new_urls,
    }

def picture(name, alt, width=None):
    w = f' width="{width}"' if width else ""
    return (f'<picture>\n  <source media="(prefers-color-scheme: dark)" srcset="{ASSETS}/{name}-dark.svg">\n'
            f'  <img{w} alt="{alt}" src="{ASSETS}/{name}-light.svg">\n</picture>')

def preview_rows(rows, new_urls, limit):
    """New rows first, then name-like entries (alphanumeric start, short titles), then the rest."""
    def rank(r):
        name, url, _, _ = row_fields(r)
        return (url not in new_urls, not (name[:1].isalnum() and len(name) <= 48))
    return sorted(rows, key=rank)[:limit]  # stable: alphabetical inside each rank

def table(rows, new_urls):
    out = [TABLE_HEADER.strip(), TABLE_RULE.strip()]
    for r in rows:
        if row_fields(r)[1] in new_urls:
            name = re.match(r"^\|\s*(\*\*.*?\*\*)", r)
            if name:
                r = r.replace(name.group(1), f'{name.group(1)} <img src="{ASSETS}/new.svg" height="16" alt="new">', 1)
        out.append(r)
    return "\n".join(out)

def generated_block(data, s):
    new_urls = s["new_urls"]
    rows_md = ["| Category | Newsletters | New | |", "|:--|--:|--:|:--|"]
    for c in s["cats"]:
        new = f"+{c['new']}" if c["new"] else "—"
        rows_md.append(f"| [{c['label']}](#{gh_anchor(c['label'])}) | **{c['count']:,}** | {new} | "
                       f"{picture('bars/' + c['slug'], plural(c['count']))} |".replace("\n", " "))
    parts = ["## Browse by category", "", "\n".join(rows_md), "",
             "<sub>Bars share one scale. Each category links to its full list.</sub>", "",
             "## Where they are published", "",
             '<p align="center">', picture("platform-mix", "Where these newsletters are published", "100%"), "</p>", ""]
    for (category, rows), c in zip(data, s["cats"]):
        desc = CATEGORY_INFO.get(category) or f"Newsletters in {category}."
        link = f"directory/{c['slug']}.md"
        new_txt = f" · <b>{c['new']}</b> new since the last run" if c["new"] else ""
        parts += [f"## {category}", "", f"{desc}<br>",
                  f'<sub><b>{c["count"]:,}</b> {"newsletter" if c["count"] == 1 else "newsletters"}{new_txt} · <a href="{link}">view all</a> · '
                  f'<a href="#browse-by-category">back to top ↑</a></sub>', ""]
        shown = preview_rows(rows, new_urls, PREVIEW_VISIBLE + PREVIEW_HIDDEN)
        head, rest = shown[:PREVIEW_VISIBLE], shown[PREVIEW_VISIBLE:]
        if head:
            parts += [table(head, new_urls), ""]
        if rest:
            parts += ["<details>", f"<summary><b>Show {len(rest)} more</b></summary>", "", table(rest, new_urls), "", "</details>", ""]
        parts += [f"**[View all {plural(c['count'])} in {category} →]({link})**", ""]
    return "\n".join(parts)

def main():
    data = read_all()
    # (re)write every category file so its title, definition and count stay current
    for category, rows in data:
        write_category(category_path(category), category, rows)
    s = collect_stats(data)
    readme_assets.write_all(s)
    with open(README_PATH, "r", encoding="utf-8") as f:
        text = f.read()
    a, b = text.find(START), text.find(END)
    if a == -1 or b == -1:
        raise SystemExit(f"README.md is missing the {START} / {END} markers")
    text = text[:a + len(START)] + "\n\n" + generated_block(data, s) + "\n" + text[b:]
    with open(README_PATH, "w", encoding="utf-8") as f:
        f.write(text)
    print(f"README rebuilt: {s['total']:,} newsletters, {s['categories']} categories, "
          f"{s['platforms']} platforms, {len(text) / 1024:.0f} KB")

if __name__ == "__main__":
    main()
