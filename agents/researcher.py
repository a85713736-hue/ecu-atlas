"""Free ECU Atlas researcher: Bing RSS or optional self-hosted SearXNG.

No API key required for RSS. Optional SEARXNG_URL enables self-hosted search.
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
import xml.etree.ElementTree as ET
import re
import html

SEARCH_TERMS = {
    "identification": '"{ecu}" ECU HW SW automotive',
    "mcu": '"{ecu}" ECU microcontroller processor',
    "memory": '"{ecu}" ECU Flash EEPROM',
    "pinout": '"{ecu}" ECU pinout bench',
    "loader": '"{ecu}" PCMflash BitBox bench boot',
    "field_reports": '"{ecu}" ECU forum read write',
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

def rss_search(query: str) -> list[dict]:
    url = 'https://www.bing.com/search?' + urllib.parse.urlencode({'q': query, 'format': 'rss'})
    req = urllib.request.Request(url, headers={'User-Agent':'Mozilla/5.0 ECUAtlasResearch/0.4','Accept':'application/rss+xml,application/xml'})
    with urllib.request.urlopen(req, timeout=25) as response:
        data = response.read(700_000)
    root = ET.fromstring(data)
    output = []
    for item in root.findall('./channel/item')[:10]:
        link = (item.findtext('link') or '').strip()
        if not link.startswith(('https://','http://')): continue
        output.append({'title':html.unescape(item.findtext('title') or ''),
                       'url':link,
                       'snippet':re.sub(r'<[^>]*>', ' ', html.unescape(item.findtext('description') or ''))[:700],
                       'verification':'unverified'})
    if not output: raise RuntimeError('RSS search returned no items')
    return output

def ecu_identifiers(ecu: str) -> list[str]:
    return [token.upper() for token in re.findall(r'[A-Za-z0-9]+', ecu)
            if len(token) >= 5 and any(ch.isdigit() for ch in token)]

def relevant_result(item: dict, identifiers: list[str]) -> bool:
    text = ' '.join(str(item.get(k, '')) for k in ('title', 'url', 'snippet')).upper()
    host = urllib.parse.urlparse(item.get('url', '')).hostname or ''
    if any(term in host.lower() for term in ('bosch-home.', 'boschtools.')):
        return False
    if any(term in text for term in ('DISHWASHER', 'REFRIGERATOR', 'TV SERIES', 'POLICE PROCEDURAL')):
        return False
    return any(re.search(r'(?<![A-Z0-9])' + re.escape(identifier) + r'(?![A-Z0-9])', text) for identifier in identifiers)

def run(ecu: str, base_url: str = '') -> dict:
    if not ecu.strip() or len(ecu) > 150:
        raise ValueError("ECU name must contain 1–150 characters")
    identifiers = ecu_identifiers(ecu)
    if not identifiers:
        raise ValueError("Specify an ECU model or hardware number containing digits")
    sections = {}
    seen = set()
    search_name = ' '.join(identifiers)
    variants = [search_name, ' '.join(re.findall(r'[A-Za-z]+|[0-9]+', search_name))]
    for topic, pattern in SEARCH_TERMS.items():
        query = pattern.format(ecu=variants[0])
        try:
            raw = search(query, base_url) if base_url else rss_search(query)
            results = []
            for item in raw:
                url = item['url'].split('#')[0].rstrip('/')
                if url in seen or not relevant_result(item, identifiers):
                    continue
                seen.add(url)
                results.append(item)
            sections[topic] = {"query": query, "results": results, "discarded": len(raw) - len(results)}
        except Exception as exc:
            sections[topic] = {"query": query, "results": [], "error": str(exc)}
    if not seen:
        for query in ['"' + search_name + '"', search_name + ' ECU', 'Bosch ' + search_name]:
            try:
                raw = search(query, base_url) if base_url else rss_search(query)
                results = [item for item in raw if relevant_result(item, identifiers) and item['url'] not in seen]
                for item in results:
                    seen.add(item['url'])
                sections['fallback_' + str(len(sections))] = {'query': query, 'results': results}
                if results:
                    break
            except Exception as exc:
                sections['fallback_' + str(len(sections))] = {'query': query, 'results': [], 'error': str(exc)}
    return {
        "search_backend": "searxng" if base_url else "bing_rss",
        "ecu": ecu.strip(),
        "relevant_source_count": len(seen),
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
