"""Collect technical-document leads already discovered by search."""
from urllib.parse import urlparse

DOCUMENT_WORDS = ('datasheet', 'manual', 'service', 'wiring', 'schematic',
                  'pinout', 'application note', 'документация', 'схема',
                  'руководство', 'распиновка', 'pdf', 'technical')

def documentation_leads(research: dict) -> dict:
    leads = []
    seen = set()
    for category, section in research.get('sections', {}).items():
        for item in section.get('results', []):
            url = item.get('url', '')
            parsed = urlparse(url)
            if parsed.scheme not in ('https', 'http') or not parsed.hostname or url in seen:
                continue
            combined = ' '.join([item.get('title', ''), item.get('snippet', ''), parsed.path]).lower()
            tags = [word for word in DOCUMENT_WORDS if word in combined]
            if not tags:
                continue
            seen.add(url)
            leads.append({'source_url': url, 'title': item.get('title', ''),
                          'search_category': category, 'document_clues': tags,
                          'verification': 'unverified', 'requires_manual_review': True,
                          'note': 'Candidate documentation link, not a verified PDF or OEM manual.'})
    return {'agent': 'documentation', 'publication': 'blocked', 'leads': leads[:100]}
