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

def _html_links(page: str, excluded_hosts: tuple[str, ...]) -> list[dict]:
    """Extract possible external search links without assuming the engine's CSS."""
    output = []
    for attrs, label in re.findall(r'<a\\b([^>]*)>(.*?)</a>', page, flags=re.I | re.S):
        href_match = re.search(r'href="([^"]+)"', attrs, flags=re.I)
        if not href_match:
            continue
        link = html.unescape(href_match.group(1))
        parsed = urllib.parse.urlparse(link)
        if parsed.path.startswith('/l/'):
            link = urllib.parse.parse_qs(parsed.query).get('uddg', [''])[0]
        parsed = urllib.parse.urlparse(link)
        if parsed.scheme not in ('http', 'https'):
            continue
        host = parsed.hostname or ''
        if any(host == h or host.endswith('.' + h) for h in excluded_hosts):
            continue
        title = html.unescape(re.sub(r'<[^>]+>', ' ', label)).strip()
        if len(title) < 8:
            continue
        output.append({'title': title[:250], 'url': link,
                       'snippet': '', 'verification': 'unverified'})
        if len(output) >= 10:
            break
    if not output:
        raise RuntimeError('No parseable search links')
    return output

def _html_search(endpoint: str, query: str, excluded_hosts: tuple[str, ...]) -> list[dict]:
    url = endpoint + '?' + urllib.parse.urlencode({'q': query})
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0', 'Accept': 'text/html'})
    with urllib.request.urlopen(req, timeout=20) as response:
        page = response.read(700_000).decode('utf-8', errors='replace')
    return _html_links(page, excluded_hosts)

def ddg_search(query: str) -> list[dict]:
    return _html_search('https://html.duckduckgo.com/html/', query, ('duckduckgo.com',))

def brave_search(query: str) -> list[dict]:
    return _html_search('https://search.brave.com/search', query, ('brave.com',))

def mojeek_search(query: str) -> list[dict]:
    return _html_search('https://www.mojeek.com/search', query, ('mojeek.com',))

def github_repository_search(query: str) -> list[dict]:
    url = 'https://api.github.com/search/repositories?' + urllib.parse.urlencode({'q': query, 'per_page': 10})
    req = urllib.request.Request(url, headers={'User-Agent': 'ECUAtlasResearcher/0.6',
                                              'Accept': 'application/vnd.github+json'})
    with urllib.request.urlopen(req, timeout=20) as response:
        payload = json.load(response)
    return [{'title': item.get('full_name', ''), 'url': item.get('html_url', ''),
             'snippet': item.get('description') or '', 'verification': 'unverified'}
            for item in payload.get('items', [])[:10] if item.get('html_url', '').startswith('https://')]

TECHNICAL_SITES = (
    'pcmflash.ru', 'bitbox.ru', 'ecutools.eu', 'alientech-tools.com',
    'magicmotorsport.com', 'autotuner.com', 'ecufix.info',
    'mhhauto.com', 'digital-kaos.co.uk', 'ecuconnections.com',
)

def specialist_queries(identifier: str) -> list[str]:
    """Domain-restricted leads; every result still requires exact ECU identity."""
    return ['site:' + domain + ' "' + identifier + '"' for domain in TECHNICAL_SITES]

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
    compact = re.sub(r'[^A-Z0-9]', '', text)
    return any(re.search(r'(?<![A-Z0-9])' + re.escape(identifier) + r'(?![A-Z0-9])', text) or identifier in compact for identifier in identifiers)

def run(ecu: str, base_url: str = '') -> dict:
    if not ecu.strip() or len(ecu) > 150:
        raise ValueError("ECU name must contain 1–150 characters")
    identifiers = ecu_identifiers(ecu)
    if not identifiers:
        raise ValueError("Specify an ECU model or hardware number containing digits")
    sections = {}
    seen = set()
    search_name = ' '.join(identifiers)
    for topic, pattern in SEARCH_TERMS.items():
        query = pattern.format(ecu=search_name)
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
        for query in ['"' + search_name + '"', search_name + ' ECU', 'Bosch ' + search_name, '"MG1 US008"' if search_name == 'MG1US008' else search_name + ' pinout', search_name + ' ECU Bosch processor']:
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
    if not seen:
        for query in ['"' + search_name + '" ECU', 'Bosch ' + search_name, search_name + ' flash EEPROM']:
            try:
                raw = ddg_search(query)
                results = []
                for item in raw:
                    url = item['url'].split('#')[0].rstrip('/')
                    if url in seen or not relevant_result(item, identifiers):
                        continue
                    seen.add(url)
                    results.append(item)
                sections['duckduckgo_' + str(len(sections))] = {'query': query, 'results': results, 'discarded': len(raw)-len(results)}
                if results:
                    break
            except Exception as exc:
                sections['duckduckgo_' + str(len(sections))] = {'query': query, 'results': [], 'error': str(exc)}
    if not seen:
        for query in ['"' + search_name + '" ECU', 'Bosch ' + search_name]:
            try:
                raw = brave_search(query)
                results = []
                for item in raw:
                    url = item['url'].split('#')[0].rstrip('/')
                    if url in seen or not relevant_result(item, identifiers):
                        continue
                    seen.add(url)
                    results.append(item)
                sections['brave_' + str(len(sections))] = {'query': query, 'results': results, 'discarded': len(raw)-len(results)}
                if results:
                    break
            except Exception as exc:
                sections['brave_' + str(len(sections))] = {'query': query, 'results': [], 'error': str(exc)}
    if not seen:
        for backend, finder in [('mojeek', mojeek_search), ('github', github_repository_search)]:
            try:
                raw = finder(search_name + (' ECU' if backend == 'mojeek' else ''))
                results = []
                for item in raw:
                    url = item['url'].split('#')[0].rstrip('/')
                    if url in seen or not relevant_result(item, identifiers):
                        continue
                    seen.add(url)
                    results.append(item)
                sections[backend + '_' + str(len(sections))] = {
                    'query': search_name, 'results': results, 'discarded': len(raw)-len(results)}
                if results:
                    break
            except Exception as exc:
                sections[backend + '_' + str(len(sections))] = {
                    'query': search_name, 'results': [], 'error': str(exc)}
    if not seen:
        specialist_results = []
        specialist_errors = []
        discarded = 0
        for query in specialist_queries(search_name):
            try:
                raw = search(query, base_url) if base_url else rss_search(query)
                for item in raw:
                    url = item['url'].split('#')[0].rstrip('/')
                    if url in seen or not relevant_result(item, identifiers):
                        discarded += 1
                        continue
                    seen.add(url)
                    specialist_results.append(item)
                if len(specialist_results) >= 10:
                    break
            except Exception as exc:
                specialist_errors.append(query + ': ' + str(exc))
        sections['specialist_sites'] = {
            'query': 'ECU identifier on specialist loader and forum sites',
            'results': specialist_results,
            'discarded': discarded,
            'error': '; '.join(specialist_errors[:3]) if specialist_errors else None,
        }
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
