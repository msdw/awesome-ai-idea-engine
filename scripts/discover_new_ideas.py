#!/usr/bin/env python3
"""Discover new AI idea candidates from public sources."""
import sys
import json
import argparse
import datetime
import re
import time
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import URLError

ROOT = Path(__file__).parent.parent
DATA = ROOT / "data"

GITHUB_API = "https://api.github.com"
HN_API = "https://hacker-news.firebaseio.com/v0"
HN_SEARCH_API = "https://hn.algolia.com/api/v1"

AI_KEYWORDS = [
    "llm", "gpt", "claude", "gemini", "openai", "anthropic",
    "langchain", "llamaindex", "rag", "vector", "embedding",
    "ai agent", "ai automation", "ai saas", "ai tool"
]


def fetch_json(url: str, token: str = None) -> dict | list | None:
    headers = {"User-Agent": "awesome-ai-idea-engine/1.0"}
    if token:
        headers["Authorization"] = f"token {token}"
    try:
        req = Request(url, headers=headers)
        with urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"  Fetch error {url}: {e}", file=sys.stderr)
        return None


def discover_from_github(mode: str, dry_run: bool) -> list[dict]:
    """Discover AI repos from GitHub trending."""
    print("\n[GitHub] Searching trending AI repositories...")
    candidates = []

    # GitHub trending (scrape is unreliable — use search API instead)
    query = "llm OR rag OR 'ai agent' OR 'ai automation' language:python"
    since_days = 7 if mode == "weekly" else 1
    since = (datetime.datetime.utcnow() - datetime.timedelta(days=since_days)).strftime("%Y-%m-%d")
    url = f"{GITHUB_API}/search/repositories?q={query.replace(' ', '+')}+created:>{since}&sort=stars&per_page=20"

    data = fetch_json(url)
    if not data:
        return candidates

    for repo in data.get("items", []):
        name = repo.get("full_name", "")
        desc = repo.get("description") or ""
        stars = repo.get("stargazers_count", 0)
        topics = repo.get("topics", [])
        url_html = repo.get("html_url", "")

        if stars < 50:
            continue

        candidate = {
            "id": f"candidate_{name.replace('/', '_').lower()}",
            "title": f"{repo.get('name', '')} — {desc[:80]}",
            "summary": desc or "No description available",
            "category": "ai_saas",
            "target_users": ["developer"],
            "pain_points": ["See repository description"],
            "ai_solution": ["See repository description"],
            "ai_patterns": ["generation"],
            "possible_business_models": ["subscription_saas"],
            "technical_stack": ["openai_api", "python"],
            "validation_methods": ["forum_research"],
            "validation_steps": ["Review repository README and issues"],
            "difficulty": "medium",
            "time_to_mvp": "unknown",
            "risk_level": "medium",
            "scoring": {
                "pain_intensity": 5, "willingness_to_pay": 5, "ai_fit": 7,
                "buildability": 6, "market_signal": stars // 100,
                "differentiation_potential": 5, "monetization_potential": 5,
                "compliance_risk": 3
            },
            "tags": topics[:5] or ["automation"],
            "source": url_html,
            "status": "candidate",
            "_discovery_meta": {
                "source": "github",
                "stars": stars,
                "discovered_at": datetime.datetime.utcnow().isoformat()
            }
        }
        candidates.append(candidate)
        print(f"  Found: {name} ({stars} stars)")
        time.sleep(0.3)

    return candidates


