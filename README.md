# 📅 CS Paper Deadlines — Calendar Feed

[![update-deadlines](https://github.com/espressolee/paper-deadlines/actions/workflows/update.yml/badge.svg)](https://github.com/espressolee/paper-deadlines/actions/workflows/update.yml)
![last commit](https://img.shields.io/github/last-commit/espressolee/paper-deadlines?label=last%20updated)

An **auto-updating calendar feed** of upcoming **paper submission deadlines** across 8 computer-science
fields, ready to subscribe in Apple / Google / Outlook Calendar. Refreshed every 12 hours by GitHub Actions.

> Only *submission deadlines* are kept (venue/held events are filtered out), merged across fields and
> de-duplicated, so your calendar stays clean.

## 🔔 Subscribe

Paste this URL into your calendar app's **"Subscribe by URL"** entry:

```
https://raw.githubusercontent.com/espressolee/paper-deadlines/main/paper-deadlines.ics
```

- **Apple Calendar** — Calendar → File → New Calendar Subscription… → paste URL → set auto-refresh to *Daily*.
  (Or open `webcal://raw.githubusercontent.com/espressolee/paper-deadlines/main/paper-deadlines.ics` in Safari.)
- **Google Calendar** — Other calendars → From URL → paste URL.
- **Outlook** — Add calendar → Subscribe from web → paste URL.

## 📚 Fields covered

Software Engineering / PL / Systems · Theory & Formal Methods · Security · Databases · Networks ·
Artificial Intelligence · Graphics & Vision
(ccfddl subfields `SE CT SC DB NW AI CG` — SE bundles SWE, programming languages and systems:
FSE, SANER, ICSE, ASE, ISSTA, POPL, OOPSLA, PLDI, ICFP; CT covers CAV, LICS, …)

## ⚙️ How it works

`merge_deadlines.py` fetches the per-subfield iCal feeds from **[ccfddl](https://ccfddl.com)** (the
authoritative CCF-deadlines project), keeps **upcoming** deadlines only, merges + de-dupes by UID, cleans
titles, and writes `paper-deadlines.ics`. **Non-CCF venues** that ccfddl doesn't track (e.g. **CPP —
Certified Programs and Proofs**) are added by hand in the `MANUAL_EVENTS` list. A scheduled GitHub Action
(`.github/workflows/update.yml`) regenerates and commits it every 12 h.

**Customize:** edit `SUBFIELDS` (ccfddl codes) or add a venue to `MANUAL_EVENTS` (name + `YYYYMMDD` date +
url from the official CFP) in `merge_deadlines.py`.

## 🙏 Data source & credits

CCF-ranked deadline data comes from the community-maintained
**[ccfddl / ccf-deadlines](https://github.com/ccfddl/ccf-deadlines)** project. This repo only **filters,
merges, and cleans** those public feeds (plus a few hand-added non-CCF venues) into a single calendar —
all credit for the underlying data goes to ccfddl and the venues' organizers.

## ⚠️ Disclaimer

Unofficial and provided as-is. Deadlines, timezones, and rounds change — always confirm against the
conference's official Call for Papers before relying on a date.

## 📄 License

[MIT](LICENSE) — code only. Deadline data belongs to its respective upstream sources.
