#!/usr/bin/env python3
"""Generate the 16alves02 GitHub profile's self-contained SVG cards."""
from __future__ import annotations

import html
import json
import os
import re
import urllib.request
from collections import Counter
from datetime import date, datetime, timedelta, timezone
from html.parser import HTMLParser
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "cards"
CACHE = ROOT / "data" / "contributions.json"
USERNAME = "16alves02"
ACCENT = "#F07836"
ACCENT_LIGHT = "#FFAA70"
BG = "#10100F"
PANEL = "#191817"
PANEL_LIGHT = "#211F1D"
TEXT = "#F4F0EA"
MUTED = "#A7A098"
STATIC = os.getenv("STATIC", "0") == "1"
OUT.mkdir(exist_ok=True)


class ContributionParser(HTMLParser):
    """Extract contribution cells without depending on attribute order."""

    def __init__(self):
        super().__init__()
        self.days = []
        self.current = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "td" and attrs.get("data-date"):
            self._finish()
            self.current = {
                "date": attrs["data-date"],
                "count": attrs.get("data-count"),
                "level": attrs.get("data-level", "0"),
                "label": attrs.get("aria-label", ""),
                "text": "",
            }
        elif self.current is not None:
            if attrs.get("data-count") is not None:
                self.current["count"] = attrs["data-count"]
            label = attrs.get("aria-label") or attrs.get("title")
            if label:
                self.current["label"] += " " + label

    def handle_data(self, data):
        if self.current is not None:
            self.current["text"] += " " + data

    def handle_endtag(self, tag):
        if tag == "td":
            self._finish()

    def _finish(self):
        if not self.current:
            return
        item = self.current
        raw_count = item["count"]
        if raw_count is None:
            match = re.search(r"([\d,]+)\s+contributions?", item["label"] + " " + item["text"], re.I)
            raw_count = match.group(1).replace(",", "") if match else None
        if raw_count is None and re.search(r"no contributions?", item["label"] + " " + item["text"], re.I):
            raw_count = "0"
        try:
            parsed_date = date.fromisoformat(item["date"])
            count = int(raw_count) if raw_count is not None else None
            level = max(0, min(4, int(item["level"])))
            if count is not None and count >= 0:
                self.days.append({"date": parsed_date.isoformat(), "count": count, "level": level})
        except (TypeError, ValueError):
            pass
        self.current = None


def parse_contribution_html(source: str):
    parser = ContributionParser()
    parser.feed(source)
    unique = {item["date"]: item for item in parser.days}
    return [unique[key] for key in sorted(unique)]


def load_cache():
    if not CACHE.exists():
        return []
    try:
        payload = json.loads(CACHE.read_text(encoding="utf-8"))
        days = payload.get("days", []) if isinstance(payload, dict) else payload
        return sorted(days, key=lambda item: item["date"])
    except (OSError, ValueError, TypeError, KeyError):
        return []


def fetch_contributions():
    url = f"https://github.com/users/{USERNAME}/contributions"
    request = urllib.request.Request(url, headers={"User-Agent": "16alves02-profile-cards/2.0"})
    try:
        with urllib.request.urlopen(request, timeout=25) as response:
            source = response.read().decode("utf-8", "replace")
        days = parse_contribution_html(source)
        if len(days) < 300:
            raise ValueError(f"Expected a full contribution year; parsed only {len(days)} days")
        CACHE.parent.mkdir(parents=True, exist_ok=True)
        CACHE.write_text(
            json.dumps({"updated_at": datetime.now(timezone.utc).isoformat(), "days": days}, indent=2) + "\n",
            encoding="utf-8",
        )
        return days
    except Exception as exc:
        cached = load_cache()
        if cached:
            print(f"Live contribution fetch failed ({exc}); using {len(cached)} cached days.")
            return cached
        print(f"Live contribution fetch failed ({exc}); no cache is available.")
        return []


def write(name: str, body: str):
    (OUT / name).write_text(body, encoding="utf-8")


