"""Utils partagés pour les scrapers."""
from __future__ import annotations


def normalize(offer: dict) -> dict:
    now = __import__("datetime").datetime.now().isoformat()
    return {
        "title": (offer.get("title") or "").strip()[:200],
        "url": (offer.get("url") or "").strip(),
        "company": (offer.get("company") or "").strip()[:120],
        "location": (offer.get("location") or "").strip()[:120],
        "description": (offer.get("description") or "").strip()[:5000],
        "salary": offer.get("salary") or "",
        "remote": bool(offer.get("remote")),
        "source": offer.get("source") or "unknown",
        "published_at": offer.get("published_at") or now,
        "scraped_at": now,
        "tags": offer.get("tags") or [],
    }


def dedupe(jobs: list[dict]) -> list[dict]:
    seen = set()
    out = []
    for j in jobs:
        key = (j.get("url") or "").strip() or ((j.get("title") or "").lower(), j.get("source"))
        if key in seen:
            continue
        seen.add(key)
        out.append(j)
    return out


def auto_tag(jobs: list[dict]) -> None:
    rules = {
        "QA": ["qa", "quality assurance"],
        "testeur": ["testeur", "tester"],
        "ISTQB": ["istqb"],
        "Selenium": ["selenium"],
        "Squash": ["squash"],
        "recette": ["recette", "validation"],
        "automatisation": ["automatisation", "automation"],
        "freelance": ["freelance", "mission", "indépendant", "tjm", "taux journalier"],
    }
    for job in jobs:
        text = f"{job.get('title','')} {job.get('description','')}".lower()
        tags = set(job.get("tags") or [])
        for tag, kws in rules.items():
            if any(k in text for k in kws):
                tags.add(tag)
        job["tags"] = list(tags)
