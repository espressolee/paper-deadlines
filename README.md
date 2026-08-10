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

Security · Databases · Computer Systems · Graphics & Vision · Networks · Artificial Intelligence ·
Software Engineering · Mathematics & Statistics

## ⚙️ How it works

`merge_deadlines.py` fetches the per-field iCal feeds from **[labmate.cloud](https://labmate.cloud/ko/conferences)**
(codes `SC DB DS CG NW AI SE MATH`), keeps only submission-deadline events, merges + de-dupes by UID, and
writes `paper-deadlines.ics`. A scheduled GitHub Action (`.github/workflows/update.yml`) regenerates and
commits it every 12 h.

**Customize:** edit the `CODES` list in `merge_deadlines.py` (get a field's code by filtering on the
labmate page and clicking *Copy calendar feed URL*).

## 🙏 Data source & credits

Deadline data comes from **[labmate.cloud](https://labmate.cloud)**, which itself builds on the
community-maintained **[ccfddl / ccf-deadlines](https://github.com/ccfddl/ccf-deadlines)** project. This repo
only **filters and merges** those public feeds into a single calendar — all credit for the underlying data
goes to those projects.

## ⚠️ Disclaimer

Unofficial and provided as-is. Deadlines, timezones, and rounds change — always confirm against the
conference's official Call for Papers before relying on a date.

## 📄 License

[MIT](LICENSE) — code only. Deadline data belongs to its respective upstream sources.
