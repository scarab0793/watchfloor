#!/usr/bin/env python3
"""Conservative editorial staging; leaves live pages untouched."""
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CONFIG = ROOT / "editorial_config.json"
SELECTED = ROOT / "selected.json"
ARCHIVE = ROOT / "editorial.json"

def main():
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    selected = json.loads(SELECTED.read_text(encoding="utf-8"))
    archive = json.loads(ARCHIVE.read_text(encoding="utf-8")) if ARCHIVE.exists() else {"items": []}
    if not isinstance(selected, list) or not isinstance(archive.get("items"), list):
        raise ValueError("Invalid editorial input")
    pending = [item for item in selected if item.get("status") == "staging_unverified"]
    print("Candidate reports:", len(pending))
    print("Existing editorial reports:", len(archive["items"]))
    print("Configured per-run limit:", config["max_articles_per_run"])
    print("Live publishing disabled until source verification and translation integration pass")
    if not os.getenv("OPENAI_API_KEY"):
        print("OPENAI_API_KEY missing; no API usage attempted")

if __name__ == "__main__":
    main()
