# Daily run procedure

The scheduled job searches for jobs; `tools/jobtool.py` (stdlib only, tests in `tools/test_jobtool.py`) decides what is
worth showing. Search judgement stays with the agent, repeatable decisions live in the tool.

## Steps

1. **Plan**: `python3 tools/jobtool.py plan --date YYYY-MM-DD` lists today's queries (core cities daily, other hubs on a
   4-day rotation, site-targeted web queries, 3 watchlist employers, extended web sweeps on Mon/Thu). Run them
   (Indeed tool for `INDEED`, WebSearch for `WEB`). Give each query an id.
2. **Collect** every plausible hit into `candidates.json` (scratch dir, not committed):
   ```json
   {"meta": {"queries": [{"id": "indeed:FR:Paris:cordiste", "q": "cordiste", "results": 10}], "notes": ""},
    "candidates": [{"title": "", "company": "", "location": "", "country": "France", "url": "",
                    "posted": "2026-10-05", "indeed_id": "JOBSEARCH_100177", "query": "indeed:FR:Paris:cordiste",
                    "level": "entry|l2|l3|cqp|unspecified", "note": "", "verified": null, "verified_by": "",
                    "relevant": null}]}
   ```
   Always fill `posted` when the source shows any date. Do not pre-filter duplicates; the tool does that.
3. **Precheck**: `python3 tools/jobtool.py precheck candidates.json --date D` prints which candidates still need work.
   Already-known and off-topic ones need nothing.
4. **Verify only those** (this is what keeps dead ads out):
   - Indeed hits: call `get_job_details(indeed_id)` in the same session. Success means the ad is live: set
     `verified: "open"`, `verified_by: "Indeed job details"`, take the exact `posted`, read the real requirements
     (IRATA / CQP / SS4 / years) into `level` and `note`, and use the **fresh URL the details call returns**.
     A repeated error is *not* proof of closure: leave `verified` null. Set `"closed"` only on explicit evidence.
   - Other sites: `process` tries an HTTP check itself when the network allows it (`jobtool.py netcheck`). It detects
     404/410, soft redirects to a listing/home page, "no longer available / expired / filled / pourvue / besetzt /
     scaduta / encerrada …" in 9 languages, and `validThrough` dates in the past. LinkedIn and many career sites
     block automated reads, which yields "unknown", never "open".
   - If the network is blocked, unverified ads are handled by policy below. Never mark `open` without evidence.
5. **Process**: `python3 tools/jobtool.py process candidates.json --date D` writes `digests/D.md`, updates
   `state/jobs.json` and `state/run_log.jsonl`. Use `--rerun` to redo a date, `--dry-run` to preview.
6. Update the README's "Latest" line, commit, push to the default branch. Check `git status` afterwards: the
   push has failed silently before.

## Rules the tool enforces

| Question | Rule |
|---|---|
| Same job? | normalised company + title + city (accents, `(m/w/d)`, `H/F`, legal suffixes, postcodes ignored). **Never the URL**: Indeed mints a new short-link on every call. |
| Shown again? | Not if shown in the last 21 days. After that, only if the ad's posting date is newer than when it was last shown (the company reposted), or it vanished from all searches for 14+ days and came back with no date to compare. An ad listed continuously is never repeated. |
| Closed then back | A job verified closed and later verified open (or posted after it closed) is shown again, tagged `REOPENED`. |
| Dead links | Verified closed: dropped. Unverified and posted over 30 days ago: dropped as probably dead. Unverified and recent or undated: shown in a separate "Could not confirm still open" section. Verified open but over 60 days old: shown with an "older ad" tag. |
| Relevance | Title must carry a rope/height-access signal (rope, IRATA, cordiste, fune, Seil, klimmer, vertical, rigging, fall protection…) unless the agent sets `relevant: true` (e.g. generic roles at Acrobatica) or `false`. |

## Tuning

`jobtool.py stats` shows per-query results vs. jobs actually shown over recent runs: drop queries that never yield,
add terms/cities where yield is high. Constants (`COOLDOWN_DAYS`, `GAP_DAYS`, `MAX_UNVERIFIED_AGE`, `OLD_AD_DAYS`)
are at the top of `tools/jobtool.py`.

## Known environment limits (as of 2026-10-11)

The cloud container's network policy blocks direct access to job sites (curl, WebFetch, Python all fail), so only the
Indeed tool and WebSearch work. Everything else shows as unverified. Allowing outbound access in the environment's
network settings would enable the HTTP checks above and direct employer feeds.

`state/seen_jobs.json` is the frozen pre-2026-10-11 archive; `state/jobs.json` is the live state.
