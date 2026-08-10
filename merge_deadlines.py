#!/usr/bin/env python3
"""Build one calendar of UPCOMING CS paper deadlines from ccfddl (the authoritative,
community-maintained CCF-deadlines project), merged across chosen subfields, de-duped,
future-only, with cleaned titles. Non-CCF venues that ccfddl does not track are added
manually via MANUAL_EVENTS. Output: paper-deadlines.ics."""
import urllib.request, sys, datetime

# ccfddl subfield codes. SE = 软件工程/系统软件/程序设计语言 (SWE + PL + systems: FSE, SANER, ICSE,
# ASE, ISSTA, POPL, OOPSLA, PLDI, ICFP). CT = 理论 (CAV, LICS, ...). Others: SC DB NW AI CG.
SUBFIELDS = ["SE", "CT", "SC", "DB", "NW", "AI", "CG"]
FEED = "https://ccfddl.com/conference/deadlines_zh_{}.ics"

# Venues ccfddl does NOT track (non-CCF). Add {name,date(YYYYMMDD),url}; edit dates from official CFP.
MANUAL_EVENTS = [
    {"name": "CPP 2027 초록 마감", "date": "20260903", "url": "https://popl27.sigplan.org/home/CPP-2027"},
    {"name": "CPP 2027 투고 마감", "date": "20260910", "url": "https://popl27.sigplan.org/home/CPP-2027"},
]

OUT = "paper-deadlines.ics"
TODAY = datetime.date.today().strftime("%Y%m%d")


def fetch(code):
    url = FEED.format(code)
    req = urllib.request.Request(url, headers={"User-Agent": "paper-deadlines-merger/2.0"})
    with urllib.request.urlopen(req, timeout=40) as r:
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
    return next((l for l in uf if l.startswith(key)), "")


def clean_block(block):
    """Chinese -> Korean in SUMMARY only (titles like 'POPL 2027 截稿日期 [..]')."""
    out = []
    for ln in block:
        if ln.startswith("SUMMARY"):
            ln = ln.replace("截稿日期", "투고 마감").replace("摘要截稿", "초록 마감")
        out.append(ln)
    return out


def dtstart(uf):
    for l in uf:
        if l.startswith("DTSTART"):
            return l.split(":")[-1][:8]
    return ""


def main():
    seen, kept = set(), []  # kept: (date, cleaned_block)
    for c in SUBFIELDS:
        try:
            t = fetch(c)
        except Exception as e:
            print(f"warn: {c} fetch failed: {e}", file=sys.stderr)
            continue
        for b in vevents(t):
            uf = unfold(b)
            d = dtstart(uf)
            uid = field(uf, "UID")
            if d and d >= TODAY and uid and uid not in seen:  # future only, dedup
                seen.add(uid)
                kept.append((d, clean_block(b)))

    # manual non-CCF venues
    for i, m in enumerate(MANUAL_EVENTS):
        d = m["date"]
        if d < TODAY:
            continue
        blk = ["BEGIN:VEVENT",
               f"UID:manual-noccf:{i}:{d}@paper-deadlines",
               f"DTSTAMP:{TODAY}T000000Z",
               f"DTSTART;VALUE=DATE:{d}",
               f"SUMMARY:{m['name']}",
               f"DESCRIPTION:비-CCF venue (수동 추가). 출처: {m.get('url','')}",
               f"URL:{m.get('url','')}",
               "END:VEVENT"]
        kept.append((d, blk))

    kept.sort(key=lambda x: x[0])
    hdr = [
        "BEGIN:VCALENDAR", "VERSION:2.0",
        "PRODID:-//espressolee//CS Paper Deadlines//EN",
        "CALSCALE:GREGORIAN", "METHOD:PUBLISH",
        "X-WR-CALNAME:논문 마감 (CS)",
        "X-WR-CALDESC:ccfddl 기반 CS 논문 마감(SE/CT/SC/DB/NW/AI/CG) 병합, 미래만. 비-CCF는 수동.",
        "X-WR-TIMEZONE:Asia/Seoul",
        "REFRESH-INTERVAL;VALUE=DURATION:PT12H", "X-PUBLISHED-TTL:PT12H",
    ]
    out = hdr[:]
    for _, b in kept:
        out += b
    out.append("END:VCALENDAR")
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("\r\n".join(out) + "\r\n")
    print(f"wrote {OUT}: {len(kept)} upcoming events ({len(SUBFIELDS)} ccfddl subfields + {len(MANUAL_EVENTS)} manual)")


if __name__ == "__main__":
    main()
