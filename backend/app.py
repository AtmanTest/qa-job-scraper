"""
QA Job Scraper - Flask backend with Supabase storage.
Serves jobs via API and renders frontend dashboard.
"""
import os
from datetime import datetime, timezone
from flask import Flask, request, jsonify, render_template
from supabase import create_client, Client
from scraper import scrape_qa_jobs

app = Flask(__name__)
app.config["JSON_SORT_KEYS"] = False

# ── Config ──────────────────────────────────────────────────────────────────
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")  # service_role

_FRONTEND_INDEX = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "frontend", "index.html"
)


def get_supabase() -> Client:
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise RuntimeError("SUPABASE_URL / SUPABASE_KEY manquants")
    return create_client(SUPABASE_URL, SUPABASE_KEY)


# ── Routes ───────────────────────────────────────────────────────────────────
@app.route("/api/jobs", methods=["GET"])
def api_jobs():
    """Return all QA jobs, optionally filtered by keyword."""
    try:
        sb = get_supabase()
    except RuntimeError as exc:
        return jsonify({"error": str(exc), "jobs": []}), 500

    query = sb.table("jobs").select("*").order("fetched_at", desc=True)

    keyword = request.args.get("keyword", "").strip().lower()
    if keyword:
        query = query.or_(
            f"title.ilike.%{keyword}%,company.ilike.%{keyword}%,description.ilike.%{keyword}%"
        )

    limit = request.args.get("limit", 200, type=int)
    query = query.limit(min(limit, 500))

    res = query.execute()
    jobs = res.data or []
    return jsonify({"count": len(jobs), "jobs": jobs})


@app.route("/api/stats", methods=["GET"])
def api_stats():
    """Simple stats: total jobs, last fetch time, top sources."""
    try:
        sb = get_supabase()
    except RuntimeError as exc:
        return jsonify({"error": str(exc)}), 500

    count_res = sb.table("jobs").select("id", count="exact").execute()
    total = count_res.count if hasattr(count_res, "count") else 0

    latest_res = (
        sb.table("jobs")
        .select("fetched_at")
        .order("fetched_at", desc=True)
        .limit(1)
        .execute()
    )
    latest = latest_res.data[0]["fetched_at"] if latest_res.data else None

    sources_res = (
        sb.table("jobs")
        .select("source")
        .execute()
    )
    sources = {}
    for row in (sources_res.data or []):
        src = row.get("source", "unknown")
        sources[src] = sources.get(src, 0) + 1

    return jsonify({"total": total, "last_fetch": latest, "sources": sources})


@app.route("/api/refresh", methods=["POST"])
def api_refresh():
    """Trigger a fresh scrape (by GitHub Actions or cron)."""
    token = request.headers.get("X-CRON-TOKEN", "")
    expected = os.environ.get("CRON_TOKEN", "")
    if expected and token != expected:
        return jsonify({"error": "unauthorized"}), 401

    try:
        jobs = scrape_qa_jobs()
        save_jobs(jobs)
        return jsonify({"inserted": len(jobs), "at": datetime.now(timezone.utc).isoformat()})
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


@app.route("/", methods=["GET"])
def index():
    try:
        with open(_FRONTEND_INDEX, "r", encoding="utf-8") as fh:
            return fh.read()
    except FileNotFoundError:
        return jsonify({"status": "running", "docs": "/api/jobs"}), 200


# ── Helpers ──────────────────────────────────────────────────────────────────
def save_jobs(jobs: list[dict]):
    """Upsert jobs into Supabase `jobs` table by unique URL."""
    if not jobs:
        return
    sb = get_supabase()
    rows = []
    for j in jobs:
        rows.append(
            {
                "title": j.get("title", ""),
                "company": j.get("company", ""),
                "location": j.get("location", ""),
                "url": j.get("url", ""),
                "source": j.get("source", ""),
                "description": j.get("description", ""),
                "fetched_at": datetime.now(timezone.utc).isoformat(),
            }
        )
    # Upsert by url (unique constraint on jobs.url)
    sb.table("jobs").upsert(rows, on_conflict="url").execute()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port, debug=True)
