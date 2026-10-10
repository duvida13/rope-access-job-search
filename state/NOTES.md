# Notes for future daily runs

## Indeed short-links are not stable job identifiers

The `mcp__Indeed__search_jobs` tool returns `to.indeed.com/...` tracking
links. These are minted fresh on every search call — the *same* job posting
(same title, same company, same location) gets a brand-new `to.indeed.com`
URL each time it's searched for, even on the same day.

Dedup must therefore be done on **normalized (title, company)** content,
not on the raw URL, for any `to.indeed.com` link. As of 2026-10-10,
`state/seen_jobs.json` had 3358 URL entries but only ~2264 unique
title+company combinations — roughly a third of recorded "new" postings in
past digests were likely the same handful of recurring Indeed listings
(e.g. "Pedreiros e Pintores de Alturas..." / Solução Futuro, Lisboa — seen
under 9+ different to.indeed.com URLs since 2026-09-21) being re-reported
as new because the URL looked different.

Non-Indeed sources (InfoJobs, OLX, StepStone, VDAB, company career sites,
jobindex.dk, etc.) give stable, reusable URLs — plain URL dedup is fine for
those.

**Recommended check before writing a day's digest:** for every candidate
with a `to.indeed.com` URL, normalize `title` and `company` (lowercase,
strip punctuation) and check against the same normalized keys already in
`seen_jobs.json`, not just the URL set.
