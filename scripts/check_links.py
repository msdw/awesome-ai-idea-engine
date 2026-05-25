#!/usr/bin/env python3
"""Check URLs in Markdown and YAML files for broken links."""
import sys
import re
import time
import argparse
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

ROOT = Path(__file__).parent.parent

URL_PATTERN = re.compile(r'https?://[^\s\)\]\"\'<>]+')

SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv"}
SKIP_DOMAINS = {
    "localhost",
    "127.0.0.1",
    "example.com",
    "your-domain.com",
}

# URLs that return non-200 but are valid
IGNORE_LIST = set()

REQUEST_DELAY = 1.0
TIMEOUT = 10

broken = []
skipped = []
checked = set()


def check_url(url: str, source_file: str) -> bool:
    """Return True if URL is reachable."""
    # Clean trailing punctuation
    url = url.rstrip(".,;:)'\"")

    if url in checked:
        return True
    checked.add(url)

    domain = re.sub(r'^https?://', '', url).split('/')[0]
    if domain in SKIP_DOMAINS or url in IGNORE_LIST:
        skipped.append(url)
        return True

    try:
        req = Request(url, headers={"User-Agent": "awesome-ai-link-checker/1.0"})
        resp = urlopen(req, timeout=TIMEOUT)
        status = resp.status
        time.sleep(REQUEST_DELAY)
        if status < 400:
            return True
        broken.append((url, f"HTTP {status}", source_file))
        return False
    except HTTPError as e:
        if e.code == 429:
            # Rate limited — treat as skipped
            skipped.append(url)
            return True
        broken.append((url, f"HTTP {e.code}", source_file))
        time.sleep(REQUEST_DELAY)
        return False
    except URLError as e:
        broken.append((url, str(e.reason), source_file))
        return False
    except Exception as e:
        broken.append((url, str(e), source_file))
        return False


def scan_file(path: Path) -> None:
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return

    urls = URL_PATTERN.findall(text)
    for url in urls:
        check_url(url, str(path.relative_to(ROOT)))


def main() -> None:
    parser = argparse.ArgumentParser(description="Check links in Markdown and YAML files")
    parser.add_argument("--hard", action="store_true", help="Exit 1 on broken links (default: soft)")
    args = parser.parse_args()

    print("=== Checking links ===")
    print(f"Mode: {'hard (fail on broken)' if args.hard else 'soft (warn only)'}")

    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix not in {".md", ".yaml", ".yml"}:
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        scan_file(path)

    print(f"\nURLs checked: {len(checked)}")
    print(f"Skipped:      {len(skipped)}")
    print(f"Broken:       {len(broken)}")

    if broken:
        print("\nBroken links:", file=sys.stderr)
        for url, reason, src in broken:
            print(f"  {src}: {url} — {reason}", file=sys.stderr)
        if args.hard:
            sys.exit(1)
    else:
        print("\nAll links OK")


if __name__ == "__main__":
    main()
