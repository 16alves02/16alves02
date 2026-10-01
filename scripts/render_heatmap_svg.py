#!/usr/bin/env python3
import json
INPUT = "data/contributions.json"
OUTPUT = "contrib-heatmap.svg"

def level(count):
    return 0 if count == 0 else 1 if count == 1 else 2 if count <= 3 else 3 if count <= 6 else 4

def main():
    with open(INPUT, encoding="utf-8") as file:
        data = json.load(file)
    days = data.get("contributions", [])
    total = data.get("total_contributions", 0)
    cells = []
    for index, day in enumerate(days):
        x = 28 + (index // 7) * 14
        y = 72 + (index % 7) * 12
        cells.append(f'<rect x="{x}" y="{y}" width="10" height="10" rx="2" data-level="{level(day["contributionCount"])}"><title>{day["date"]}: {day["contributionCount"]} contributions</title></rect>')
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 760 180">
<style>.bg{{fill:#0d1117}}.border{{fill:none;stroke:#30363d}}.text{{fill:#8b949e;font:14px monospace}}.strong{{fill:#f0f6fc;font:16px monospace}}rect[data-level="0"]{{fill:#161b22}}rect[data-level="1"]{{fill:#0e4429}}rect[data-level="2"]{{fill:#006d32}}rect[data-level="3"]{{fill:#26a641}}rect[data-level="4"]{{fill:#39d353}}</style>
<rect class="bg" width="760" height="180" rx="16"/><rect class="border" x="1" y="1" width="758" height="178" rx="15"/>
<text class="text" x="28" y="30">github@16alves02 ~ $ contributions --year</text>
<text class="strong" x="28" y="53">{total} contributions</text>
{"".join(cells)}
</svg>'''
    with open(OUTPUT, "w", encoding="utf-8") as file:
        file.write(svg)

if __name__ == "__main__":
    main()
