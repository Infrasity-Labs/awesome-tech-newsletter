"""Draw the README graphics (banner, per-category bars, platform mix, NEW tag).

Stdlib only. Each graphic is written in a light and a dark variant and embedded
with <picture>, so GitHub shows the one that matches the reader's theme. System
fonts only, so the SVGs render identically inside GitHub's <img> sandbox.
"""
import os
from xml.sax.saxutils import escape

import hero_banner

ASSET_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".github", "assets")
REPO_SLUG = "infrasity-labs / awesome-tech-newsletter"

SANS = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif"
MONO = "ui-monospace, SFMono-Regular, Menlo, Consolas, monospace"

THEMES = {
    "light": dict(panel="#f6f8fa", line="#d1d9e0", card="#ffffff", fg="#1f2328", muted="#59636e",
                  dim="#818b98", accent="#6a5af0", accent_bg="#ece9ff", track="#eef1f4", green="#1a7f37"),
    "dark": dict(panel="#151b23", line="#30363d", card="#0d1117", fg="#f0f6fc", muted="#9198a1",
                 dim="#6e7681", accent="#8b7dff", accent_bg="#262046", track="#1d242d", green="#3fb950"),
}

def _t(x, y, text, size, fill, weight=None, anchor=None, family=SANS, spacing=None, tabular=False):
    a = [f'x="{x}"', f'y="{y}"', f'font-family="{family}"', f'font-size="{size}"', f'fill="{fill}"']
    if weight: a.append(f'font-weight="{weight}"')
    if anchor: a.append(f'text-anchor="{anchor}"')
    if spacing: a.append(f'letter-spacing="{spacing}"')
    if tabular: a.append('style="font-variant-numeric:tabular-nums"')
    return f'<text {" ".join(a)}>{escape(str(text))}</text>'

def _svg(w, h, label, body, desc=None):
    if desc:
        head = f'<title id="t">{escape(label)}</title>\n<desc id="d">{escape(desc)}</desc>\n'
        aria = 'aria-labelledby="t d"'
    else:
        head, aria = "", f'aria-label="{escape(label)}"'
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
            f'role="img" {aria}>\n{head}{body}\n</svg>\n')

def _panel(w, h, c, rx=14):
    return f'<rect x="0.5" y="0.5" width="{w - 1}" height="{h - 1}" rx="{rx}" fill="{c["panel"]}" stroke="{c["line"]}"/>'

def banner(s, c):
    added = "—" if s["added"] is None else f"+{s['added']:,}"
    tiles = [(f"{s['total']:,}", "newsletters tracked", False), (f"{s['categories']}", "categories", False),
             (f"{s['platforms']}", "platforms scanned", False), (added, "new since last run", True)]
    out = [_panel(1280, 360, c, 16),
           f'<rect x="64" y="56" width="34" height="34" rx="8" fill="{c["accent"]}"/>',
           f'<path d="M72 66 h18 v14 h-18 z M72 66 l9 8 l9 -8" fill="none" stroke="#ffffff" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"/>',
           _t(112, 82, REPO_SLUG, 15, c["muted"], family=MONO),
           _t(64, 138, "Tech Newsletters Directory", 50, c["fg"], 700, spacing=-1.2),
           _t(64, 172, "Newsletters for software engineers, developer advocates and technology founders. Refreshed nightly.", 19, c["muted"])]
    for i, (num, label, hot) in enumerate(tiles):
        x = 64 + i * 286
        if hot:
            out.append(f'<rect x="{x}" y="200" width="266" height="96" rx="12" fill="{c["accent_bg"]}" stroke="{c["accent"]}" stroke-opacity="0.55"/>')
        else:
            out.append(f'<rect x="{x}" y="200" width="266" height="96" rx="12" fill="{c["card"]}" stroke="{c["line"]}"/>')
        out.append(_t(x + 22, 252, num, 36, c["accent"] if hot else c["fg"], 700, spacing=-0.8, tabular=True))
        out.append(_t(x + 22, 278, label, 15, c["muted"]))
    out.append(f'<circle cx="70" cy="328" r="4" fill="{c["green"]}"/>')
    out.append(_t(82, 333, f"last updated {s['when']}  ·  next run 00:00 UTC", 13, c["dim"], family=MONO))
    desc = (f"{s['total']:,} newsletters across {s['categories']} categories, "
            f"scanned from {s['platforms']} platforms; last updated {s['when']}.")
    return _svg(1280, 360, "Tech Newsletters Directory", "\n".join(out), desc)

def bar(count, scale_max, c):
    w = 240
    fill = max(round(count / scale_max * w), 6) if count and scale_max else 0
    body = f'<rect x="0" y="0" width="{w}" height="12" rx="4" fill="{c["track"]}"/>'
    if fill:
        body += f'<rect x="0" y="0" width="{fill}" height="12" rx="4" fill="{c["accent"]}"/>'
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="12" viewBox="0 0 {w} 12">{body}</svg>\n'

def new_tag(c):
    return ('<svg xmlns="http://www.w3.org/2000/svg" width="38" height="18" viewBox="0 0 38 18">'
            f'<rect width="38" height="18" rx="9" fill="{c["accent"]}"/>'
            f'<text x="19" y="12.6" text-anchor="middle" font-family="{SANS}" font-size="10" font-weight="700" '
            'letter-spacing="0.6" fill="#ffffff">NEW</text></svg>\n')

def platform_mix(s, c):
    mix = [(l, v) for l, v in s["platform_mix"] if v > 0]
    total = sum(v for _, v in mix) or 1
    gap, usable = 2, 1222 - 2 * (len(mix) - 1)
    opac = [1.0, 0.8, 0.62, 0.46, 0.32, 0.22]
    out = [_panel(1280, 150, c), _t(28, 44, "Where these newsletters are published", 19, c["fg"], 650)]
    x = lx = 28.0
    for i, (label, v) in enumerate(mix):
        o = opac[min(i, len(opac) - 1)]
        w = max(usable * v / total, 4)
        out.append(f'<rect x="{x:.1f}" y="70" width="{w:.1f}" height="22" rx="4" fill="{c["accent"]}" fill-opacity="{o}"/>')
        x += w + gap
        text = f"{label}  {v:,} · {round(v / total * 100)}%"
        out.append(f'<rect x="{lx:.1f}" y="114" width="12" height="12" rx="3" fill="{c["accent"]}" fill-opacity="{o}"/>')
        out.append(_t(f"{lx + 20:.1f}", 125, text, 14, c["fg"]))
        lx += 20 + len(text) * 7.3 + 30
    return _svg(1280, 150, "Where newsletters are published", "\n".join(out))

def _write(name, text):
    path = os.path.join(ASSET_DIR, name)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)

def write_all(s):
    """Write every graphic. `s` comes from build_readme.collect_stats()."""
    scale = max((c["count"] for c in s["cats"]), default=1) or 1
    _write("hero.svg", hero_banner.render("newsletters", "Awesome Tech Newsletters",
           f"{s['total']:,} newsletters across {s['categories']} categories"))
    for theme, c in THEMES.items():
        _write(f"banner-{theme}.svg", banner(s, c))
        _write(f"platform-mix-{theme}.svg", platform_mix(s, c))
        for cat in s["cats"]:
            _write(f"bars/{cat['slug']}-{theme}.svg", bar(cat["count"], scale, c))
    _write("new.svg", new_tag(THEMES["light"]))
