# Daily job-search runs

For the scheduled "Daily EU Rope Access Job Search" run, follow `docs/PROCESS.md`. It supersedes steps 2, 4 and 6 of the
scheduled prompt:

- Do not read or write `state/seen_jobs.json` (frozen archive). State lives in `state/jobs.json`, managed only by
  `tools/jobtool.py`.
- Never dedupe by URL. Indeed issues a new short-link on every call. `jobtool.py precheck/process` match jobs by
  company + title + city and decide what is new, re-posted or reopened.
- Never mark a posting verified `open` without evidence (Indeed `get_job_details` success, or an HTTP check by the tool).
- Run the plan from `jobtool.py plan`, and verify only what `precheck` lists.
- After pushing, confirm with `git status` that `main` matches `origin/main`. Report any push or tool failure in the
  final message instead of finishing silently.
- Run `python3 tools/test_jobtool.py` after any change to `tools/`.
