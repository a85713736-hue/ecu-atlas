"""Fetch public ECU research pages and extract *candidate* identifiers.

No LLM guesses, no ECU power/wiring instructions, no auto-publication.
Usage: python agents/extract.py research/out/latest.json --output research/out/extracted.json
"""
import argparse
import html
from html.parser import HTMLParser
import ipaddress
import json
from pathlib import Path
import re
import socket
import urllib.parse
import urllib.request

PATTERNS = {
    "bosch_part_number": r"\b(?:0\s*261\s*[A-Z0-9]{5,9}|F\s*0\s*1\s*R\s*[A-Z0-9]{5,10})\b",
    "mcu": r"\b(?:TC2(?:7[0-9]|9[0-9])[A-Z0-9]*|SPC5[0-9A-Z]{3,12}|MPC5[0-9A-Z]{3,12}|SH70[0-9]{2})\b",
    "memory": r"\b(?:EEPROM|D-?FLASH|P-?FLASH|NOR\s+FLASH|NAND\s+FLASH|EMMC)\b",
    "loader": r"\b(?:PCMflash|BitBox|CombiLoader|KESS3?|FLEX|AutoTuner)\b",
    "mode": r"\b(?:OBD|Bench|Boot|BDM|JTAG|GPT)\b",
}
MAX_BYTES = 1_000_000
MAX_URLS = 30

class TextParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []
        self.skip = 0
    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style", "noscript"):
            self.skip += 1
    def handle_endtag(self, tag):
        if tag in ("script", "style", "noscript") and self.skip:
            self.skip -= 1
    def handle_data(self, data):
        if not self.skip:
            self.parts.append(data)

def safe_url(url):
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
        return False
    if parsed.port not in (None, 443):
        return False
    host = parsed.hostname.lower()
    if host == "localhost" or host.endswith((".local", ".internal")):
        return False
    try:
        addresses = socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)
        return bool(addresses) and all(
            ipaddress.ip_address(address[4][0]).is_global for address in addresses
        )
    except (OSError, ValueError):
        return False

class SafeRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if not safe_url(newurl):
            raise ValueError("Unsafe redirect")
        return super().redirect_request(req, fp, code, msg, headers, newurl)

def fetch(url):
    if not safe_url(url):
        raise ValueError("URL is not a public HTTPS endpoint")
    req = urllib.request.Request(url, headers={
        "User-Agent": "ECUAtlasResearcher/0.3 (+public documentation)",
        "Accept": "text/html,text/plain",
    })
    opener = urllib.request.build_opener(SafeRedirect)
    with opener.open(req, timeout=12) as response:
        if response.headers.get_content_type() not in ("text/html", "text/plain"):
            raise ValueError("Unsupported content type")
        raw = response.read(MAX_BYTES + 1)
        if len(raw) > MAX_BYTES:
            raise ValueError("Document exceeds size limit")
        charset = response.headers.get_content_charset() or "utf-8"
        source = raw.decode(charset, errors="replace")
        if response.headers.get_content_type() == "text/plain":
            return source
        parser = TextParser()
        parser.feed(source)
        return html.unescape(" ".join(parser.parts))

def candidates(text):
    output = []
    for category, expression in PATTERNS.items():
        matches = list(re.finditer(expression, text, flags=re.I))
        seen = set()
        for match in matches:
            value = match.group(0).strip()
            if value.casefold() in seen:
                continue
            seen.add(value.casefold())
            context = re.sub(r"\s+", " ", text[max(0, match.start()-90):match.end()+90])
            output.append({
                "category": category,
                "value": value,
                "excerpt": context[:230],
                "verification": "unverified",
                "hardware_revision": None,
            })
            if len(seen) >= 25:
                break
    return output

def extract(document):
    findings = []
    errors = []
    seen = set()
    for category, section in document.get("sections", {}).items():
        for item in section.get("results", []):
            url = item.get("url", "")
            if url in seen:
                continue
            seen.add(url)
            if len(seen) > MAX_URLS:
                break
            try:
                body = fetch(url)
                if document.get("ecu", "").split()[-1].upper() not in body.upper():
                    errors.append({"source_url": url, "error": "ECU identifier not found in page"})
                    continue
                findings.append({"source_url": url, "search_category": category,
                                 "candidates": candidates(body), "review_required": True})
            except Exception as exc:
                errors.append({"source_url": url, "error": str(exc)})
    return {"ecu": document.get("ecu"), "publication": "blocked",
            "status": "requires_source_verification", "documents": findings, "errors": errors}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input")
    parser.add_argument("--output", default="research/out/extracted.json")
    args = parser.parse_args()
    result = extract(json.loads(Path(args.input).read_text(encoding="utf-8")))
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Extracted candidate identifiers from {len(result['documents'])} pages; {len(result['errors'])} fetch errors")

if __name__ == "__main__":
    main()
