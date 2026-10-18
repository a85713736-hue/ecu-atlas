"""Validate researcher output and prepare an ECU Atlas review report.

Never automatically approve pinouts, memory maps, test points, or loader operations.
Usage: python agents/verify.py research/out/latest.json
"""
import argparse
import json
from pathlib import Path
from urllib.parse import urlparse

CATEGORIES = ("identification", "mcu", "memory", "pinout", "loader", "field_reports")

def verify(document: dict) -> dict:
    findings = []
    seen = set()
    errors = []
    for category in CATEGORIES:
        section = document.get("sections", {}).get(category, {})
        if section.get("error"):
            errors.append({"category": category, "error": section["error"]})
        for item in section.get("results", []):
            url = item.get("url", "")
            parsed = urlparse(url)
            if parsed.scheme not in ("https", "http") or not parsed.netloc:
                continue
            key = (category, url.rstrip("/"))
            if key in seen:
                continue
            seen.add(key)
            findings.append({
                "category": category,
                "title": item.get("title", ""),
                "source_url": url,
                "snippet": item.get("snippet", ""),
                "verification": "unverified",
                "requires_manual_review": True,
                "ecu_hardware_id": None,
                "claims": [],
            })
    return {
        "ecu": document.get("ecu"),
        "review_status": "pending",
        "publish_allowed": False,
        "source_count": len(findings),
        "errors": errors,
        "findings": findings,
        "review_checklist": [
            "Check that source content supports the exact technical claim",
            "Match ECU hardware and PCB revision before attributing pins",
            "Check connector numbering and orientation from an actual diagram",
            "Identify MCU marking and memory capacities from authoritative evidence",
            "Distinguish loader family support from verified HW/SW compatibility",
            "Require independent corroboration or original documentation for safety-critical claims",
        ],
    }

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input")
    parser.add_argument("--output", default="research/out/review.json")
    args = parser.parse_args()
    document = json.loads(Path(args.input).read_text(encoding="utf-8"))
    report = verify(document)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{report['source_count']} leads queued for verification; publication blocked")

if __name__ == "__main__":
    main()