def discover_from_hn(mode: str, dry_run: bool) -> list[dict]:
    """Discover AI ideas from Hacker News Show HN posts."""
    print("\n[HN] Searching Show HN posts...")
    candidates = []

    days_back = 7 if mode == "weekly" else 1
    from_ts = int((datetime.datetime.utcnow() - datetime.timedelta(days=days_back)).timestamp())

    for kw in ["AI tool", "LLM", "GPT", "RAG assistant"]:
        url = f"{HN_SEARCH_API}/search?query=Show+HN+{kw.replace(' ', '+')}&tags=show_hn&numericFilters=created_at_i>{from_ts}&hitsPerPage=10"
        data = fetch_json(url)
        if not data:
            continue

        for hit in data.get("hits", []):
            title = hit.get("title", "")
            story_url = hit.get("url") or f"https://news.ycombinator.com/item?id={hit.get('objectID')}"
            points = hit.get("points", 0)

            if points < 10:
                continue

            candidate = {
                "id": f"candidate_hn_{hit.get('objectID', '')}",
                "title": title,
                "summary": f"HN Show HN: {title}. Source: {story_url}",
                "category": "ai_tools_devs",
                "target_users": ["developer"],
                "pain_points": ["See HN post"],
                "ai_solution": ["See HN post"],
                "ai_patterns": ["generation"],
                "possible_business_models": ["subscription_saas"],
                "technical_stack": ["openai_api"],
                "validation_methods": ["forum_research"],
                "validation_steps": ["Review HN comments for user feedback"],
                "difficulty": "medium",
                "time_to_mvp": "unknown",
                "risk_level": "low",
                "scoring": {
                    "pain_intensity": 5, "willingness_to_pay": 5, "ai_fit": 7,
                    "buildability": 6, "market_signal": min(10, points // 20),
                    "differentiation_potential": 5, "monetization_potential": 5,
                    "compliance_risk": 2
                },
                "tags": ["automation"],
                "source": story_url,
                "status": "candidate",
                "_discovery_meta": {
                    "source": "hacker_news",
                    "points": points,
                    "discovered_at": datetime.datetime.utcnow().isoformat()
                }
            }
            candidates.append(candidate)
            print(f"  Found: {title[:80]} ({points} pts)")
        time.sleep(0.5)

    return candidates


def save_candidates(candidates: list[dict], dry_run: bool) -> None:
    if not candidates:
        print("\nNo new candidates found")
        return

    print(f"\nFound {len(candidates)} candidates")

    if dry_run:
        print("DRY RUN — not writing to files")
        for c in candidates:
            print(f"  - {c['title'][:80]}")
        return

    # Append to ideas.yaml as candidates
    import yaml
    ideas_path = DATA / "ideas.yaml"
    data = {}
    if ideas_path.exists():
        with open(ideas_path, encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

    existing_ids = {i["id"] for i in data.get("ideas", [])}
    new_ideas = []
    for c in candidates:
        if c["id"] not in existing_ids:
            new_ideas.append(c)

    if not new_ideas:
        print("All candidates already exist in ideas.yaml")
        return

    data.setdefault("ideas", []).extend(new_ideas)

    with open(ideas_path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

    print(f"Added {len(new_ideas)} new candidates to data/ideas.yaml")

    # Update log
    log_path = DATA / "updates_log.yaml"
    log_data = {}
    if log_path.exists():
        with open(log_path, encoding="utf-8") as f:
            log_data = yaml.safe_load(f) or {}

    log_data.setdefault("updates", []).append({
        "date": datetime.datetime.utcnow().isoformat(),
        "action": "discovery",
        "new_candidates": len(new_ideas),
        "mode": "weekly"
    })

    with open(log_path, "w", encoding="utf-8") as f:
        yaml.dump(log_data, f, allow_unicode=True, default_flow_style=False)


def main() -> None:
    parser = argparse.ArgumentParser(description="Discover new AI idea candidates")
    parser.add_argument("--mode", choices=["weekly", "daily"], default="weekly")
    parser.add_argument("--source", choices=["github", "hn", "all"], default="all")
    parser.add_argument("--dry-run", action="store_true", help="Print candidates without saving")
    args = parser.parse_args()

    print(f"=== Discovering new AI ideas (mode={args.mode}, source={args.source}) ===")

    candidates = []

    if args.source in ("github", "all"):
        candidates.extend(discover_from_github(args.mode, args.dry_run))

    if args.source in ("hn", "all"):
        candidates.extend(discover_from_hn(args.mode, args.dry_run))

    save_candidates(candidates, args.dry_run)
    print("\nDiscovery complete")


if __name__ == "__main__":
    main()
