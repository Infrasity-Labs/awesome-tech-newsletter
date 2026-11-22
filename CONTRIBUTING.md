# Contributing to Tech Newsletters Directory

Thank you for considering contributing to the **Tech Newsletters Directory**! 

This repo is maintained by [Infrasity](https://infrasity.com) and updated regularly.

This document serves as a set of guidelines for contributing to the repository.

---
## Ways to Contribute
### 1. Submit a Newsletter

If you know of a developer newsletter that isn't listed here yet, you can easily add it yourself! The entries live in [`directory/`](directory), one Markdown file per category. `README.md` is generated from those files, so don't edit its tables.

1. **Fork the repository** to your own GitHub account.
2. Open the file for the right **category** in `directory/` (for example `directory/backend-development.md` or `directory/data-science-ai.md`).
3. Add a new row to the Markdown table in that file. Order doesn't matter, tables are sorted automatically.
4. Follow the exact table format:
   ```markdown
   | **Newsletter Name** | [↗](link) | A short description of the newsletter. | Frequency |
   ```
5. Submit a **Pull Request** with a short description of the newsletter you added!

---

### 2. The Automated Fetchers

This repository uses automated Python scripts to fetch newsletters from major platforms (like Substack, Beehiiv, Hashnode, Dev.to) automatically.

If you are a developer, you can contribute by adding new automated scrapers!
* All fetcher scripts are located in the `fetchers/` directory.
* If you want to add a new source, simply create a new Python script (e.g. `my_source.py`) that discovers newsletters and dumps them into `newsletters.json`. The workflow in `.github/workflows/update_newsletters.yml` picks up every script in `fetchers/` automatically.
* The `aggregate.py` script then takes all new newsletters from `newsletters.json`, deduplicates them, categorizes them automatically using keywords, and adds them to the matching file in `directory/`. `build_readme.py` then rebuilds `README.md` and the graphics in `.github/assets/`.

---

### 3. Improve the Code

If you want to improve existing Python fetchers, fix bugs, or add new ones, here is how you can set up the project locally on your machine:

1. **Clone the repository**:
   ```bash
   git clone https://github.com/Infrasity-Labs/awesome-tech-newsletter.git
   cd awesome-tech-newsletter
   ```

2. **Set up environment variables** (if required):
   If you are testing scripts that require API keys (like Product Hunt), create a `.env` file in the root directory:
   ```bash
   touch .env
   # Add your API keys inside, for example:
   # PRODUCTHUNT_TOKEN=your_secret_key_here
   ```

3. **Install the dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Run a fetcher locally to test your changes**:
   ```bash
   python3 fetchers/beehiiv.py
   python3 aggregate.py
   python3 checks/format_tables.py
   python3 build_readme.py
   ```

5. Check that the files in `directory/` and `README.md` updated correctly with your changes, and then submit a Pull Request!

#### Project structure

```text
.
├── directory/            # The data: one Markdown file per category (edit these)
├── fetchers/             # One script per source platform
├── aggregate.py          # Dedupes, categorizes (config.json) and files new newsletters into directory/
├── checks/               # url_check.py removes dead links, format_tables.py sorts tables
├── build_readme.py       # Rebuilds README.md and the graphics from directory/
├── readme_assets.py      # Draws the banner, bars and charts (light and dark SVGs)
├── readme_utils.py       # Shared helpers and the category definitions
├── last_run.json         # What the last run added (drives the NEW tags)
└── config.json           # Category keywords used to file newsletters
```

To add a category, add keywords for it in `config.json` and (optionally) a one-line definition in `CATEGORY_INFO` in `readme_utils.py`. Its file in `directory/` is created the first time a newsletter lands in it.

---

### 4. Pull Request Guidelines

* **Keep it relevant:** Only add newsletters that are strictly relevant to software engineers, developers, data scientists, or IT professionals.
* **No spam:** Please do not add promotional spam or generic marketing lists.
* **Clean Code:** If you are contributing Python code to the `fetchers/` directory or `aggregate.py`, please ensure your code is well-commented and handles network errors gracefully.

---

### 5. Found a Bug?

If you spot a broken link, a discontinued newsletter, or a bug in one of our Python fetchers, please [open an Issue](https://github.com/Infrasity-Labs/awesome-tech-newsletter/issues/new) on the repository so we can fix it!

Thank you for helping Infrasity build the best tech newsletter directory on the internet!
