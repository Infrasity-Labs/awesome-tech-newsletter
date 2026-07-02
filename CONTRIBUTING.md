# Contributing to Awesome Developer Newsletters

Thank you for considering contributing to the **Awesome Developer Newsletters** directory! 

This repo is maintained by [Infrasity](https://infrasity.com) and updated regularly.

This document serves as a set of guidelines for contributing to the repository.

---
## Ways to Contribute
### 1. Submit a Newsletter

If you know of a developer newsletter that isn't listed here yet, you can easily add it yourself! The main directory is driven completely by the `README.md` file.

1. **Fork the repository** to your own GitHub account.
2. Open `README.md` and locate the correct **Category** (General Software Engineering, Backend Development, Frontend Development, Data Science & AI, etc.).
3. Add a new row to the Markdown table in the respective category.
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
* If you want to add a new source, simply create a new Python script (e.g. `my_source.py`) that discovers newsletters and dumps them into `newsletters.json`.
* The `aggregate.py` script then takes all new newsletters from `newsletters.json`, deduplicates them, categorizes them automatically using keywords, and injects them directly into the `README.md` tables.

---

### 3. Improve the Code

If you want to improve existing Python fetchers, fix bugs, or add new ones, here is how you can set up the project locally on your machine:

1. **Clone the repository**:
   ```bash
   git clone https://github.com/Infrasity-Labs/awesome-developer-newsletter.git
   cd awesome-developer-newsletter
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
   ```

5. Check that the `README.md` file updated correctly with your changes, and then submit a Pull Request!

---

### 4. Pull Request Guidelines

* **Keep it relevant:** Only add newsletters that are strictly relevant to software engineers, developers, data scientists, or IT professionals.
* **No spam:** Please do not add promotional spam or generic marketing lists.
* **Clean Code:** If you are contributing Python code to the `fetchers/` directory or `aggregate.py`, please ensure your code is well-commented and handles network errors gracefully.

---

### 5. Found a Bug?

If you spot a broken link, a discontinued newsletter, or a bug in one of our Python fetchers, please [open an Issue](https://github.com/Infrasity-Labs/awesome-developer-newsletter/issues/new) on the repository so we can fix it!

Thank you for helping Infrasity build the best developer newsletter directory on the internet!
