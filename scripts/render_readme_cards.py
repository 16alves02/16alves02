#!/usr/bin/env python3
"""Render the 16alves02 GitHub profile cards from public contribution data.

Run with STATIC=1 to render the final frame without animation.
The script uses only the Python standard library.
"""
from __future__ import annotations

import html
import json
import os
import re
import urllib.request
from collections import Counter
from datetime import date, datetime, timedelta
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "cards"
USERNAME = "16alves02"
ACCENT = "#F07836"
BG = "#111111"
PANEL = "#191919"
TEXT = "#F3F0EB"
MUTED = "#A6A19B"
STATIC = os.getenv("STATIC", "0") == "1"
OUT.mkdir(exist_ok=True)


def fetch_contributions():
    url = f"https://github.com/users/{USERNAME}/contributions"
    request = urllib.request.Request(url, headers={"User-Agent": "16alves02-readme-cards/1.0"})
    try:
        with urllib.request.urlopen(request, timeout=25) as response:
            source = response.read().decode("utf-8", "replace")
        days = []
        for match in re.finditer(r'<td[^>]*data-date="(\d{4}-\d{2}-\d{2})"[^>]*data-count="(\d+)"[^>]*data-level="(\d+)"', source):
            days.append({"date": match.group(1), "count": int(match.group(2)), "level": int(match.group(3))})
        if not days:
            # Attribute order varies; parse each contribution cell independently.
            for cell in re.findall(r'<td\\b[^>]*>', source):
                d = re.search(r'data-date="(\d{4}-\d{2}-\d{2})"', cell)
                c = re.search(r'data-count="(\d+)"', cell)
                l = re.search(r'data-level="(\d+)"', cell)
                if d and c:
                    days.append({"date": d.group(1), "count": int(c.group(1)), "level": int(l.group(1)) if l else 0})
        if not days:
            raise ValueError("GitHub returned no parseable contribution cells")
        return days
    except Exception as exc:
        cache = ROOT / "data" / "contributions.json"
        if cache.exists():
            print(f"Warning: live contribution fetch failed ({exc}); using cached data.")
            return json.loads(cache.read_text(encoding="utf-8")).get("days", [])
        print(f"Warning: live contribution fetch failed ({exc}); rendering an empty activity card.")
        return []


def write(name: str, body: str):
    (OUT / name).write_text(body, encoding="utf-8")


