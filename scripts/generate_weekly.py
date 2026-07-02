#!/usr/bin/env python3
"""Generate WEEKLY.md, TOP10.md and social/latest.md from the main data file."""
import datetime
from pathlib import Path

import yaml

ROOT = Path(__file__).parent.parent
DATA = ROOT / "data"

# Repo-specific configuration
DATA_FILE = "ideas.yaml"
DATA_KEY = "ideas"
ENTRY_LABEL = "idea"
TITLE_FIELD = "title"
SUMMARY_FIELD = "summary"
REPO_URL = "https://github.com/msdw/awesome-ai-idea-engine"
REPO_NAME = "Awesome AI Idea Engine"
HUB_URL = "https://msdw.github.io/awesome-ai-hub/"


def load_entries() -> list:
    with open(DATA / DATA_FILE, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return data.get(DATA_KEY, [])


def total_score(entry: dict) -> int:
    scoring = entry.get("scoring") or {}
    return sum(v for v in scoring.values() if isinstance(v, (int, float)))


def discovered_at(entry: dict) -> str:
    meta = entry.get("_meta") or {}
    return meta.get("discovered_at", "")


def recent_entries(entries: list, days: int = 7) -> list:
    now = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
    cutoff = (now - datetime.timedelta(days=days)).isoformat()
    recent = [e for e in entries if discovered_at(e) >= cutoff]
    if not recent:
        # Fall back to the most recently discovered entries so the digest is never empty
        dated = [e for e in entries if discovered_at(e)]
        recent = sorted(dated, key=discovered_at, reverse=True)[:5]
    if not recent:
        # No dated entries at all — highlight the best of the full list instead
        recent = entries[:5]
    return sorted(recent, key=total_score, reverse=True)


def entry_line(e: dict) -> str:
    title = e.get(TITLE_FIELD, e.get("id", "Untitled"))
    summary = (e.get(SUMMARY_FIELD) or "").strip()
    source = e.get("source", "")
    score = total_score(e)
    line = f"- **{title}**"
    if summary:
        line += f" — {summary}"
    line += f" *(score: {score})*"
    if source.startswith("http"):
        line += f" — [source]({source})"
    return line


def write_weekly(entries: list) -> list:
    picks = recent_entries(entries)
    today = datetime.date.today().isoformat()
    lines = [
        f"# This Week's Finds — {today}",
        "",
        f"The latest {ENTRY_LABEL} candidates discovered by our automated weekly scan, ranked by score.",
        f"Curated by hand — see [the full list]({REPO_URL}).",
        "",
    ]
    lines += [entry_line(e) for e in picks]
    lines += [
        "",
        "---",
        "",
        f"📬 [Get this digest by email]({HUB_URL}) · "
        f"🔗 Part of the [Awesome AI Builder Series]({HUB_URL})",
        "",
    ]
    (ROOT / "WEEKLY.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"WEEKLY.md written ({len(picks)} entries)")
    return picks


def write_top10(entries: list) -> None:
    ranked = sorted(entries, key=total_score, reverse=True)[:10]
    today = datetime.date.today().isoformat()
    lines = [
        f"# Top 10 — updated {today}",
        "",
        f"The 10 highest-scoring entries in the {REPO_NAME}, across all scoring dimensions.",
        "",
    ]
    for i, e in enumerate(ranked, 1):
        title = e.get(TITLE_FIELD, e.get("id", "Untitled"))
        summary = (e.get(SUMMARY_FIELD) or "").strip()
        lines.append(f"{i}. **{title}** *(score: {total_score(e)})*")
        if summary:
            lines.append(f"   {summary}")
    lines += [
        "",
        "---",
        "",
        f"📬 [Get weekly updates]({HUB_URL}) · 🔗 [Awesome AI Builder Series]({HUB_URL})",
        "",
    ]
    (ROOT / "TOP10.md").write_text("\n".join(lines), encoding="utf-8")
    print("TOP10.md written")


def write_social(picks: list) -> None:
    top3 = picks[:3]
    today = datetime.date.today().isoformat()
    social_dir = ROOT / "social"
    social_dir.mkdir(exist_ok=True)

    def short_title(e):
        return e.get(TITLE_FIELD, e.get("id", "Untitled"))

    linkedin = [
        f"This week in {REPO_NAME} ({today}):",
        "",
    ]
    for e in top3:
        summary = (e.get(SUMMARY_FIELD) or "").strip()
        linkedin.append(f"→ {short_title(e)}" + (f" — {summary}" if summary else ""))
    linkedin += [
        "",
        "Every entry is scored, structured, and hype-free.",
        f"Full list: {REPO_URL}",
        f"The whole series: {HUB_URL}",
    ]

    x_post = [
        f"This week's top AI {ENTRY_LABEL}s, scored and structured — no hype:",
        "",
    ]
    for e in top3:
        x_post.append(f"→ {short_title(e)}")
    x_post += ["", REPO_URL]

    content = [
        f"# Social posts — {today}",
        "",
        "Copy-paste ready. Review before publishing.",
        "",
        "## LinkedIn",
        "",
        "```",
        *linkedin,
        "```",
        "",
        "## X / Twitter",
        "",
        "```",
        *x_post,
        "```",
        "",
    ]
    (social_dir / "latest.md").write_text("\n".join(content), encoding="utf-8")
    print("social/latest.md written")


def main():
    entries = load_entries()
    if not entries:
        print("No entries found — nothing to generate")
        return
    picks = write_weekly(entries)
    write_top10(entries)
    write_social(picks)


if __name__ == "__main__":
    main()
