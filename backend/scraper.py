"""
QA Job Scraper.
Sources: LinkedIn (via web search), Indeed, Welcome to the Jungle.
"""

from __future__ import annotations
import re
from urllib.parse import quote_plus

KEYWORDS = [
    "QA ingénieur test logiciel",
    "testeur logiciel",
    "ingénieur QA",
    "QA engineer",
    "software tester",
    "automation test engineer",
    "test automation engineer",
    "contrôleur qualité logiciel",
]

KEYWORDS_EN = [
    "QA engineer",
    "software tester",
    "test automation engineer",
    "quality assurance engineer",
    "QA analyst",
    "SDET",
    "test engineer",
]


def _build_queries() -> list[str]:
    queries = list(KEYWORDS)
    for kw in KEYWORDS_EN:
        if kw not in queries:
            queries.append(kw)
    return queries


def scrape_qa_jobs() -> list[dict]:
    """Return QA jobs. Uses web search to discover listings."""
    from hermes_tools import web_search  # type: ignore

    jobs: list[dict] = []
    seen: set[str] = set()

    for query in _build_queries():
        try:
            res = web_search(f"{query} site:linkedin.com/jobs OR site:indeed.com OR site:wttj.co", limit=8)
        except Exception:
            continue

        for item in res.get("data", {}).get("web", []):
            url = item.get("url", "")
            title = item.get("title", "").strip()
            desc = item.get("description", "").strip()

            if not url or not title:
                continue

            # Filter: must contain QA/test keywords
            combined = f"{title} {desc}".lower()
            if not any(tok in combined for tok in [
                "qa", "test", "testeur", "ingénieur test", "automation",
                "quality assurance", "sdet", "contrôleur qualité"
            ]):
                continue

            if url in seen:
                continue
            seen.add(url)

            source = "linkedin" if "linkedin.com/jobs" in url else (
                "indeed" if "indeed.com" in url else (
                    "wttj" if "wttj.co" in url else "other"
                )
            )

            # Extract company from title (many LinkedIn titles are "TITLE at COMPANY")
            company = ""
            m = re.search(r"at\s+([A-ZÀ-ÿ][\w &\-]+)", title, re.I)
            if m:
                company = m.group(1).strip()
            else:
                # Try first sentence of description
                first_sentence = desc.split(".")[0] if desc else ""
                company = first_sentence[:60]

            # Location: try to find in title or description
            location = ""
            loc_match = re.search(
                r"([\w\s,]+(?:France|Suisse|Luxembourg|Maroc|Canada|Belgique|UAE|Dubai|Paris|Lyon|Toulouse|Bordeaux|Nantes|Lille))",
                title + " " + desc, re.I
            )
            if loc_match:
                location = loc_match.group(1).strip()

            jobs.append({
                "title": title[:200],
                "company": company[:120],
                "location": location[:120],
                "url": url,
                "source": source,
                "description": desc[:1000],
            })

    # Deduplicate by similar title+company
    deduped: list[dict] = []
    sigs: set[str] = set()
    for j in jobs:
        sig = f"{j['title'].lower()}|{j['company'].lower()}"
        if sig not in sigs:
            sigs.add(sig)
            deduped.append(j)
    return deduped


if __name__ == "__main__":
    import json
    jobs = scrape_qa_jobs()
    print(json.dumps({"count": len(jobs), "jobs": jobs[:5]}, indent=2, ensure_ascii=False))
