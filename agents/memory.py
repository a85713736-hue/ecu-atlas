"""Collect source-backed MCU and memory leads without inferring capacities."""
import re

CHIP = re.compile(r'(?i)\b(?:TC2[0-9]{2}[A-Z0-9-]*|TC3[0-9]{2}[A-Z0-9-]*|SPC5[A-Z0-9]{3,12}|MPC5[A-Z0-9]{3,12}|SH70[0-9]{2}|ST10F[0-9A-Z]+|C16[0-9A-Z]+)\b')
MEMORY = re.compile(r'(?i)\b(?:EEPROM|D-?FLASH|P-?FLASH|NOR\s+FLASH|NAND\s+FLASH|EMMC|INTERNAL\s+FLASH|EXTERNAL\s+FLASH)\b')
SIZE = re.compile(r'(?i)\b(?:[0-9]+(?:[.,][0-9]+)?\s*(?:K|M|G)(?:B|BYTE|BIT))\b')

def memory_leads(extracted: dict) -> dict:
    results = []
    seen = set()
    for document in extracted.get('documents', []):
        source = document.get('source_url', '')
        for candidate in document.get('candidates', []):
            excerpt = candidate.get('excerpt') or ''
            chips = sorted(set(CHIP.findall(excerpt)))
            memories = sorted(set(MEMORY.findall(excerpt)), key=str.upper)
            sizes = sorted(set(SIZE.findall(excerpt)))
            if not chips and not memories:
                continue
            key = (source, tuple(chips), tuple(memories), tuple(sizes))
            if key in seen:
                continue
            seen.add(key)
            results.append({'source_url': source, 'mcu_mentions': chips,
                            'memory_mentions': memories, 'size_mentions': sizes,
                            'excerpt': excerpt[:230], 'verification': 'unverified',
                            'requires_manual_review': True,
                            'warning': 'Sizes and memory types are co-mentioned, not proven to belong to the MCU.'})
    return {'agent': 'memory', 'publication': 'blocked', 'leads': results[:100]}
