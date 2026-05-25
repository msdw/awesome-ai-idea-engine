#!/usr/bin/env python3
"""Compute and update composite scores for all accepted ideas."""
import yaml
from pathlib import Path

ROOT = Path(__file__).parent.parent
DATA = ROOT / "data"

WEIGHTS = {
    "pain_intensity": 0.20,
    "willingness_to_pay": 0.20,
    "ai_fit": 0.15,
    "buildability": 0.15,
    "market_signal": 0.10,
    "differentiation_potential": 0.10,
    "monetization_potential": 0.05,
    "compliance_risk": 0.05,  # lower is better — inverted
}


def composite_score(scoring: dict) -> float:
    total = 0.0
    for field, weight in WEIGHTS.items():
        val = scoring.get(field, 5)
        if field == "compliance_risk":
            val = 11 - val  # invert — lower risk = higher score
        total += val * weight
    return round(total, 2)


def main() -> None:
    ideas_path = DATA / "ideas.yaml"
    with open(ideas_path, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    updated = 0
    for idea in data.get("ideas", []):
        if idea.get("status") != "accepted":
            continue
        scoring = idea.get("scoring", {})
        if scoring:
            idea["composite_score"] = composite_score(scoring)
            updated += 1

    with open(ideas_path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

    print(f"Updated composite scores for {updated} ideas")
    # Print top ideas by score
    ideas = [i for i in data.get("ideas", []) if "composite_score" in i]
    ideas.sort(key=lambda x: x["composite_score"], reverse=True)
    print("\nTop ideas by composite score:")
    for idea in ideas[:10]:
        print(f"  {idea['composite_score']:.2f}  {idea['title'][:70]}")


if __name__ == "__main__":
    main()
