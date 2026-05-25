#!/usr/bin/env python3
"""Generate browseable index pages from YAML data."""
import sys
import argparse
import yaml
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).parent.parent
DATA = ROOT / "data"
IDEAS_DIR = ROOT / "ideas"

HEADER = "<!-- AUTO-GENERATED — do not edit manually. Run: python scripts/generate_markdown.py -->\n\n"


def load_yaml(path: Path) -> dict | list | None:
    if not path.exists():
        return None
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_ideas() -> list[dict]:
    data = load_yaml(DATA / "ideas.yaml")
    if not data:
        return []
    return [i for i in data.get("ideas", []) if i.get("status") == "accepted"]


def idea_link(idea: dict) -> str:
    return f"- [{idea['title']}](../data/ideas.yaml) — {idea.get('summary', '')[:100].strip()}"


def write_page(path: Path, content: str, check_only: bool) -> bool:
    """Write page. Returns True if content changed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    full = HEADER + content

    if path.exists():
        existing = path.read_text(encoding="utf-8")
        if existing == full:
            return False

    if check_only:
        print(f"  WOULD WRITE: {path.relative_to(ROOT)}")
        return True

    path.write_text(full, encoding="utf-8")
    print(f"  WROTE: {path.relative_to(ROOT)}")
    return True


def generate_by_industry(ideas: list[dict], check_only: bool) -> None:
    grouped = defaultdict(list)
    for idea in ideas:
        for ind in idea.get("industries", ["uncategorized"]):
            grouped[ind].append(idea)

    lines = ["# Ideas by Industry\n\n"]
    for industry in sorted(grouped):
        lines.append(f"## {industry.replace('_', ' ').title()}\n\n")
        for idea in grouped[industry]:
            lines.append(idea_link(idea) + "\n")
        lines.append("\n")

    write_page(IDEAS_DIR / "by-industry.md", "".join(lines), check_only)


def generate_by_role(ideas: list[dict], check_only: bool) -> None:
    grouped = defaultdict(list)
    for idea in ideas:
        for role in idea.get("target_users", ["other"]):
            grouped[role].append(idea)

    lines = ["# Ideas by Target Role\n\n"]
    for role in sorted(grouped):
        lines.append(f"## {role.replace('_', ' ').title()}\n\n")
        for idea in grouped[role]:
            lines.append(idea_link(idea) + "\n")
        lines.append("\n")

    write_page(IDEAS_DIR / "by-role.md", "".join(lines), check_only)


def generate_by_business_model(ideas: list[dict], check_only: bool) -> None:
    grouped = defaultdict(list)
    for idea in ideas:
        for bm in idea.get("possible_business_models", ["other"]):
            grouped[bm].append(idea)

    lines = ["# Ideas by Business Model\n\n"]
    for bm in sorted(grouped):
        lines.append(f"## {bm.replace('_', ' ').title()}\n\n")
        for idea in grouped[bm]:
            lines.append(idea_link(idea) + "\n")
        lines.append("\n")

    write_page(IDEAS_DIR / "by-business-model.md", "".join(lines), check_only)


def generate_by_technical_stack(ideas: list[dict], check_only: bool) -> None:
    grouped = defaultdict(list)
    for idea in ideas:
        for stack in idea.get("technical_stack", ["other"]):
            grouped[stack].append(idea)

    lines = ["# Ideas by Technical Stack\n\n"]
    for stack in sorted(grouped):
        lines.append(f"## {stack.replace('_', ' ').title()}\n\n")
        for idea in grouped[stack]:
            lines.append(idea_link(idea) + "\n")
        lines.append("\n")

    write_page(IDEAS_DIR / "by-technical-stack.md", "".join(lines), check_only)


def generate_by_difficulty(ideas: list[dict], check_only: bool) -> None:
    order = ["low", "medium", "high", "very_high"]
    grouped = defaultdict(list)
    for idea in ideas:
        grouped[idea.get("difficulty", "unknown")].append(idea)

    lines = ["# Ideas by Difficulty\n\n"]
    for diff in order:
        if diff in grouped:
            lines.append(f"## {diff.replace('_', ' ').title()}\n\n")
            for idea in grouped[diff]:
                lines.append(idea_link(idea) + "\n")
            lines.append("\n")

    write_page(IDEAS_DIR / "by-difficulty.md", "".join(lines), check_only)


def generate_by_time_to_build(ideas: list[dict], check_only: bool) -> None:
    grouped = defaultdict(list)
    for idea in ideas:
        grouped[idea.get("time_to_mvp", "unknown")].append(idea)

    lines = ["# Ideas by Time to Build\n\n"]
    for ttb in sorted(grouped):
        lines.append(f"## {ttb}\n\n")
        for idea in grouped[ttb]:
            lines.append(idea_link(idea) + "\n")
        lines.append("\n")

    write_page(IDEAS_DIR / "by-time-to-build.md", "".join(lines), check_only)


def generate_by_risk_level(ideas: list[dict], check_only: bool) -> None:
    order = ["low", "medium", "high", "very_high"]
    grouped = defaultdict(list)
    for idea in ideas:
        grouped[idea.get("risk_level", "unknown")].append(idea)

    lines = ["# Ideas by Risk Level\n\n"]
    for risk in order:
        if risk in grouped:
            lines.append(f"## {risk.replace('_', ' ').title()}\n\n")
            for idea in grouped[risk]:
                lines.append(idea_link(idea) + "\n")
            lines.append("\n")

    write_page(IDEAS_DIR / "by-risk-level.md", "".join(lines), check_only)


def generate_by_ai_pattern(ideas: list[dict], check_only: bool) -> None:
    grouped = defaultdict(list)
    for idea in ideas:
        for pattern in idea.get("ai_patterns", ["other"]):
            grouped[pattern].append(idea)

    lines = ["# Ideas by AI Pattern\n\n"]
    for pattern in sorted(grouped):
        lines.append(f"## {pattern.replace('_', ' ').title()}\n\n")
        for idea in grouped[pattern]:
            lines.append(idea_link(idea) + "\n")
        lines.append("\n")

    write_page(IDEAS_DIR / "by-ai-pattern.md", "".join(lines), check_only)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate Markdown index pages from YAML data")
    parser.add_argument("--check", action="store_true", help="Check what would be written without writing")
    parser.add_argument("--force", action="store_true", help="Regenerate all pages even if unchanged")
    args = parser.parse_args()

    print(f"=== {'Checking' if args.check else 'Generating'} Markdown pages ===")

    ideas = load_ideas()
    print(f"Loaded {len(ideas)} accepted ideas")

    if not ideas:
        print("No accepted ideas found — nothing to generate")
        sys.exit(0)

    generate_by_industry(ideas, args.check)
    generate_by_role(ideas, args.check)
    generate_by_business_model(ideas, args.check)
    generate_by_technical_stack(ideas, args.check)
    generate_by_difficulty(ideas, args.check)
    generate_by_time_to_build(ideas, args.check)
    generate_by_risk_level(ideas, args.check)
    generate_by_ai_pattern(ideas, args.check)

    print("\nDone")


if __name__ == "__main__":
    main()
