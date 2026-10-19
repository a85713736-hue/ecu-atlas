"""Cross-check candidate ECU facts against independent source domains.

Evidence scoring only; never confirms a pinout or enables publication.
"""
from collections import defaultdict
from urllib.parse import urlparse

def crosscheck(extracted: dict) -> dict:
    claims = defaultdict(lambda: {'domains': set(), 'sources': set(), 'excerpts': []})
    for document in extracted.get('documents', []):
        url = document.get('source_url', '')
        host = (urlparse(url).hostname or '').lower().removeprefix('www.')
        if not host:
            continue
        for candidate in document.get('candidates', []):
            key = (str(candidate.get('category', '')).lower(), str(candidate.get('value', '')).strip().upper())
            if not key[0] or not key[1]:
                continue
            entry = claims[key]
            entry['domains'].add(host)
            entry['sources'].add(url)
            if len(entry['excerpts']) < 3:
                entry['excerpts'].append(candidate.get('excerpt', ''))
    output = []
    for (category, value), item in claims.items():
        output.append({'category': category, 'value': value,
                       'independent_domains': len(item['domains']),
                       'source_urls': sorted(item['sources'])[:10],
                       'excerpts': item['excerpts'],
                       'corroborated_lead': len(item['domains']) >= 2,
                       'verification': 'unverified', 'manual_review_required': True})
    output.sort(key=lambda item: (-item['independent_domains'], item['category'], item['value']))
    return {'agent': 'crosscheck', 'publication': 'blocked', 'claims': output[:100]}
