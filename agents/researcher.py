"""Free ECU Atlas researcher: public search via configurable SearXNG JSON endpoint.

Set SEARXNG_URL to a trusted instance you control, with JSON output enabled.
No paid search API or payment card required. Public instances may reject bots.
"""
import argparse
import datetime as dt
import json
import os
from pathlib import Path
import sys
import urllib.parse
import urllib.request

SEARCH_TERMS = {
    "identification": '"{ecu}" ECU HW SW identification',
    "mcu": '"{ecu}" processor MCU SPC TC',
    "memory": '"{ecu}" Flash EEPROM size',
    "pinout": '"{ecu}" connector pinout wiring',
    "loader": '"{ecu}" PCMflash BitBox CombiLoader Bench Boot',
    "field_reports": '"{ecu}" forum repair read write experience',
}

def search(query: str, base_url: str) -> list[dict]:
    parsed = urllib.parse.urlparse(base_url)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise ValueError("SEARXNG_URL must be a full HTTP(S) URL")
    endpoint = base_url.rstrip("/") + "/search"
    url = endpoint + "?" + urllib.parse.urlencode({"q": query, "format": "json", "language": "ru-RU"})
    request = urllib.request.Request(url, headers={"User-Agent": "ECUAtlasResearcher/0.2", "Accept": "application/json"})
    with urllib.request.urlopen(request, timeout=25) as response:
        payload = json.load(response)
    return [
        {"title": r.get("title", ""), "url": r.get("url", ""),
         "snippet": r.get("content", ""), "verification": "unverified"}
        for r in payload.get("results", [])[:10]
        if str(r.get("url", "")).startswith(("https://", "http://"))
    ]

def run(ecu: str, base_url: str) -> dict:
    if not base_url:
        raise ValueError("SEARXNG_URL is required. Deploy a SearXNG instance with JSON enabled.")
    if not ecu.strip() or len(ecu) > 150:
        raise ValueError("ECU name must contain 1–150 characters")
    sections = {}
    for topic, pattern in SEARCH_TERMS.items():
        query = pattern.format(ecu=ecu.strip())
        try:
            sections[topic] = {"query": query, "results": search(query, base_url)}
        except Exception as exc:
            sections[topic] = {"query": query, "results": [], "error": str(exc)}
    return {
        "ecu": ecu.strip(),
        "created_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "status": "needs_human_verification",
        "publication": "blocked",
        "sections": sections,
    }

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("ecu")
    parser.add_argument("--output", default="research/out/latest.json")
    args = parser.parse_args()
    try:
        result = run(args.ecu, os.getenv("SEARXNG_URL", ""))
    except ValueError as exc:
        print(exc, file=sys.stderr)
        sys.exit(2)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Saved {sum(len(s['results']) for s in result['sections'].values())} unverified leads to {output}")
