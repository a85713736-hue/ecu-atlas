"""Identify loader and read/write mode mentions in extracted ECU sources."""
import re

LOADERS = re.compile(r'(?i)\b(?:PCMflash|BitBox|CombiLoader|KESS3?|FLEX|AutoTuner|KTAG|CMDFlash|FoxFlash|Trasdata|FC200|DC706)\b')
MODES = re.compile(r'(?i)\b(?:OBD(?:2)?|BENCH|BOOT(?:MODE)?|BDM|JTAG|GPT|ISP)\b')
ACTIONS = re.compile(r'(?i)\b(?:read|write|backup|clone|checksum|чтени[ея]|запис[ьи]|клонировани[ея])\b')

def loader_leads(extracted: dict) -> dict:
    results = []
    seen = set()
    for document in extracted.get('documents', []):
        url = document.get('source_url', '')
        for candidate in document.get('candidates', []):
            excerpt = candidate.get('excerpt') or ''
            loaders = sorted({v.upper() for v in LOADERS.findall(excerpt)})
            modes = sorted({v.upper() for v in MODES.findall(excerpt)})
            actions = sorted({v.upper() for v in ACTIONS.findall(excerpt)})
            if not loaders:
                continue
            key = (url, tuple(loaders), tuple(modes), tuple(actions))
            if key in seen:
                continue
            seen.add(key)
            results.append({'source_url': url, 'loaders': loaders, 'modes': modes,
                            'operations': actions, 'excerpt': excerpt[:230],
                            'verification': 'unverified', 'requires_manual_review': True,
                            'warning': 'Mentions do not establish compatibility with specific HW/SW.'})
    return {'agent': 'loader', 'publication': 'blocked', 'leads': results[:100]}
