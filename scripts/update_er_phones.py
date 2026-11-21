#!/usr/bin/env python3
"""Conservative monthly check for explicitly labeled emergency-room direct numbers."""
import html
import pathlib
import re
import urllib.request
from urllib.parse import urlparse

ROOT = pathlib.Path(__file__).resolve().parents[1]
INDEX = ROOT / "index.html"
PHONE = re.compile(r"(?<!\d)(?:0\d{1,2}[-.\s]?)?\d{3,4}[-.\s]?\d{4}(?!\d)")
LABEL = re.compile(r"응급실\s*(?:직통|직접|전화번호|연락처|전화)\s*[:：]?\s*", re.I)
ROW = re.compile(r"\{d:'[^']+',n:'(?P<name>[^']+)',a:'[^']+',rep:'(?P<rep>[^']+)',er:'(?P<er>[^']*)',source:'(?P<source>[^']+)'\}")
# Explicit hospital-owned pages only; third-party sources are excluded.
ALLOWED = {
    "서울특별시 서남병원": {"www.seoulnamhospital.or.kr"},
    "한강수병원": {"www.hangangsoo.co.kr"},
    "명지성모병원": {"www.myongji-sm.co.kr"},
    "대림성모병원": {"www.drh.co.kr"},
}

def normalize(number):
    digits = re.sub(r"\D", "", number)
    if digits.startswith("02") and len(digits) in (9, 10):
        return "02-" + digits[2:-4] + "-" + digits[-4:]
    if digits.startswith("0") and len(digits) in (10, 11):
        return digits[:3] + "-" + digits[3:-4] + "-" + digits[-4:]
    return None

def lookup(url, name, representative):
    host = (urlparse(url).hostname or "").lower()
    if host not in ALLOWED[name] or urlparse(url).scheme != "https":
        return None
    request = urllib.request.Request(url, headers={"User-Agent": "EmergencyHospitalContactAudit/1.0"})
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            if response.geturl().split("/")[2].lower() not in ALLOWED[name]:
                return None
            raw = response.read(1500000)
            charset = response.headers.get_content_charset() or "utf-8"
            page = raw.decode(charset, errors="replace")
    except Exception as exc:
        print(f"{name}: unable to check official page ({type(exc).__name__})")
        return None
    # Preserve tag boundaries as spaces to avoid joining unrelated table cells.
    plain = html.unescape(re.sub(r"<[^>]*>", " ", re.sub(r"(?is)<(script|style)\b.*?</\1>", " ", page)))
    plain = re.sub(r"\s+", " ", plain)
    matches = set()
    for label in LABEL.finditer(plain):
        # Only numbers immediately after an explicit direct-contact label.
        snippet = plain[label.end():label.end()+28]
        hit = PHONE.match(snippet.lstrip())
        if hit:
            candidate = normalize(hit.group())
            if candidate and re.sub(r"\D", "", candidate) != re.sub(r"\D", "", representative):
                matches.add(candidate)
    return next(iter(matches)) if len(matches) == 1 else None

def main():
    original = INDEX.read_text(encoding="utf-8")
    updated = original
    for row in ROW.finditer(original):
        name, number = row.group("name"), row.group("er")
        if name not in ALLOWED or number:
            continue
        found = lookup(row.group("source"), name, row.group("rep"))
        if not found:
            print(f"{name}: no unambiguous official direct number; unchanged")
            continue
        old = row.group(0)
        new = old.replace("er:''", "er:'" + found + "'", 1)
        updated = updated.replace(old, new, 1)
        print(f"{name}: verified direct number added: {found}")
    if updated != original:
        INDEX.write_text(updated, encoding="utf-8")
    else:
        print("No verified changes")

if __name__ == "__main__":
    main()
