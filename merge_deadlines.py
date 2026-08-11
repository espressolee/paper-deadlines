#!/usr/bin/env python3
"""Build one clean calendar of UPCOMING CS paper deadlines.

Source: ccfddl (https://github.com/ccfddl/ccf-deadlines), the authoritative community CCF-deadlines
project. Per-subfield iCal feeds are fetched, upcoming deadlines are kept, merged + de-duped by UID,
tagged with CCF rank, and given D-7 / D-1 reminders. Original VEVENT blocks are passed through with
minimal surgical edits (so the source's DTSTART/TZID, TEXT escaping and line folding are preserved).
Non-CCF venues ccfddl doesn't track (e.g. CPP) are added via MANUAL_EVENTS.

Reliability (fail-closed): if ANY required subfield feed fails, the script aborts WITHOUT writing, so
the previous good calendar is preserved rather than silently publishing a partial (deleted-looking) one.
"""
import urllib.request, sys, re, datetime, time

# ---- config -----------------------------------------------------------------
SUBFIELDS = ["SE", "CT", "SC", "DB", "NW", "AI", "CG"]   # ccfddl codes; SE = SWE+PL+systems
VENUE_ALLOWLIST = []   # e.g. ["FSE","SANER","POPL","CPP"]; empty = keep all subfield venues
MANUAL_EVENTS = [      # non-CCF venues (name / YYYYMMDD / url); keep dates from the official CFP
    {"name": "CPP 2027 초록 마감", "date": "20260903", "url": "https://popl27.sigplan.org/home/CPP-2027"},
    {"name": "CPP 2027 투고 마감", "date": "20260910", "url": "https://popl27.sigplan.org/home/CPP-2027"},
]
ALARM_DAYS = [7, 1]
OUT = "paper-deadlines.ics"
FEED = "https://ccfddl.com/conference/deadlines_zh_{}.ics"
KST = datetime.timezone(datetime.timedelta(hours=9))
TODAY = datetime.datetime.now(KST).date()
CUTOFF = (TODAY - datetime.timedelta(days=1)).strftime("%Y%m%d")   # 1-day grace (AoE/TZ)
NOW_UTC = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
# -----------------------------------------------------------------------------


def fetch(code, retries=3):
    url = FEED.format(code)
    for a in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "paper-deadlines-merger/4.0"})
            with urllib.request.urlopen(req, timeout=40) as r:
                return r.read().decode("utf-8")
        except Exception as e:
            if a == retries - 1:
                print(f"warn: {code} failed after {retries} tries: {e}", file=sys.stderr)
                return None
            time.sleep(2 * (a + 1))


def vevents(text):
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    blocks, cur = [], None
    for ln in lines:
        u = ln.upper()
        if u == "BEGIN:VEVENT":
            cur = [ln]
        elif u == "END:VEVENT":
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


def prop(uf, name):
    """Value of a property, matching name before ';' or ':' (case-insensitive, ignores params)."""
    name = name.upper()
    for l in uf:
        head = l.split(":", 1)[0].split(";", 1)[0].upper()
        if head == name:
            return l.split(":", 1)[1] if ":" in l else ""
    return ""


def date_of(uf):
    l = next((x for x in uf if x.split(":", 1)[0].split(";", 1)[0].upper() == "DTSTART"), "")
    return l.split(":")[-1][:8] if l else ""


def esc(t):
    return t.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n")


def fold(line):
    """Fold a content line at <=75 octets (UTF-8 safe), continuation lines start with a space."""
    b = line.encode("utf-8")
    if len(b) <= 75:
        return [line]
    out, cur = [], b""
    first = True
    for ch in line:
        cb = ch.encode("utf-8")
        limit = 75 if first else 74  # continuation reserves 1 octet for leading space
        if len(cur) + len(cb) > limit:
            out.append((cur if first else b" " + cur).decode("utf-8")); cur = b""; first = False
        cur += cb
    if cur:
        out.append((cur if first else b" " + cur).decode("utf-8"))
    return out


def alarms():
    out = []
    for d in ALARM_DAYS:
        out += ["BEGIN:VALARM", "ACTION:DISPLAY", f"DESCRIPTION:마감 D-{d}", f"TRIGGER:-P{d}D", "END:VALARM"]
    return out


