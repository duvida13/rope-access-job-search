# Updated scheduled-routine prompt (optional paste)

The repo's `CLAUDE.md` already redirects the daily run to `docs/PROCESS.md`, so the routine works with its old prompt.
For a cleaner setup, replace "YOUR JOB THIS RUN" and "NOTES" in the routine prompt
(https://claude.ai/code/routines/trig_01DUGoFPDzPfR4PEuXgZu2wz) with the text below. Keep the profile, terms and country
paragraphs as they are.

```
YOUR JOB THIS RUN:
You are running inside a clone of the target git repo. FIRST read docs/PROCESS.md and follow it exactly: it is the
runbook for this job. In short: run `python3 tools/jobtool.py plan --date <today>` and execute those searches; collect
candidates (title, company, location, country, direct link, posting date, requirement level, one-line note) into a
scratch candidates.json; run `jobtool.py precheck`; verify ONLY the candidates it lists (Indeed: call get_job_details
and read the real requirements; other sites: the tool does HTTP checks when the network allows); run `jobtool.py
process` to write digests/<today>.md and update state/jobs.json; update README.md's 'Latest: digests/<today>.md' line;
commit ('Daily digest YYYY-MM-DD: N new postings') and push to the default branch, then confirm with git status that
the push really succeeded.

The tool decides what counts as new, so do NOT dedupe by URL yourself (Indeed gives a fresh link on every call), do NOT
edit state/seen_jobs.json (frozen archive), and never mark a posting 'open' without real evidence. A posting shown
before is shown again only if the tool says it was re-posted or reopened.

NOTES:
- Some career sites block automated fetching or are unreachable from the cloud environment. That is expected: such
  postings land in the digest's 'could not confirm still open' section or are dropped by policy. Do not fail the run.
- Only include postings backed by a real link. Never fabricate a posting, company or detail.
- If the push fails, or the searches/tools are broken, say so clearly in your final message instead of finishing silently.
- Keep the digest concise and scannable; Luis reviews it himself by opening the repo.
```