def svg(content: str, width=960, height=260, label="16alves02 profile card", delay=0):
    animation = "" if STATIC else """
    <style>
      .enter{opacity:0;transform:translateY(14px);animation:rise .75s cubic-bezier(.2,.8,.2,1) forwards}
      .shine{animation:glow 5s ease-in-out infinite}
      @keyframes rise{to{opacity:1;transform:translateY(0)}}
      @keyframes glow{0%,75%,100%{opacity:.18}85%{opacity:.8}}
      @media(prefers-reduced-motion:reduce){.enter{animation:none;opacity:1;transform:none}.shine{animation:none}}
    </style>"""
    group = f'<g class="enter" style="animation-delay:{delay}s">{content}</g>' if not STATIC else content
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="{escape(label)}">
    <rect width="{width}" height="{height}" rx="22" fill="{BG}"/>
    <rect x="1" y="1" width="{width-2}" height="{height-2}" rx="21" fill="none" stroke="#34312E"/>
    {animation}{group}</svg>'''


def text(x, y, value, size=20, color=TEXT, weight=400, family="Arial, sans-serif", extra=""):
    return f'<text x="{x}" y="{y}" fill="{color}" font-family="{family}" font-size="{size}" font-weight="{weight}" {extra}>{html.escape(str(value))}</text>'


def rounded_rect(x, y, w, h, fill=PANEL, radius=12, stroke="none"):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{radius}" fill="{fill}" stroke="{stroke}"/>'


def render_hero():
    content = rounded_rect(28, 28, 904, 204, PANEL, 16, "#34312E")
    content += text(58, 76, "16ALVES02  /  SOFTWARE DEVELOPER", 14, ACCENT, 700, extra='letter-spacing="2"')
    content += text(58, 137, "Leonardo Alves.", 54, TEXT, 700, "Georgia, serif")
    content += text(60, 174, "Creative thinking. Engineering mindset. Complete products.", 19, MUTED)
    content += text(60, 207, "PORTUGAL  ·  BUILDING WEB, BACKEND & MOBILE SOFTWARE", 12, "#817B74", 700, extra='letter-spacing="1.4"')
    content += f'<path d="M790 75h90M835 30v90" stroke="{ACCENT}" stroke-width="1" opacity=".45"/>'
    content += f'<circle cx="835" cy="75" r="42" fill="none" stroke="{ACCENT}" opacity=".55"/>'
    content += text(835, 83, "LA", 26, ACCENT, 700, "Georgia, serif", 'text-anchor="middle"')
    write("hero.svg", svg(content, height=260, label="Leonardo Alves profile hero"))


def render_tiles():
    tiles = [
        ("BUILD", "Software projects", "https://github.com/16alves02?tab=repositories"),
        ("CREATE", "Products & experiments", "https://16alves02-com.vercel.app/"),
        ("LEARN", "Academic work", "https://github.com/13alves05"),
    ]
    for index, (title, subtitle, _) in enumerate(tiles):
        x = 24 + index * 312
        content = rounded_rect(x, 18, 296, 116, PANEL, 14, "#34312E")
        content += text(x+22, 62, title, 27, ACCENT, 700, "Georgia, serif")
        content += text(x+22, 94, subtitle, 14, MUTED)
        content += f'<path d="M{x+250} 39l12 12-12 12" fill="none" stroke="{ACCENT}" stroke-width="2"/>'
        write(f"tile-{title.lower()}.svg", svg(content, width=960, height=152, label=f"{title}: {subtitle}", delay=index*.12))


def contribution_stats(days):
    counts = [int(d.get("count", 0)) for d in days]
    total = sum(counts)
    active = sum(c > 0 for c in counts)
    busiest = max(counts, default=0)
    months = Counter()
    for item in days:
        months[item["date"][:7]] += int(item.get("count", 0))
    latest = date.today()
    streak = 0
    lookup = {d["date"]: int(d.get("count", 0)) for d in days}
    cursor = latest
    if lookup.get(cursor.isoformat(), 0) == 0:
        cursor -= timedelta(days=1)
    while lookup.get(cursor.isoformat(), 0) > 0:
        streak += 1
        cursor -= timedelta(days=1)
    return total, active, busiest, streak, months


def render_activity(days):
    total, active, busiest, streak, months = contribution_stats(days)
    content = text(42, 48, "CONTRIBUTION ACTIVITY", 13, ACCENT, 700, extra='letter-spacing="2"')
    metrics = [("CONTRIBUTIONS", total), ("ACTIVE DAYS", active), ("CURRENT STREAK", f"{streak} days"), ("BEST DAY", busiest)]
    for i, (label, value) in enumerate(metrics):
        x = 42 + i*222
        content += text(x, 91, label, 11, MUTED, 700)
        content += text(x, 128, value, 27, TEXT, 700, "Georgia, serif")
    selected = sorted(months.items())[-8:]
    max_value = max((v for _, v in selected), default=1) or 1
    for i, (month, value) in enumerate(selected):
        x = 48 + i*108
        bar_h = max(4, int(66*value/max_value))
        content += f'<rect x="{x}" y="{222-bar_h}" width="48" height="{bar_h}" rx="5" fill="{ACCENT if i == len(selected)-1 else "#625047"}"/>'
        content += text(x+24, 242, month[5:], 11, MUTED, 400, extra='text-anchor="middle"')
    content += text(42, 166, "LAST 8 MONTHS", 10, "#817B74", 700, extra='letter-spacing="1.5"')
    write("activity.svg", svg(content, height=270, label="GitHub contribution totals and monthly activity", delay=.25))


def render_contributions(days):
    content = text(34, 43, "CONTRIBUTION GRAPH", 13, ACCENT, 700, extra='letter-spacing="2"')
    by_date = {d["date"]: d for d in days}
    if days:
        start = date.fromisoformat(days[0]["date"])
        start -= timedelta(days=(start.weekday()+1) % 7)
        for index in range(371):
            current = start + timedelta(days=index)
            item = by_date.get(current.isoformat(), {})
            level = int(item.get("level", 0))
            count = int(item.get("count", 0))
            color = ["#292725", "#623B2A", "#99502F", "#C96535", ACCENT][min(level, 4)]
            col, row = index // 7, index % 7
            x, y = 34 + col*12, 72 + row*12
            content += f'<rect x="{x}" y="{y}" width="8" height="8" rx="2" fill="{color}" data-count="{count}"/>'
    else:
        content += text(34, 110, "Contribution data will appear after the first successful refresh.", 16, MUTED)
    write("contributions.svg", svg(content, height=174, label="GitHub contribution calendar in orange", delay=.35))


def render_repo_cards():
    repos = [
        ("SABORGEST", "Food-business management system", "PHP · MySQL · Kotlin", "https://github.com/16alves02/SaborGest"),
        ("RUNLATTICE", "Workflow automation product prototype", "Next.js · TypeScript · PostgreSQL", "https://github.com/16alves02/RunLattice"),
        ("MRDR.", "Original crime-deduction game", "React · TypeScript · Capacitor", "https://github.com/16alves02/mrdr"),
        ("RAW.", "Social card game · 6 languages", "Web · PWA · Product design", "https://raw-app-bice.vercel.app/"),
        ("HOOP", "Academic basketball-store frontend", "React · TypeScript · Vite", "https://github.com/16alves02/hoop"),
    ]
    for index, (name, description, stack, _) in enumerate(repos):
        content = rounded_rect(24, 18, 912, 116, PANEL, 14, "#34312E")
        content += text(48, 57, name, 24, ACCENT, 700, "Georgia, serif")
        content += text(48, 88, description, 15, TEXT)
        content += text(48, 113, stack, 12, MUTED)
        content += f'<circle cx="888" cy="52" r="5" fill="{ACCENT}" class="shine"/>'
        write(f"project-{index+1}.svg", svg(content, height=152, label=f"{name}: {description}", delay=.5+index*.12))


def main():
    days = fetch_contributions()
    render_hero()
    render_tiles()
    render_activity(days)
    render_contributions(days)
    render_repo_cards()
    print(f"Rendered profile cards to {OUT} ({len(days)} contribution days; STATIC={int(STATIC)}).")


if __name__ == "__main__":
    main()
