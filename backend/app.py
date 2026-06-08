"""
QA Job Scraper — Flask backend with Supabase storage.
Serves jobs via API and renders frontend dashboard.
"""
import os
import threading
from datetime import datetime, timezone
from flask import Flask, request, jsonify, render_template
from supabase import create_client, Client

app = Flask(__name__)
app.config["JSON_SORT_KEYS"] = False

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")
_LAST_SCRAPE = {"at": None, "inserted": 0}


def get_supabase() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_KEY)


@app.route("/api/jobs", methods=["GET"])
def api_jobs():
    sb = get_supabase()
    res = sb.table("jobs").select("*").order("scraped_at", desc=True).limit(200).execute()
    jobs = res.data or []
    keyword = request.args.get("keyword", "").strip().lower()
    if keyword:
        jobs = [j for j in jobs if keyword in f"{j.get('title','')} {j.get('description','')}".lower()]
    return jsonify({"count": len(jobs), "jobs": jobs})


@app.route("/api/stats", methods=["GET"])
def api_stats():
    sb = get_supabase()
    count_res = sb.table("jobs").select("id", count="exact").execute()
    total = count_res.count if hasattr(count_res, "count") else 0
    latest = sb.table("jobs").select("scraped_at").order("scraped_at", desc=True).limit(1).execute()
    last = latest.data[0]["scraped_at"] if latest.data else None
    return jsonify({"total": total, "last_fetch": last})


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "last_scrape": _LAST_SCRAPE})


@app.route("/", methods=["GET"])
def index():
    return jsonify({"status": "running", "docs": "/api/jobs", "dashboard": "/dashboard"})


@app.route("/dashboard", methods=["GET"])
def dashboard():
    try:
        path = os.path.join(os.path.dirname(__file__), "..", "frontend", "index.html")
        with open(path, "r", encoding="utf-8") as fh:
            return fh.read()
    except FileNotFoundError:
        return jsonify({"status": "running", "docs": "/api/jobs"})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port, debug=True)
