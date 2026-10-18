"""ECU Atlas researcher: public web search -> review queue (no automatic publication).

Usage:
  python agents/researcher.py "Bosch MG1US008" --output research/out/mg1us008.json
Environment:
  BRAVE_SEARCH_API_KEY: optional Brave Search API key.
Without it the script fails clearly rather than fabricating results.
"""
import argparse
import datetime as dt
import json
import os
import pathlib
import sys
import urllib.parse
import urllib.request

SEARCH_TERMS = {
    "identification": '"{ecu}" hardware software ECU identification',
    "mcu": '"{ecu}" microcontroller processor SPC TC',
    "memory": '"{ecu}" flash eeprom memory size',
    "pinout": '"{ecu}" connector pinout wiring diagram',
    "loader": '"{ecu}" PCMflash BitBox bench boot read write',
    "field_reports": '"{ecu}" repair forum bench boot experience',
}
BRAVE_ENDPOINT = "https://api.search.brave.com/res/v1/web/search"

def search_brave(query: str, api_key: str, count: int = 5) -> list[dict]:
    url = BRAVE_ENDPOINT + "?" + urllib.parse.urlencode({"q": query, "count": count})
    req = urllib.request.Request(url, headers={
        "Accept": "application/json",
        "X-Subscription-Token": api_key,
        "User-Agent": "ECUAtlasResearcher/0.1",
    })
    with urllib.request.urlopen(req, timeout=25) as response:
        data = json.load(response)
    return [
        {"title": item.get("title", ""), "url": item.get("url", ""),
         "snippet": item.get("description", ""), "verification": "unverified",
         "review_required": True}
        for item in data.get("web", {}).get("results", [])
        if item.get("url", "").startswith(("https://", "http://"))
    ]

def run(ecu: str, api_key: str) -> dict:
    if not api_key:
        raise RuntimeError("BRAVE_SEARCH_API_KEY is required for real web search.")
    if not ecu.strip() or len(ecu) > 150:
        raise ValueError("ECU identifier must contain 1–150 characters")
    sections = {}
    for category, template in SEARCH_TERMS.items():
        query = template.format(ecu=ecu.strip())
        try:
            sections[category] = {"query": query, "results": search_brave(query, api_key)}
        except Exception as exc:
            sections[category] = {"query": query, "results": [], "error": str(exc)}
    return {
        "ecu": ecu.strip(),
        "created_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "status": "needs_human_verification",
        "publication": "blocked",
        "note": "Search results are leads, not verified technical facts. Do not connect or power ECU from snippets.",
        "sections": sections,
    }

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("ecu", help="ECU family, model or HW number")
    parser.add_argument("--output", default="research/out/research.json")
    args = parser.parse_args()
    try:
        result = run(args.ecu, os.environ.get("BRAVE_SEARCH_API_KEY", ""))
    except (RuntimeError, ValueError) as exc:
        print(f"Research not started: {exc}", file=sys.stderr)
        return 2
    path = pathlib.Path(args.output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Saved {sum(len(x['results']) for x in result['sections'].values())} leads to {path}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
