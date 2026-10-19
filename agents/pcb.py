"""Collect unverified PCB and test-point mentions from source excerpts."""
import re

COMPONENT = re.compile(r'(?i)\b(?:MCU|EEPROM|FLASH|CAN\s*TRANSCEIVER|ТРАНСИВЕР|ПРОЦЕССОР|МИКРОСХЕМА|КВАРЦ)\b')
TESTPOINT = re.compile(r'(?i)\b(?:TEST\s*POINT|TESTPOINT|TP[0-9]{1,3}|BOOT\s*PIN|GPT\s*PIN|ТЕСТОВАЯ\s*ТОЧКА|КОНТРОЛЬНАЯ\s*ТОЧКА)\b')
BOARD = re.compile(r'(?i)\b(?:PCB|BOARD\s*REV(?:ISION)?|ПЛАТА|РЕВИЗИЯ\s*ПЛАТЫ)\b')

def pcb_leads(extracted: dict) -> dict:
    leads = []
    seen = set()
    for doc in extracted.get('documents', []):
        url = doc.get('source_url', '')
        for candidate in doc.get('candidates', []):
            excerpt = candidate.get('excerpt') or ''
            parts = sorted({x.upper() for x in COMPONENT.findall(excerpt)})
            points = sorted({x.upper() for x in TESTPOINT.findall(excerpt)})
            board = sorted({x.upper() for x in BOARD.findall(excerpt)})
            if not (parts or points or board):
                continue
            key = (url, tuple(parts), tuple(points), tuple(board))
            if key in seen:
                continue
            seen.add(key)
            leads.append({'source_url': url, 'component_mentions': parts,
                          'testpoint_mentions': points, 'board_mentions': board,
                          'excerpt': excerpt[:230], 'verification': 'unverified',
                          'requires_manual_review': True})
    return {'agent': 'pcb', 'publication': 'blocked', 'leads': leads[:100],
            'note': 'Text mentions only; no image analysis or confirmed test-point coordinates.'}
