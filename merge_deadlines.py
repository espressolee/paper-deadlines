#!/usr/bin/env python3
"""Build one clean calendar of UPCOMING CS paper deadlines.

Source: ccfddl (https://github.com/ccfddl/ccf-deadlines) — the authoritative, community-maintained
CCF-deadlines project. This script fetches per-subfield iCal feeds, keeps upcoming deadlines only,
merges + de-dupes, cleans titles, tags CCF rank, and adds reminders. Non-CCF venues that ccfddl does
not track (e.g. CPP) are added by hand in MANUAL_EVENTS. Output: paper-deadlines.ics.

Safety: if ccfddl returns nothing (outage), the script aborts WITHOUT writing, so the last good
calendar is preserved instead of being wiped.
"""
import urllib.request, sys, re, datetime, time

# ---- config -----------------------------------------------------------------
# ccfddl subfield codes. SE = SWE + PL + systems (FSE, SANER, ICSE, ASE, ISSTA, POPL, OOPSLA, PLDI,
# ICFP); CT = theory / formal methods (CAV, LICS); plus SC DB NW AI CG.
SUBFIELDS = ["SE", "CT", "SC", "DB", "NW", "AI", "CG"]

# Optional tight allow-list: keep only these venues (by name prefix). Empty = keep all subfield venues.
# e.g. VENUE_ALLOWLIST = ["FSE", "SANER", "ICSE", "ASE", "ISSTA", "POPL", "OOPSLA", "PLDI", "ICFP", "CAV", "CPP"]
VENUE_ALLOWLIST = []

# Non-CCF venues ccfddl doesn't track. Add {name, date(YYYYMMDD), url}; keep dates from the official CFP.
MANUAL_EVENTS = [
    {"name": "CPP 2027 초록 마감", "date": "20260903", "url": "https://popl27.sigplan.org/home/CPP-2027", "rank": "-"},
    {"name": "CPP 2027 투고 마감", "date": "20260910", "url": "https://popl27.sigplan.org/home/CPP-2027", "rank": "-"},
]

ALARM_DAYS = [7, 1]           # reminders this many days before each deadline
OUT = "paper-deadlines.ics"
FEED = "https://ccfddl.com/conference/deadlines_zh_{}.ics"
TODAY = datetime.date.today().strftime("%Y%m%d")
# -----------------------------------------------------------------------------


def fetch(code, retries=3):
    url = FEED.format(code)
    for a in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "paper-deadlines-merger/3.0"})
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


def dstart(uf):
    l = field(uf, "DTSTART")
    return l.split(":")[-1][:8] if l else ""   # value is after the final ':' (handles ;TZID="..:.." )


def ccf_rank(uf):
    m = re.search(r"CCF[\s\-]?([ABC])\b", " ".join(uf))
    return m.group(1) if m else "?"


def summary_text(uf):
    l = field(uf, "SUMMARY")
    return l[len("SUMMARY:"):] if l.startswith("SUMMARY:") else l


def alarms():
    out = []
    for d in ALARM_DAYS:
        out += ["BEGIN:VALARM", "ACTION:DISPLAY", "DESCRIPTION:마감 D-%d" % d,
                "TRIGGER:-P%dD" % d, "END:VALARM"]
    return out


def emit_event(uid, date, summary, desc, url, rank):
    """Build a normalized VEVENT (date-based) with rank prefix + reminders."""
    tag = f"[CCF-{rank}] " if rank in ("A", "B", "C") else ""
    ev = ["BEGIN:VEVENT", f"UID:{uid}", f"DTSTAMP:{TODAY}T000000Z",
          f"DTSTART;VALUE=DATE:{date}", f"SUMMARY:{tag}{summary}"]
    if desc:
        ev.append("DESCRIPTION:" + desc.replace("\n", " "))
    if url:
        ev.append("URL:" + url)
    ev += alarms()
    ev.append("END:VEVENT")
    return ev


def main():
    seen, kept, ccf_n = set(), [], 0
    allow = [v.lower() for v in VENUE_ALLOWLIST]
    for c in SUBFIELDS:
        t = fetch(c)
        if not t:
            continue
        for b in vevents(t):
            uf = unfold(b)
            d, uline = dstart(uf), field(uf, "UID")
            uid = uline[len("UID:"):] if uline.startswith("UID:") else uline
            if not (d and d >= TODAY and uid and uid not in seen):
                continue
            summ = summary_text(uf).replace("截稿日期", "투고 마감").replace("摘要截稿", "초록 마감")
            if allow and not any(summ.lower().startswith(v) or (" " + v) in summ.lower() for v in allow):
                continue
            seen.add(uid)
            dl = field(uf, "DESCRIPTION")
            desc = dl[len("DESCRIPTION:"):] if dl.startswith("DESCRIPTION:") else ""
            ul = field(uf, "URL")
            url = ul[len("URL:"):] if ul.startswith("URL:") else ""
            kept.append((d, emit_event(uid, d, summ, desc, url, ccf_rank(uf))))
            ccf_n += 1

    # SAFETY: ccfddl gave nothing -> abort, keep the previous good calendar.
    if ccf_n == 0:
        print("ERROR: 0 events from ccfddl (outage?). Aborting without overwriting.", file=sys.stderr)
        sys.exit(1)

    for i, m in enumerate(MANUAL_EVENTS):
        if m["date"] < TODAY:
            continue
        uid = f"manual-noccf:{i}:{m['date']}@paper-deadlines"
        kept.append((m["date"], emit_event(uid, m["date"], m["name"],
                     f"비-CCF venue (수동). {m.get('url','')}", m.get("url", ""), m.get("rank", "-"))))

    kept.sort(key=lambda x: x[0])
    hdr = ["BEGIN:VCALENDAR", "VERSION:2.0",
           "PRODID:-//espressolee//CS Paper Deadlines//EN", "CALSCALE:GREGORIAN", "METHOD:PUBLISH",
           "X-WR-CALNAME:논문 마감 (CS)",
           "X-WR-CALDESC:ccfddl 기반 CS 논문 마감(SE/CT/SC/DB/NW/AI/CG) 병합·미래만·CCF등급·D-7/D-1 알림. 비-CCF 수동.",
           "X-WR-TIMEZONE:Asia/Seoul",
           "REFRESH-INTERVAL;VALUE=DURATION:PT12H", "X-PUBLISHED-TTL:PT12H"]
    out = hdr[:]
    for _, ev in kept:
        out += ev
    out.append("END:VCALENDAR")
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("\r\n".join(out) + "\r\n")
    print(f"wrote {OUT}: {len(kept)} upcoming ({ccf_n} ccfddl + {len(kept)-ccf_n} manual)")


if __name__ == "__main__":
    main()
