#!/usr/bin/env python3
"""Fetch CS paper submission deadlines from labmate.cloud per-field ICS feeds,
keep only '투고 마감' (submission deadline) events across the chosen fields,
merge + dedup by UID, write one calendar (paper-deadlines.ics)."""
import urllib.request, sys

CODES = ["SC", "DB", "DS", "CG", "NW", "AI", "SE", "MATH"]  # 보안 DB 시스템 그래픽스비전 네트워크 AI SW수학
BASE = "https://api.labmate.cloud/api/conferences/calendar.ics"
FILTER = "투고 마감"
OUT = "paper-deadlines.ics"


def fetch(code):
    url = f"{BASE}?sub={code}"
    req = urllib.request.Request(url, headers={"User-Agent": "paper-deadlines-merger/1.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8")


def vevents(text):
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    blocks, cur = [], None
    for ln in lines:
        if ln == "BEGIN:VEVENT":
            cur = [ln]
        elif ln == "END:VEVENT":
            if cur is not None:
                cur.append(ln); blocks.append(cur); cur = None
        elif cur is not None:
            cur.append(ln)
    return blocks


def unfold(block):
    out = []
    for ln in block:
        if out and ln[:1] in (" ", "\t"):
            out[-1] += ln[1:]
        else:
            out.append(ln)
    return out


def field(uf, key):
    for l in uf:
        if l.startswith(key):
            return l
    return ""


def main():
    seen, kept = set(), []
    for c in CODES:
        try:
            t = fetch(c)
        except Exception as e:
            print(f"warn: {c} fetch failed: {e}", file=sys.stderr)
            continue
        for b in vevents(t):
            uf = unfold(b)
            summ = field(uf, "SUMMARY")
            uid = field(uf, "UID")
            if FILTER in summ and uid and uid not in seen:
                seen.add(uid)
                kept.append(b)  # keep RAW (folded) block for fidelity

    def dtstart(b):
        for l in unfold(b):
            if l.startswith("DTSTART"):
                return l.split(":")[-1][:8]
        return "99999999"

    kept.sort(key=dtstart)
    hdr = [
        "BEGIN:VCALENDAR", "VERSION:2.0",
        "PRODID:-//espressolee//CS Paper Deadlines//KO",
        "CALSCALE:GREGORIAN", "METHOD:PUBLISH",
        "X-WR-CALNAME:논문 마감 (CS)",
        "X-WR-CALDESC:labmate.cloud 8개 분야(SC/DB/DS/CG/NW/AI/SE/MATH) 투고 마감 병합",
        "X-WR-TIMEZONE:Asia/Seoul",
        "REFRESH-INTERVAL;VALUE=DURATION:PT12H", "X-PUBLISHED-TTL:PT12H",
    ]
    out = hdr[:]
    for b in kept:
        out += b
    out.append("END:VCALENDAR")
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("\r\n".join(out) + "\r\n")
    print(f"wrote {OUT}: {len(kept)} deadline events from {len(CODES)} fields")


if __name__ == "__main__":
    main()