def svg(content: str, width=960, height=220, label="16alves02 profile card", delay=0):
    motion = "" if STATIC else f"""
    <style>
      .enter{{opacity:0;transform:translateY(13px);animation:rise .72s cubic-bezier(.2,.8,.2,1) {delay}s both}}
      .glow{{animation:pulse 4.8s ease-in-out infinite}}
      .sweep{{animation:sweep 7s ease-in-out infinite}}
      @keyframes rise{{to{{opacity:1;transform:translateY(0)}}}}
      @keyframes pulse{{0%,100%{{opacity:.35}}50%{{opacity:1}}}}
      @keyframes sweep{{0%,65%,100%{{opacity:0}}75%{{opacity:.8}}}}
      @media(prefers-reduced-motion:reduce){{.enter,.glow,.sweep{{animation:none;opacity:1;transform:none}}}}
    </style>"""
    group = f'<g class="enter">{content}</g>' if not STATIC else content
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="{escape(label)}">
    <defs>
      <linearGradient id="accent" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{ACCENT_LIGHT}"/><stop offset="1" stop-color="{ACCENT}"/></linearGradient>
      <linearGradient id="fade" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{ACCENT}" stop-opacity="0"/><stop offset=".5" stop-color="{ACCENT_LIGHT}" stop-opacity=".7"/><stop offset="1" stop-color="{ACCENT}" stop-opacity="0"/></linearGradient>
    </defs>
    <rect width="{width}" height="{height}" rx="20" fill="{BG}"/>
    <rect x=".75" y=".75" width="{width-1.5}" height="{height-1.5}" rx="19.25" fill="none" stroke="#38332F"/>
    {motion}{group}</svg>'''


def tx(x, y, value, size=18, color=TEXT, weight=400, family="Arial, sans-serif", extra=""):
    return f'<text x="{x}" y="{y}" fill="{color}" font-family="{family}" font-size="{size}" font-weight="{weight}" {extra}>{html.escape(str(value))}</text>'


def panel(x, y, width, height, radius=13):
    return f'<rect x="{x}" y="{y}" width="{width}" height="{height}" rx="{radius}" fill="{PANEL}" stroke="#38332F"/>'


def render_hero():
    content = panel(22, 22, 916, 216, 17)
    content += '<path d="M22 92H938" stroke="#38332F"/>'
    content += tx(52, 62, "16ALVES02  /  SOFTWARE DEVELOPER", 13, ACCENT, 700, extra='letter-spacing="2.1"')
    content += tx(52, 139, "Leonardo Alves.", 57, TEXT, 700, "Georgia, serif")
    content += tx(55, 177, "Creative thinking. Engineering mindset. Complete products.", 18, MUTED)
    content += tx(55, 211, "PORTUGAL     WEB  /  BACKEND  /  MOBILE", 11, "#817B74", 700, extra='letter-spacing="1.8"')
    content += '<circle cx="827" cy="132" r="65" fill="none" stroke="#44352D" stroke-width="1"/>'
    content += '<circle cx="827" cy="132" r="49" fill="none" stroke="url(#accent)" stroke-width="1.5" opacity=".75"/>'
    content += '<path d="M827 67V197M762 132H892" stroke="#44352D" stroke-width="1"/>'
    content += tx(827, 142, "LA", 32, ACCENT_LIGHT, 700, "Georgia, serif", 'text-anchor="middle"')
    content += '<rect x="752" y="222" width="150" height="3" rx="1.5" fill="url(#fade)" class="sweep"/>'
    write("hero.svg", svg(content, height=260, label="Leonardo Alves - 16alves02 software developer"))


def render_tiles():
    tiles = [
        ("BUILD", "Software projects", "01", "https://github.com/16alves02?tab=repositories"),
        ("CREATE", "Products & experiments", "02", "https://16alves02-com.vercel.app/"),
        ("LEARN", "Academic work", "03", "https://github.com/13alves05"),
    ]
    for index, (title, subtitle, number, _) in enumerate(tiles):
        content = panel(7, 7, 306, 138, 13)
        content += tx(27, 37, number, 10, "#82776E", 700, extra='letter-spacing="1.5"')
        content += tx(27, 83, title, 27, ACCENT_LIGHT, 700, "Georgia, serif")
        content += tx(28, 111, subtitle, 12, MUTED)
        content += f'<path d="M270 45l13 13-13 13" fill="none" stroke="{ACCENT}" stroke-width="2"/>'
        content += f'<rect x="27" y="126" width="{65+index*13}" height="2" rx="1" fill="url(#accent)"/>'
        write(f"tile-{title.lower()}.svg", svg(content, width=320, height=152, label=f"{title}: {subtitle}", delay=index*.1))


def contribution_stats(days):
    lookup = {item["date"]: int(item.get("count", 0)) for item in days}
    total = sum(lookup.values())
    active = sum(value > 0 for value in lookup.values())
    best_date, best_count = max(lookup.items(), key=lambda pair: pair[1], default=("", 0))
    months = Counter()
    for item in days:
        months[item["date"][:7]] += int(item.get("count", 0))
    streak = 0
    if lookup:
        cursor = min(date.today(), date.fromisoformat(max(lookup)))
        if lookup.get(cursor.isoformat(), 0) == 0:
            cursor -= timedelta(days=1)
        while lookup.get(cursor.isoformat(), 0) > 0:
            streak += 1
            cursor -= timedelta(days=1)
    return total, active, best_count, best_date, streak, months


def render_activity(days):
    if not days:
        content = panel(22, 22, 916, 176)
        content += tx(48, 68, "ACTIVITY / WAITING FOR DATA", 13, ACCENT, 700, extra='letter-spacing="2"')
        content += tx(48, 112, "Contribution data will appear after the first successful refresh.", 17, MUTED)
        write("activity.svg", svg(content, height=220, label="GitHub contribution activity awaiting data"))
        return

    total, active, best, best_date, streak, months = contribution_stats(days)
    content = panel(22, 18, 916, 184)
    content += tx(48, 48, "DEVELOPMENT ACTIVITY", 12, ACCENT, 700, extra='letter-spacing="2"')
    metrics = [
        ("CONTRIBUTIONS", f"{total:,}"),
        ("ACTIVE DAYS", f"{active:,}"),
        ("CURRENT STREAK", f"{streak} days"),
        ("BEST DAY", f"{best:,}"),
    ]
    for index, (label, value) in enumerate(metrics):
        x = 48 + index * 222
        content += tx(x, 86, label, 10, MUTED, 700, extra='letter-spacing="1.1"')
        content += tx(x, 119, value, 25, TEXT, 700, "Georgia, serif")
        if index == 3 and best_date:
            content += tx(x, 137, best_date, 10, "#827B73")
        content += f'<rect x="{x}" y="148" width="176" height="2" rx="1" fill="#38332F"/>'
    selected = sorted(months.items())[-8:]
    max_value = max((value for _, value in selected), default=1) or 1
    for index, (month, value) in enumerate(selected):
        x = 50 + index * 108
        bar_height = max(3, int(30 * value / max_value))
        content += f'<rect x="{x}" y="{190-bar_height}" width="44" height="{bar_height}" rx="4" fill="{ACCENT if index == len(selected)-1 else "#674B3C"}"/>'
        content += tx(x+22, 198, month[2:], 9, MUTED, 400, extra='text-anchor="middle"')
    write("activity.svg", svg(content, height=220, label="GitHub contribution statistics and monthly activity", delay=.15))


def render_contributions(days):
    content = panel(22, 14, 916, 142)
    content += tx(46, 42, "CONTRIBUTION MAP", 12, ACCENT, 700, extra='letter-spacing="2"')
    if not days:
        content += tx(46, 91, "No contribution data available yet.", 15, MUTED)
    else:
        first = date.fromisoformat(days[0]["date"])
        start = first - timedelta(days=(first.weekday() + 1) % 7)
        by_date = {item["date"]: item for item in days}
        columns = 53
        cell = 10
        gap = 4
        graph_width = columns * (cell + gap) - gap
        origin_x = (960 - graph_width) / 2
        origin_y = 61
        month_seen = set()
        for index in range(columns * 7):
            current = start + timedelta(days=index)
            if current > date.today():
                continue
            item = by_date.get(current.isoformat(), {})
            level = max(0, min(4, int(item.get("level", 0))))
            color = ["#292725", "#573627", "#8A482C", "#C96535", ACCENT][level]
            column, row = index // 7, index % 7
            x = origin_x + column * (cell + gap)
            y = origin_y + row * (cell + gap)
            content += f'<rect x="{x:.1f}" y="{y}" width="{cell}" height="{cell}" rx="2.5" fill="{color}"/>'
            if current.day <= 7 and current.strftime("%Y-%m") not in month_seen:
                month_seen.add(current.strftime("%Y-%m"))
                content += tx(x, 55, current.strftime("%b").upper(), 7, "#817B74", 400)
    content += tx(46, 142, "LESS", 8, MUTED)
    for index, color in enumerate(["#292725", "#573627", "#8A482C", "#C96535", ACCENT]):
        content += f'<rect x="{78+index*14}" y="134" width="9" height="9" rx="2" fill="{color}"/>'
    content += tx(156, 142, "MORE", 8, MUTED)
    write("contributions.svg", svg(content, height=170, label="GitHub contribution calendar in orange", delay=.25))


def render_repo_cards():
    repos = [
        ("SABORGEST", "Food-business management system", "PHP  /  MYSQL  /  KOTLIN"),
        ("RUNLATTICE", "Workflow automation product prototype", "NEXT.JS  /  TYPESCRIPT  /  POSTGRESQL"),
        ("MRDR.", "Original crime-deduction game", "REACT  /  TYPESCRIPT  /  CAPACITOR"),
        ("RAW.", "Social card game  /  six languages", "WEB  /  PWA  /  PRODUCT DESIGN"),
        ("HOOP", "Academic basketball-store frontend", "REACT  /  TYPESCRIPT  /  VITE"),
    ]
    for index, (name, description, stack) in enumerate(repos):
        content = panel(12, 10, 936, 132)
        content += tx(42, 48, f"0{index+1}", 10, "#817B74", 700)
        content += tx(42, 84, name, 25, ACCENT_LIGHT, 700, "Georgia, serif")
        content += tx(260, 65, description, 16, TEXT, 500)
        content += tx(260, 94, stack, 10, MUTED, 700, extra='letter-spacing="1.1"')
        content += f'<circle cx="905" cy="48" r="4" fill="{ACCENT}" class="glow"/>'
        content += f'<path d="M260 112H900" stroke="#38332F"/>'
        write(f"project-{index+1}.svg", svg(content, height=152, label=f"{name}: {description}", delay=.35+index*.09))


def main():
    days = fetch_contributions()
    render_hero()
    render_tiles()
    render_activity(days)
    render_contributions(days)
    render_repo_cards()
    print(f"Rendered {len(list(OUT.glob('*.svg')))} SVG cards from {len(days)} contribution days (STATIC={int(STATIC)}).")


if __name__ == "__main__":
    main()
