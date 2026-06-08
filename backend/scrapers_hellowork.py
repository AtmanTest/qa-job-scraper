import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone


def scrape(locations: list[str] | None = None, keywords: list[str] | None = None) -> list[dict]:
    keywords = keywords or ["QA", "test", "qualité", "automatisation", "SDET"]
    locations = locations or ["France", "Paris", "Lyon", "Toulouse", "Bordeaux", "Nantes", "Lille", "Remote"]
    jobs: list[dict] = []
    seen: set[str] = set()
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        )
    }

    for keyword in keywords:
        for location in locations:
            query = f"site:hellowork.com {keyword} {location}"
            try:
                res = requests.get(
                    "https://html.duckduckgo.com/html/",
                    params={"q": query},
                    headers=headers,
                    timeout=20,
                    allow_redirects=False,
                )
                res.raise_for_status()
            except Exception:
                continue

            soup = BeautifulSoup(res.text, "lxml")
            for result in soup.select(".result"):
                link = result.select_one("a.result__a")
                snippet = result.select_one(".result__snippet")
                if not link:
                    continue
                title = link.get_text(strip=True) or ""
                href = link.get("href", "") or ""
                description = snippet.get_text(strip=True) if snippet else ""
                if not title or not href:
                    continue
                signature = f"{title.lower()}|{href.lower()}"
                if signature in seen:
                    continue
                seen.add(signature)
                jobs.append(
                    {
                        "title": title[:220],
                        "company": _guess_company(title)[:120],
                        "location": location[:120],
                        "url": href,
                        "source": "HelloWork",
                        "description": description[:1500],
                        "fetched_at": datetime.now(timezone.utc).isoformat(),
                    }
                )
    return jobs[:120]


def _guess_company(title: str) -> str:
    if " - " in title:
        return title.split(" - ")[0].strip()
    return title
