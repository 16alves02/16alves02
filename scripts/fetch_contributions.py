#!/usr/bin/env python3
import json, os, urllib.request
from datetime import datetime, timedelta, timezone

USERNAME = "16alves02"
OUTPUT = "data/contributions.json"

def main():
    token = os.environ["GITHUB_TOKEN"]
    today = datetime.now(timezone.utc).date()
    start = today - timedelta(days=365)
    query = f'''{{ user(login: "{USERNAME}") {{ contributionsCollection(from: "{start}T00:00:00Z", to: "{today}T23:59:59Z") {{ contributionCalendar {{ totalContributions weeks {{ contributionDays {{ date contributionCount }} }} }} }} }} }}'''
    request = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": query}).encode(),
        headers={"Authorization": f"bearer {token}", "Content-Type": "application/json", "User-Agent": "16alves02-profile"},
        method="POST",
    )
    with urllib.request.urlopen(request) as response:
        payload = json.load(response)
    if "errors" in payload:
        raise RuntimeError(payload["errors"])
    calendar = payload["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    days = [day for week in calendar["weeks"] for day in week["contributionDays"]]
    os.makedirs("data", exist_ok=True)
    with open(OUTPUT, "w", encoding="utf-8") as file:
        json.dump({"generated_at": datetime.now(timezone.utc).isoformat(), "user": USERNAME, "total_contributions": calendar["totalContributions"], "contributions": days}, file, indent=2)
        file.write("\n")

if __name__ == "__main__":
    main()
