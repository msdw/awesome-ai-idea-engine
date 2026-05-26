#!/usr/bin/env python3
"""Weekly script: discover new source candidates and update sources.yaml.

This script searches for new useful sources (GitHub awesome lists, HN resource
threads, AI tool directories) and proposes them as candidates in sources.yaml.
The CI creates a PR so the maintainer can review before merging.
"""
import sys
import json
import argparse
import datetime
import time
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import URLError

try:
    import yaml
except ImportError:
    print("PyYAML required. Run: pip install pyyaml", file=sys.stderr)
    sys.exit(1)

ROOT = Path(__file__).parent.parent
DATA = ROOT / "data"
SOURCES_FILE = DATA / "sources.yaml"

GITHUB_API = "https://api.github.com"
HN_SEARCH_API = "https://hn.algolia.com/api/v1"

# Queries to find new awesome lists / resource collections relevant to AI ideas
GITHUB_SOURCE_QUERIES = [
    "awesome ai tools list",
    "awesome llm resources",
    "awesome ai startup",
    "awesome ai applications",
    "ai ideas list curated",
]

HN_SOURCE_QUERIES = [
    "best AI resources list",
    "AI tools directory curated",
    "awesome list AI startup",
]


def fetch_json(url: str) -> dict | list | None:
    headers = {"User-Agent": "awesome-ai-idea-engine/1.0 source-updater"}
    try:
        req = Request(url, headers=headers)
        with urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"  Fetch error {url}: {e}", file=sys.stderr)
        return None


def load_existing_sources() -> dict:
    if SOURCES_FILE.exists():
        with open(SOURCES_FILE, encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    return {"sources": {}}


def existing_urls(data: dict) -> set:
    """Return set of all URLs and search_queries already in sources.yaml."""
    known = set()
    for src in data.get("sources", {}).values():
        if "url" in src:
            known.add(src["url"].rstrip("/").lower())
        if "search_query" in src:
            known.add(src["search_query"].lower())
    return known


def search_github_for_sources(dry_run: bool) -> list[tuple[str, dict]]:
    """Search GitHub for awesome lists that could be added as sources."""
    print("\n[GitHub] Searching for new source candidates...")
    candidates = []
    known = existing_urls(load_existing_sources())

    for query in GITHUB_SOURCE_QUERIES:
        q = query.replace(" ", "+")
        url = f"{GITHUB_API}/search/repositories?q={q}&sort=stars&per_page=5"
        data = fetch_json(url)
        if not data:
            time.sleep(1)
            continue

        for repo in data.get("items", []):
            stars = repo.get("stargazers_count", 0)
            if stars < 100:
                continue
            html_url = repo.get("html_url", "").rstrip("/").lower()
            if html_url in known:
                continue

            slug = repo.get("full_name", "").replace("/", "_").replace("-", "_").lower()
            name = f"github_{slug}"[:64]
            entry = {
                "type": "github",
                "description": (repo.get("description") or repo.get("name", ""))[:120],
                "url": repo.get("html_url", ""),
                "search_query": query,
                "frequency": "weekly",
                "status": "candidate",
                "stars": stars,
                "added_at": datetime.date.today().isoformat(),
            }
            candidates.append((name, entry))
            print(f"  + {repo.get('full_name')} ({stars}⭐) — {entry['description'][:60]}")
            known.add(html_url)

        time.sleep(0.8)

    return candidates


def search_hn_for_sources(dry_run: bool) -> list[tuple[str, dict]]:
    """Search HN for threads that list AI resources / curated sources."""
    print("\n[HN] Searching for new source candidates...")
    candidates = []
    known = existing_urls(load_existing_sources())
    from_ts = int((datetime.datetime.utcnow() - datetime.timedelta(days=30)).timestamp())

    for query in HN_SOURCE_QUERIES:
        q = query.replace(" ", "+")
        url = (
            f"{HN_SEARCH_API}/search?query={q}"
            f"&numericFilters=created_at_i>{from_ts}&hitsPerPage=5"
        )
        data = fetch_json(url)
        if not data:
            time.sleep(0.5)
            continue

        for hit in data.get("hits", []):
            points = hit.get("points", 0)
            if points < 30:
                continue
            hn_url = hit.get("url") or f"https://news.ycombinator.com/item?id={hit.get('objectID')}"
            if hn_url.rstrip("/").lower() in known:
                continue

            obj_id = hit.get("objectID", "")
            name = f"hn_{obj_id}"
            entry = {
                "type": "hn",
                "description": hit.get("title", "")[:120],
                "url": hn_url,
                "search_query": query,
                "frequency": "weekly",
                "status": "candidate",
                "points": points,
                "added_at": datetime.date.today().isoformat(),
            }
            candidates.append((name, entry))
            print(f"  + HN: {hit.get('title', '')[:70]} ({points} pts)")
            known.add(hn_url.rstrip("/").lower())

        time.sleep(0.5)

    return candidates


def save_candidates(candidates: list[tuple[str, dict]], dry_run: bool) -> int:
    if not candidates:
        print("\nNo new source candidates found.")
        return 0

    print(f"\n{len(candidates)} new source candidates found.")

    if dry_run:
        print("DRY RUN — not writing to sources.yaml")
        for name, entry in candidates:
            print(f"  [{name}] {entry.get('description', '')[:60]}")
        return len(candidates)

    data = load_existing_sources()
    existing_keys = set(data.get("sources", {}).keys())
    added = 0

    for name, entry in candidates:
        # Make key unique if collision
        key = name
        i = 2
        while key in existing_keys:
            key = f"{name}_{i}"
            i += 1
        data.setdefault("sources", {})[key] = entry
        existing_keys.add(key)
        added += 1

    with open(SOURCES_FILE, "w", encoding="utf-8") as f:
        yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

    print(f"Saved {added} new candidates to {SOURCES_FILE.name}")

    # Append to updates log
    log_path = DATA / "updates_log.yaml"
    log_data: dict = {}
    if log_path.exists():
        with open(log_path, encoding="utf-8") as f:
            log_data = yaml.safe_load(f) or {}
    log_data.setdefault("updates", []).append({
        "date": datetime.datetime.utcnow().isoformat(),
        "action": "sources_update",
        "new_source_candidates": added,
    })
    with open(log_path, "w", encoding="utf-8") as f:
        yaml.dump(log_data, f, allow_unicode=True, default_flow_style=False)

    return added


def main() -> None:
    parser = argparse.ArgumentParser(description="Discover new source candidates for idea discovery")
    parser.add_argument("--dry-run", action="store_true", help="Print candidates without saving")
    args = parser.parse_args()

    print("=== Source discovery run (Awesome AI Idea Engine) ===")
    print(f"Date: {datetime.date.today().isoformat()}")

    candidates: list[tuple[str, dict]] = []
    candidates.extend(search_github_for_sources(args.dry_run))
    candidates.extend(search_hn_for_sources(args.dry_run))

    added = save_candidates(candidates, args.dry_run)

    print(f"\nSource update complete. {added} candidates added to sources.yaml.")
    if added > 0 and not args.dry_run:
        print("Review candidates in data/sources.yaml — change status to 'active' to enable them.")


if __name__ == "__main__":
    main()