def transform(block, rank):
    """Pass through the original (folded) block; only edit SUMMARY (rank tag + zh->ko) and inject alarms."""
    out = []
    for ln in block:
        if ln.upper() == "END:VEVENT":
            out += alarms(); out.append("END:VEVENT"); continue
        head = ln.split(":", 1)[0].split(";", 1)[0].upper()
        if head == "SUMMARY" and ":" in ln:
            pre, val = ln.split(":", 1)
            val = val.replace("截稿日期", "투고 마감").replace("摘要截稿", "초록 마감")
            tag = f"[CCF-{rank}] " if rank in ("A", "B", "C") else ""
            out += fold(f"{pre}:{tag}{val}")
        else:
            out.append(ln)   # DTSTART/TZID, DESCRIPTION(already folded+escaped), UID, URL: verbatim
    return out


def ccf_rank(uf):
    m = re.search(r"CCF[\s\-]?([ABC])\b", prop(uf, "DESCRIPTION"))
    return m.group(1) if m else "?"


def manual_event(m):
    uid = "manual:" + re.sub(r"[^A-Za-z0-9]", "", m["name"]) + ":" + m["date"] + "@paper-deadlines"
    ev = ["BEGIN:VEVENT", f"UID:{uid}", f"DTSTAMP:{NOW_UTC}", f"DTSTART;VALUE=DATE:{m['date']}"]
    ev += fold("SUMMARY:" + esc(m["name"]))
    ev += fold("DESCRIPTION:" + esc(f"비-CCF venue (수동 추가). {m.get('url','')}"))
    if m.get("url"):
        ev += fold("URL:" + m["url"])
    ev += alarms(); ev.append("END:VEVENT")
    return ev


def main():
    feeds, failed = {}, []
    for c in SUBFIELDS:
        t = fetch(c)
        (feeds.__setitem__(c, t) if t else failed.append(c))
    if failed:   # fail-closed: never publish a partial calendar
        print(f"ERROR: feeds failed {failed}; aborting without overwriting.", file=sys.stderr)
        sys.exit(1)

    seen, kept, allow = set(), [], [v.lower() for v in VENUE_ALLOWLIST]
    for c in SUBFIELDS:
        for b in vevents(feeds[c]):
            uf = unfold(b)
            d, uline = date_of(uf), prop(uf, "UID")
            if not (d and d >= CUTOFF and uline and uline not in seen):
                continue
            summ = prop(uf, "SUMMARY").replace("截稿日期", "").replace("摘要截稿", "").lower()
            if allow and not any(re.search(r"(?<![a-z0-9])" + re.escape(v) + r"(?![a-z0-9])", summ) for v in allow):
                continue
            seen.add(uline)
            kept.append((d, transform(b, ccf_rank(uf))))

    for m in MANUAL_EVENTS:
        if m["date"] >= CUTOFF:
            kept.append((m["date"], manual_event(m)))

    kept.sort(key=lambda x: x[0])
    hdr = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//espressolee//CS Paper Deadlines//EN",
           "CALSCALE:GREGORIAN", "METHOD:PUBLISH", "X-WR-CALNAME:논문 마감 (CS)",
           "X-WR-CALDESC:ccfddl CS paper deadlines (SE/CT/SC/DB/NW/AI/CG), upcoming, CCF-tagged, D-7/D-1. non-CCF manual.",
           "X-WR-TIMEZONE:Asia/Seoul", "REFRESH-INTERVAL;VALUE=DURATION:PT12H", "X-PUBLISHED-TTL:PT12H"]
    out = hdr[:]
    for _, ev in kept:
        out += ev
    out.append("END:VCALENDAR")
    with open(OUT, "w", encoding="utf-8", newline="") as f:
        f.write("\r\n".join(out) + "\r\n")
    print(f"wrote {OUT}: {len(kept)} upcoming ({len(kept)-sum(1 for _ in MANUAL_EVENTS if _['date']>=CUTOFF)} ccfddl + manual)")


if __name__ == "__main__":
    main()
