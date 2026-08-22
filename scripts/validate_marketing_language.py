#!/usr/bin/env python3
"""Scan all YAML and Markdown files for forbidden marketing language."""
import sys
import re
from pathlib import Path

ROOT = Path(__file__).parent.parent

FORBIDDEN_PHRASES = [
    r"guaranteed income",
    r"passive income",
    r"easy money",
    r"get rich",
    r"cash machine",
    r"make \$\d+[k]?",
    r"no effort",
    r"automatic revenue",
    r"risk.free business",
    r"secret method",
    r"zero work",
    r"side hustle.*\$\d+",
    r"financial freedom",
    r"quit your job.*ai",
    r"replace your income",
    r"autopilot.*income",
    r"set and forget.*money",
]

PATTERNS = [re.compile(p, re.IGNORECASE) for p in FORBIDDEN_PHRASES]

SCAN_EXTENSIONS = {".md", ".yaml", ".yml"}
SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv"}

# Governance files state the forbidden vocabulary on purpose: issue and PR templates
# quote it in their checklists, CONTRIBUTING defines the rule, and the PROJECT_*.md
# build spec discusses it. The rule applies to catalogue content, not to the text
# that describes the rule — scanning these files only ever produced false failures.
SKIP_DIR_NAMES = {".github"}
SKIP_FILE_NAMES = {"CONTRIBUTING.md"}
SKIP_FILE_PREFIXES = ("PROJECT_",)


def is_governance_file(path: Path) -> bool:
    if SKIP_DIR_NAMES & set(path.parts):
        return True
    if path.name in SKIP_FILE_NAMES:
        return True
    return path.name.startswith(SKIP_FILE_PREFIXES)

VIOLATIONS = []


def scan_file(path: Path) -> None:
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return

    for line_no, line in enumerate(text.splitlines(), 1):
        for pattern in PATTERNS:
            if pattern.search(line):
                msg = f"{path.relative_to(ROOT)}:{line_no}: '{line.strip()[:100]}'"
                VIOLATIONS.append(msg)
                print(f"  VIOLATION: {msg}", file=sys.stderr)


def main() -> None:
    print("=== Scanning for forbidden marketing language ===")

    for path in ROOT.rglob("*"):
        if path.is_file() and path.suffix in SCAN_EXTENSIONS:
            # Skip hidden dirs and venvs
            if any(part in SKIP_DIRS for part in path.parts):
                continue
            if is_governance_file(path.relative_to(ROOT)):
                continue
            scan_file(path)

    print(f"\nScanned files in: {ROOT}")
    print(f"Violations found: {len(VIOLATIONS)}")

    if VIOLATIONS:
        print("\nFAILED — remove forbidden phrases before merging", file=sys.stderr)
        sys.exit(1)
    else:
        print("\nPASSED — no forbidden phrases found")


if __name__ == "__main__":
    main()
