"""Extract unverified ECU connector-pin leads from already fetched source excerpts.

Never assign pins without an explicit pin number, function, source, and HW reference.
"""
import re

PIN = re.compile(r'(?i)\\b(?:connector|разъ[её]м|plug)\\s*([A-Z0-9]{1,5})?\\s*[,;:]?\\s*(?:pin|пин|контакт)\\s*(\\d{1,3})\\b')
FUNCTION = re.compile(r'(?i)\\b(?:CAN[- ]?[HL]|K[- ]?line|LIN|GND|ground|масса|питание|VBAT|KL30|KL15|5\\s?V|12\\s?V|датчик[а-я ]{0,24})\\b')
HW = re.compile(r'(?i)\\b(?:HW|hardware|аппаратн(?:ый|ая)\\s+номер)\\s*[:#-]?\\s*([A-Z0-9.-]{5,30})\\b')

def pinout_leads(extracted: dict) -> dict:
    leads = []
    seen = set()
    for doc in extracted.get('documents', []):
        url = doc.get('source_url', '')
        for candidate in doc.get('candidates', []):
            excerpt = candidate.get('excerpt') or ''
            hw = HW.search(excerpt)
            if not hw:
                continue
            for match in PIN.finditer(excerpt):
                nearby = excerpt[max(0, match.start()-50):min(len(excerpt), match.end()+80)]
                signal = FUNCTION.search(nearby)
                if not signal:
                    continue
                key = (url, hw.group(1).upper(), match.group(1) or '', match.group(2), signal.group(0).upper())
                if key in seen:
                    continue
                seen.add(key)
                leads.append({'source_url': url, 'hardware_reference': hw.group(1),
                              'connector': match.group(1), 'pin': int(match.group(2)),
                              'signal_text': signal.group(0), 'excerpt': excerpt[:230],
                              'verification': 'unverified', 'requires_manual_review': True})
    return {'agent': 'pinout', 'publication': 'blocked', 'leads': leads[:100],
            'note': 'Text leads only: confirm connector orientation, HW revision and original diagram.'}
