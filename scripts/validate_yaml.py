#!/usr/bin/env python3
"""Validate all YAML data files against required schema."""
import sys
import yaml
from pathlib import Path

ROOT = Path(__file__).parent.parent
DATA = ROOT / "data"

REQUIRED_IDEA_FIELDS = [
    "id", "title", "summary", "category", "target_users",
    "pain_points", "ai_solution", "ai_patterns",
    "possible_business_models", "difficulty", "risk_level",
    "validation_steps", "scoring", "tags", "source", "status"
]

REQUIRED_SCORING_FIELDS = [
    "pain_intensity", "willingness_to_pay", "ai_fit", "buildability",
    "market_signal", "differentiation_potential", "monetization_potential",
    "compliance_risk"
]

VALID_STATUSES = {"candidate", "needs_review", "accepted", "rejected", "duplicate", "deprecated"}
VALID_DIFFICULTIES = {"low", "medium", "high", "very_high"}
VALID_RISK_LEVELS = {"low", "medium", "high", "very_high"}

REGULATED_INDUSTRIES = {"legal", "healthcare", "finance", "insurance", "energy", "government"}

ERRORS = []
WARNINGS = []


def error(msg: str) -> None:
    ERRORS.append(msg)
    print(f"  ERROR: {msg}", file=sys.stderr)


def warn(msg: str) -> None:
    WARNINGS.append(msg)
    print(f"  WARN:  {msg}")


def load_yaml(path: Path) -> dict | list | None:
    try:
        with open(path, encoding="utf-8") as f:
            return yaml.safe_load(f)
    except yaml.YAMLError as e:
        error(f"YAML parse error in {path.name}: {e}")
        return None
    except FileNotFoundError:
        error(f"File not found: {path}")
        return None


def validate_ideas(path: Path) -> None:
    print(f"\nValidating {path.name}...")
    data = load_yaml(path)
    if data is None:
        return

    ideas = data.get("ideas", [])
    if not ideas:
        warn("ideas.yaml has no entries")
        return

    seen_ids = set()
    for i, idea in enumerate(ideas):
        prefix = f"ideas[{i}] id={idea.get('id', '?')}"

        # Check duplicate IDs
        idea_id = idea.get("id")
        if idea_id in seen_ids:
            error(f"{prefix}: duplicate id '{idea_id}'")
        seen_ids.add(idea_id)

        # Check required fields
        for field in REQUIRED_IDEA_FIELDS:
            if field not in idea:
                error(f"{prefix}: missing required field '{field}'")

        # Check status
        status = idea.get("status")
        if status and status not in VALID_STATUSES:
            error(f"{prefix}: invalid status '{status}' — must be one of {VALID_STATUSES}")

        # Check difficulty
        diff = idea.get("difficulty")
        if diff and diff not in VALID_DIFFICULTIES:
            error(f"{prefix}: invalid difficulty '{diff}' — must be one of {VALID_DIFFICULTIES}")

        # Check risk_level
        risk = idea.get("risk_level")
        if risk and risk not in VALID_RISK_LEVELS:
            error(f"{prefix}: invalid risk_level '{risk}' — must be one of {VALID_RISK_LEVELS}")

        # Check scoring fields
        scoring = idea.get("scoring", {})
        if scoring:
            for sf in REQUIRED_SCORING_FIELDS:
                if sf not in scoring:
                    error(f"{prefix}: missing scoring field '{sf}'")
                else:
                    val = scoring[sf]
                    if not isinstance(val, (int, float)) or not (1 <= val <= 10):
                        error(f"{prefix}: scoring.{sf}={val} must be a number between 1 and 10")

        # Check regulated domain compliance notes
        industries = idea.get("industries", [])
        if any(ind in REGULATED_INDUSTRIES for ind in industries):
            if not idea.get("compliance_notes"):
                error(f"{prefix}: industries include regulated domain but compliance_notes is missing")

    print(f"  Checked {len(ideas)} ideas, {len(seen_ids)} unique IDs")


def validate_taxonomy(path: Path, key: str) -> set:
    """Load a taxonomy file and return valid IDs."""
    print(f"\nValidating {path.name}...")
    data = load_yaml(path)
    if data is None:
        return set()
    items = data.get(key, [])
    ids = {item["id"] for item in items if "id" in item}
    print(f"  Found {len(ids)} entries")
    return ids


def main() -> None:
    print("=== Validating YAML schemas ===")

    # Validate taxonomy files exist and parse
    validate_taxonomy(DATA / "categories.yaml", "categories")
    validate_taxonomy(DATA / "business_models.yaml", "business_models")
    validate_taxonomy(DATA / "ai_patterns.yaml", "ai_patterns")
    validate_taxonomy(DATA / "risk_levels.yaml", "risk_levels")
    validate_taxonomy(DATA / "industries.yaml", "industries")
    validate_taxonomy(DATA / "roles.yaml", "roles")
    validate_taxonomy(DATA / "tags.yaml", "tags")
    validate_taxonomy(DATA / "technical_stacks.yaml", "technical_stacks")
    validate_taxonomy(DATA / "validation_methods.yaml", "validation_methods")

    # Validate sources and updates_log
    for fname in ["sources.yaml", "updates_log.yaml"]:
        p = DATA / fname
        if p.exists():
            load_yaml(p)
            print(f"\nValidating {fname}... OK")

    # Validate ideas
    validate_ideas(DATA / "ideas.yaml")

    print("\n=== Summary ===")
    print(f"  Errors:   {len(ERRORS)}")
    print(f"  Warnings: {len(WARNINGS)}")

    if ERRORS:
        print("\nFAILED — fix errors above before merging", file=sys.stderr)
        sys.exit(1)
    else:
        print("\nPASSED")


if __name__ == "__main__":
    main()
