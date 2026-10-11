#!/usr/bin/env python3
"""State machine for the daily rope-access job digest.

Subcommands: plan, migrate, precheck, process, check, netcheck, stats.
See docs/PROCESS.md for the daily runbook. Standard library only.
"""
import argparse
import collections
import datetime as dt
import hashlib
import json
import os
import re
import socket
import sys
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
JOBS_FILE = ROOT / "state" / "jobs.json"
SEEN_LEGACY = ROOT / "state" / "seen_jobs.json"
PLAN_FILE = ROOT / "state" / "search_plan.json"
RUN_LOG = ROOT / "state" / "run_log.jsonl"
DIGEST_DIR = ROOT / "digests"

COOLDOWN_DAYS = 21       # never re-show the same job within this many days of showing it
GAP_DAYS = 14            # absent from every search this long, then seen again => treated as re-posted
MAX_UNVERIFIED_AGE = 30  # unconfirmed ads older than this are dropped as probably dead
OLD_AD_DAYS = 60         # confirmed-open ads older than this get an "older ad" tag

COUNTRY_ORDER = ["Portugal", "United Kingdom", "Ireland", "Netherlands", "Belgium", "Germany",
                 "Switzerland", "Norway", "Denmark", "Spain", "France", "Italy"]
COUNTRY_ALIASES = {"uk": "United Kingdom", "gb": "United Kingdom", "england": "United Kingdom",
                   "scotland": "United Kingdom", "wales": "United Kingdom", "great britain": "United Kingdom",
                   "northern ireland": "United Kingdom", "deutschland": "Germany", "espana": "Spain",
                   "españa": "Spain", "nederland": "Netherlands", "belgie": "Belgium",
                   "belgique": "Belgium", "schweiz": "Switzerland", "suisse": "Switzerland",
                   "norge": "Norway", "danmark": "Denmark", "italia": "Italy", "irlanda": "Ireland",
                   "ie": "Ireland", "pt": "Portugal", "nl": "Netherlands", "be": "Belgium",
                   "de": "Germany", "ch": "Switzerland", "no": "Norway", "dk": "Denmark",
                   "es": "Spain", "fr": "France", "it": "Italy"}

# ---------------------------------------------------------------- normalisation

GENDER_RE = re.compile(r"\(?\s*\b[mfhwdx]\s*/\s*[mfhwdx](?:\s*/\s*[mfhwdx])?\s*\)?")
COMPANY_NOISE = {"srl", "srls", "spa", "sl", "sa", "sas", "sarl", "gmbh", "ag", "ltd", "limited", "bv",
                 "nv", "as", "aps", "ab", "lda", "unipessoal", "inc", "co", "kg", "group", "groupe",
                 "grupo", "gruppo", "the", "de", "des", "du", "ett", "plc", "llp"}
NO_COMPANY = {"", "none", "not disclosed", "undisclosed", "unknown", "confidential", "na", "n a"}
LOCATION_NOISE = {"area", "region", "provincia", "province", "nationwide", "and", "pt", "portugal",
                  "france", "italy", "spain", "germany", "belgium", "netherlands", "norway", "denmark",
                  "switzerland", "ireland", "uk", "united", "kingdom", "lombardia", "lazio", "madrid"}


def strip_accents(s):
    return "".join(ch for ch in unicodedata.normalize("NFKD", s or "") if not unicodedata.combining(ch))


def norm_text(s):
    s = strip_accents(s).lower().replace("’", "'")
    s = GENDER_RE.sub(" ", s)
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


def norm_company(s):
    t = norm_text((s or "").replace(".", ""))
    if t in NO_COMPANY:
        return ""
    toks = [w for w in t.split() if w not in COMPANY_NOISE]
    return " ".join(toks) or t


def norm_city(loc):
    s = strip_accents(loc or "").lower()
    s = re.sub(r"\(.*?\)", " ", s)          # department codes "(75)"
    s = s.split(",")[0]                     # "Monza, Lombardia" -> "Monza"
    s = re.sub(r"\b\d+\w*\b", " ", s)       # arrondissements, postcodes
    s = re.sub(r"[^a-z]+", " ", s)
    toks = [w for w in s.split() if w not in LOCATION_NOISE]
    return " ".join(toks)


def norm_country(c):
    c = (c or "").strip()
    return COUNTRY_ALIASES.get(strip_accents(c).lower(), c)


def fingerprint(company, title, location):
    return "|".join([norm_company(company), norm_text(title), norm_city(location)])


def job_id(fp):
    return hashlib.sha1(fp.encode()).hexdigest()[:10]


def is_indeed_short(url):
    return "to.indeed.com" in (url or "")


DATE_FORMATS = ("%Y-%m-%d", "%B %d, %Y", "%d %B %Y", "%d %b %Y", "%b %d, %Y", "%d/%m/%Y", "%d.%m.%Y")


def parse_date(v):
    if not v:
        return None
    if isinstance(v, dt.date):
        return v
    v = str(v).strip()
    for f in DATE_FORMATS:
        try:
            return dt.datetime.strptime(v, f).date()
        except ValueError:
            pass
    m = re.match(r"(\d{4}-\d{2}-\d{2})", v)
    return dt.date.fromisoformat(m.group(1)) if m else None


def iso(d):
    return d.isoformat() if d else None


# ---------------------------------------------------------------- relevance

INCLUDE_RE = re.compile(
    r"rope|irata|sprat|fisat|cordist|\bcorde|\bcordas|\bcuerda|\bfune\b|\bseil|klimm|klatre|climb|"
    r"vertical|height|abseil|rapel|alpinis|rigg|industriekletter|hohenarbeit|hoehenarbeit|"
    r"acesso por|trabajos en altura|trabajos verticales|lavori in quota|lavori su fune|travaux sur corde|"
    r"travaux acrobatiques|en hauteur|hoogte|fall protection|valbeveiliging|scaffold|steeplejack|"
    r"line technician|arborist|tree surgeon|\bacro|\bwall ?man|\bfacade|bridge inspect|wind turbine|"
    r"rotor ?blatt|blade (repair|technician)")


def relevance(c):
    r = c.get("relevant")
    if r is True:
        return True, ""
    if r is False:
        return False, "off-topic (judged by search run)"
    if INCLUDE_RE.search(norm_text(c.get("title", ""))):
        return True, ""
    return False, "off-topic (title has no rope/height-access signal)"


# ---------------------------------------------------------------- state

def load_state():
    if JOBS_FILE.exists():
        return json.loads(JOBS_FILE.read_text())
    return {"version": 1, "jobs": {}, "meta": {}}


def save_state(state):
    JOBS_FILE.parent.mkdir(parents=True, exist_ok=True)
    tmp = JOBS_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, indent=1, sort_keys=True, ensure_ascii=False) + "\n")
    tmp.replace(JOBS_FILE)


def build_index(jobs):
    idx = collections.defaultdict(list)
    for jid, j in jobs.items():
        idx[(j.get("co", ""), j.get("ti", ""))].append(jid)
    return idx


def find_job(jobs, idx, company, title, location):
    co, ti, city = norm_company(company), norm_text(title), norm_city(location)
    cands = idx.get((co, ti), [])
    for jid in cands:
        if jobs[jid].get("city", "") == city:
            return jid
    for jid in cands:  # unknown city on either side still counts as the same ad
        if not jobs[jid].get("city", "") or not city:
            return jid
    return None


def push_url(job, url):
    urls = [u for u in job.get("urls", []) if u != url]
    urls.insert(0, url)
    keep = []
    n_indeed = 0
    for u in urls:  # Indeed short-links are single-use noise: keep only the newest one
        if is_indeed_short(u):
            n_indeed += 1
            if n_indeed > 1:
                continue
        keep.append(u)
    job["urls"] = keep[:3]


# ---------------------------------------------------------------- decision logic

def clean_candidate(raw):
    c = dict(raw)
    for k in ("title", "company", "location", "country", "url", "note", "source", "query"):
        c[k] = (c.get(k) or "").strip()
    c["country"] = norm_country(c["country"])
    c["posted_d"] = parse_date(c.get("posted"))
    v = (c.get("verified") or "").strip().lower()
    c["verified"] = v if v in ("open", "closed") else None
    c["level"] = (c.get("level") or "unspecified").strip().lower()
    return c


def decide(job, c, today):
    """Return (decision, reason, prev_reported_date) for a candidate matched to an existing job (or None)."""
    if job is None:
        return "new", "never seen", None
    posted = c["posted_d"]
    lr = parse_date(job.get("last_reported"))
    ls = parse_date(job.get("last_seen"))
    if job.get("status") == "closed":
        co = parse_date(job.get("closed_on"))
        if c["verified"] == "open":
            return "reopened", "was verified closed, now verified open again", lr
        if posted and co and posted > co:
            return "reopened", "newer posting date than when it was closed", lr
        return "suppress", "previously verified closed", lr
    if lr is None:
        return "new", "seen before but never shown", None
    if (today - lr).days < COOLDOWN_DAYS:
        return "suppress", f"shown {(today - lr).days}d ago (cooldown {COOLDOWN_DAYS}d)", lr
    if posted and posted > lr:
        return "repost", f"posting date {posted} is newer than last time it was shown ({lr})", lr
    gap = (today - ls).days if ls else 0
    if gap >= GAP_DAYS and not posted:
        return "repost", f"absent from searches for {gap}d, then back (no posting date to compare)", lr
    return "suppress", f"already shown {lr}, same posting still listed", lr


def liveness_policy(c, today):
    """Return (section, exclude_reason, tags) for a candidate that is otherwise eligible to be shown."""
    age = (today - c["posted_d"]).days if c["posted_d"] else None
    if c["verified"] == "closed":
        return None, "verified closed", []
    if c["verified"] == "open":
        tags = [f"older ad ({age}d)"] if age is not None and age > OLD_AD_DAYS else []
        return "open", None, tags
    if age is not None and age > MAX_UNVERIFIED_AGE:
        return None, f"likely stale (posted {age}d ago, could not confirm still open)", []
    return "unverified", None, ([] if age is not None else ["no posting date"])


def evaluate(state, raw_cands, today):
    jobs = state["jobs"]
    idx = build_index(jobs)
    merged = collections.OrderedDict()
    out = []
    for raw in raw_cands:
        c = clean_candidate(raw)
        if not (c["title"] and c["url"] and c["country"]):
            out.append({"cand": c, "verdict": "exclude", "reason": "invalid (needs title, url, country)", "jid": None})
            continue
        fp = fingerprint(c["company"], c["title"], c["location"])
        if fp in merged:  # same ad found by two queries today
            m = merged[fp]
            for k in ("posted_d", "verified", "note"):
                if not m[k] and c[k]:
                    m[k] = c[k]
            continue
        c["fp"] = fp
        merged[fp] = c
    for fp, c in merged.items():
        jid = find_job(jobs, idx, c["company"], c["title"], c["location"])
        job = jobs.get(jid) if jid else None
        ok, why = relevance(c)
        if not ok:
            out.append({"cand": c, "jid": jid, "verdict": "exclude", "reason": why})
            continue
        decision, reason, prev = decide(job, c, today)
        if c["verified"] == "closed":
            out.append({"cand": c, "jid": jid, "verdict": "exclude", "reason": "verified closed", "decision": decision})
            continue
        if decision == "suppress":
            out.append({"cand": c, "jid": jid, "verdict": "suppress", "reason": reason, "decision": decision})
            continue
        section, excl, tags = liveness_policy(c, today)
        if excl:
            out.append({"cand": c, "jid": jid, "verdict": "exclude", "reason": excl, "decision": decision})
            continue
        out.append({"cand": c, "jid": jid, "verdict": "report", "decision": decision, "why": reason,
                    "prev": prev, "section": section, "tags": tags})
    return out


def apply_decisions(state, decisions, today):
    jobs = state["jobs"]
    for d in decisions:
        c = d["cand"]
        if d.get("reason", "").startswith("invalid"):
            continue
        jid = d.get("jid")
        if jid is None:
            jid = job_id(c["fp"])
            while jid in jobs:
                jid = job_id(jid + "x")
            jobs[jid] = {"co": norm_company(c["company"]), "ti": norm_text(c["title"]),
                         "city": norm_city(c["location"]), "first_seen": iso(today), "status": "active",
                         "last_reported": None, "reports": [], "urls": []}
        j = jobs[jid]
        j.update(title=c["title"], company=c["company"], location=c["location"], country=c["country"],
                 last_seen=iso(today))
        if not j.get("city"):
            j["city"] = norm_city(c["location"])
        push_url(j, c["url"])
        if c["posted_d"] and (not j.get("posted") or c["posted_d"] > parse_date(j["posted"])):
            j["posted"] = iso(c["posted_d"])
        if c["verified"] == "closed":
            j["status"], j["closed_on"] = "closed", iso(today)
        elif c["verified"] == "open":
            j["status"] = "active"
            j.pop("closed_on", None)
        if d["verdict"] == "report":
            j["status"] = "active"
            j.pop("closed_on", None)
            j["last_reported"] = iso(today)
            j["reports"] = (j.get("reports", []) + [iso(today)])[-20:]
            j.pop("excluded", None)
        elif d["verdict"] == "exclude":
            j["excluded"] = {"date": iso(today), "reason": d["reason"]}
        d["jid"] = jid


def rollback_day(state, day):
    """Undo a previous process run for `day` so it can be re-run idempotently."""
    d = iso(day)
    for j in state["jobs"].values():
        if j.get("last_reported") == d:
            reps = [r for r in j.get("reports", []) if r != d]
            j["reports"] = reps
            j["last_reported"] = reps[-1] if reps else None


# ---------------------------------------------------------------- HTTP liveness (when the network allows it)

CLOSED_PHRASES = [
    "no longer available", "no longer accepting", "position has been filled", "has been filled",
    "job has expired", "posting has expired", "listing has expired", "has expired", "vacancy has closed",
    "vacancy is closed", "position is closed", "applications are closed", "this job is closed",
    "job not found", "page not found", "no longer open", "no longer active", "role has been filled",
    "this job posting is no longer", "job is no longer", "vacancy is no longer", "error 404", "404 not found",
    "n'est plus disponible", "offre expiree", "offre pourvue", "poste pourvu", "offre cloturee",
    "offre est terminee", "annonce expiree", "n'est plus d'actualite", "offre n'existe plus",
    "nicht mehr verfugbar", "nicht mehr aktuell", "stelle ist besetzt", "stellenangebot ist abgelaufen",
    "anzeige ist abgelaufen", "bereits besetzt", "stelle wurde besetzt", "seite nicht gefunden",
    "ya no esta disponible", "oferta no disponible", "oferta ha caducado", "oferta caducada",
    "esta oferta ya no", "oferta finalizada", "puesto cubierto", "vacante cubierta", "oferta cerrada",
    "ya no acepta", "pagina no encontrada",
    "ja nao esta disponivel", "oferta expirada", "oferta encerrada", "vaga encerrada", "anuncio expirado",
    "ja nao se encontra disponivel", "candidaturas encerradas", "esta oferta ja nao",
    "non e piu disponibile", "annuncio scaduto", "offerta scaduta", "posizione chiusa",
    "non piu attivo", "pagina non trovata",
    "niet meer beschikbaar", "vacature is gesloten", "vacature is verlopen", "vacature is vervuld",
    "vacature is ingevuld", "niet langer beschikbaar", "pagina niet gevonden",
    "ikke lenger tilgjengelig", "stillingen er ikke lenger", "annonsen er utlopt", "soknadsfristen har gatt ut",
    "stillingen er besatt", "ikke laengere", "ikke langere", "opslaget er udlobet", "ansogningsfristen er udlobet",
    "jobbet er ikke laengere", "stillingen er ikke laengere",
]
LISTING_SLUGS = {"jobs", "job", "careers", "career", "vacancies", "vacatures", "emplois", "offres", "emploi",
                 "stellenangebote", "stellen", "jobsuche", "empleo", "ofertas", "carrieres", "karriere",
                 "search", "stillinger", "ledige-stillinger", "jobsøgning", "lavora-con-noi", "offerte-di-lavoro"}
WALL_MARKERS = ("authwall", "/login", "/signin", "uas/login", "checkpoint", "/uas/", "captcha")


def _visible_text(html):
    html = re.sub(r"(?is)<(script|style|noscript)\b.*?</\1>", " ", html)
    html = re.sub(r"(?s)<[^>]+>", " ", html)
    return re.sub(r"\s+", " ", html)


def _json_ld_jobpostings(html):
    found = []
    for m in re.finditer(r'(?is)<script[^>]+application/ld\+json[^>]*>(.*?)</script>', html):
        try:
            data = json.loads(m.group(1).strip())
        except ValueError:
            continue
        stack = [data]
        while stack:
            x = stack.pop()
            if isinstance(x, list):
                stack.extend(x)
            elif isinstance(x, dict):
                if x.get("@graph"):
                    stack.append(x["@graph"])
                t = x.get("@type")
                if t == "JobPosting" or (isinstance(t, list) and "JobPosting" in t):
                    found.append(x)
    return found


def classify_response(status, final_url, orig_url, body, today, job_title=""):
    """Pure function: decide open/closed/unknown from an HTTP response. Returns dict(verdict, reason, posted)."""
    res = {"verdict": "unknown", "reason": "", "posted": None}
    low_final = (final_url or "").lower()
    if status in (404, 410, 451):
        return {**res, "verdict": "closed", "reason": f"HTTP {status}"}
    if status in (401, 403, 405, 429, 999) or (status or 0) >= 500 or status is None:
        return {**res, "reason": f"blocked or unavailable (HTTP {status})"}
    if any(mk in low_final for mk in WALL_MARKERS) and not any(mk in orig_url.lower() for mk in WALL_MARKERS):
        return {**res, "reason": "redirected to a login wall"}
    o, f = urllib.parse.urlparse(orig_url), urllib.parse.urlparse(final_url or orig_url)
    o_segs = [s for s in o.path.split("/") if s]
    f_segs = [s for s in f.path.split("/") if s]
    changed = (o.netloc.replace("www.", ""), o.path.rstrip("/")) != (f.netloc.replace("www.", ""), f.path.rstrip("/"))
    if changed and len(o_segs) >= 2 and (not f_segs or f_segs[-1].lower() in LISTING_SLUGS or len(f_segs) < len(o_segs) - 1):
        return {**res, "verdict": "closed", "reason": f"redirected to a generic page ({final_url})"}
    html = body or ""
    postings = _json_ld_jobpostings(html)
    for p in postings:
        dp = parse_date(p.get("datePosted"))
        if dp:
            res["posted"] = iso(dp)
        vt = parse_date(p.get("validThrough"))
        if vt and vt < today:
            return {**res, "verdict": "closed", "reason": f"validThrough {vt} has passed"}
    title_m = re.search(r"(?is)<title[^>]*>(.*?)</title>", html)
    head = strip_accents((title_m.group(1) if title_m else "") + " " + _visible_text(html)[:2000]).lower().replace("’", "'")
    for ph in CLOSED_PHRASES:
        if ph in head:
            return {**res, "verdict": "closed", "reason": f"page says '{ph}'"}
    if postings:
        return {**res, "verdict": "open", "reason": "valid JobPosting structured data, no closed signals"}
    toks = [t for t in norm_text(job_title).split() if len(t) > 3]
    text = norm_text(_visible_text(html)[:20000])
    if toks and sum(t in text for t in toks) / len(toks) >= 0.5 and len(text) > 400:
        return {**res, "verdict": "open", "reason": "page shows the posting, no closed signals (weak)"}
    return {**res, "reason": "page loaded but does not clearly show the posting (may be JavaScript-rendered)"}


def http_check(url, today, job_title="", timeout=12):
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124 Safari/537.36",
        "Accept-Language": "en,pt;q=0.8,fr;q=0.7,de;q=0.6,es;q=0.5,it;q=0.4"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            body = r.read(600_000).decode(r.headers.get_content_charset() or "utf-8", "replace")
            return classify_response(r.status, r.geturl(), url, body, today, job_title)
    except urllib.error.HTTPError as e:
        return classify_response(e.code, url, url, "", today, job_title)
    except (urllib.error.URLError, socket.timeout, OSError, ValueError) as e:
        return {"verdict": "unknown", "reason": f"network error: {getattr(e, 'reason', e)}", "posted": None}


def network_ok(canary="https://www.google.com/robots.txt"):
    try:
        with urllib.request.urlopen(canary, timeout=8) as r:
            return r.status < 500
    except Exception:
        return False


# ---------------------------------------------------------------- digest rendering

LEVEL_BADGE = {"entry": "L1-compatible", "l1": "L1-compatible", "l2": "needs L2 (above current)",
               "l3": "needs L3 (above current)", "cqp": "needs CQP/French cordiste cert",
               "unspecified": "level not stated"}


def render_digest(today, decisions, meta):
    rep = [d for d in decisions if d["verdict"] == "report"]
    open_items = [d for d in rep if d["section"] == "open"]
    unv_items = [d for d in rep if d["section"] == "unverified"]
    excl = [d for d in decisions if d["verdict"] == "exclude"]
    supp = [d for d in decisions if d["verdict"] == "suppress"]
    n_new = sum(d["decision"] == "new" for d in rep)
    n_re = len(rep) - n_new
    L = [f"# Rope Access / Height Access Job Digest — {iso(today)}", ""]
    if not rep:
        L += ["No new postings found today.", ""]
    else:
        by_c = collections.Counter(d["cand"]["country"] for d in rep)
        glance = ", ".join(f"{c} {n}" for c, n in sorted(by_c.items(), key=lambda x: _corder(x[0])))
        L += [f"**{n_new} new** · **{n_re} re-posted** · {len(unv_items)} not confirmed open — {glance}", ""]

    def section(items, title, intro):
        if not items:
            return
        L.extend([f"## {title}", ""] + ([intro, ""] if intro else []))
        for country in sorted({d["cand"]["country"] for d in items}, key=_corder):
            L.extend([f"### {country}", ""])
            for d in items:
                c = d["cand"]
                if c["country"] != country:
                    continue
                badge = {"new": "", "repost": " `RE-POSTED`", "reopened": " `REOPENED`"}[d["decision"]]
                lvl = LEVEL_BADGE.get(c["level"], c["level"])
                tags = [lvl] + d["tags"]
                if d["decision"] != "new" and d.get("prev"):
                    tags.append(f"last shown {iso(d['prev'])}")
                head = f"- **{c['title']}** — {c['company'] or 'company not stated'} — {c['location'] or country}{badge}"
                L.append(head)
                L.append(f"  {c['url']}")
                bits = []
                if c["posted_d"]:
                    bits.append(f"posted {c['posted_d'].strftime('%d %b %Y')}")
                if c.get("verified_by"):
                    bits.append(f"checked: {c['verified_by']}")
                bits.append(" · ".join(tags))
                L.append("  " + " · ".join(b for b in bits if b))
                if c["note"]:
                    L.append(f"  {c['note']}")
                L.append("")

    section(open_items, "Confirmed open", "")
    section(unv_items, "Could not confirm still open — check before applying",
            "These came from sources I cannot open from the search environment (company sites, LinkedIn, etc.) "
            "and are recent enough to be plausible, but not verified.")
    L += ["---", "### Filtered out today (so you know the search ran and what was discarded)", ""]
    reasons = collections.Counter(re.sub(r"\d+", "N", d["reason"]) for d in excl)
    reasons.update(["already shown / still listed (not repeated)"] * len(supp))
    if reasons:
        for r, n in reasons.most_common():
            L.append(f"- {n} × {r}")
    else:
        L.append("- nothing")
    if excl or supp:
        L += ["", "<details><summary>Details</summary>", ""]
        for d in excl + supp:
            c = d["cand"]
            L.append(f"- {c['title']} — {c['company'] or '?'} ({c['location'] or c['country']}): {d['reason']}")
        L += ["", "</details>"]
    qs = meta.get("queries") or []
    if qs:
        zero = sum(1 for q in qs if not q.get("results"))
        L += ["", f"*Coverage: {len(qs)} searches run ({zero} returned nothing). "
                  f"Countries with no new item today: "
                  f"{', '.join(c for c in COUNTRY_ORDER if c not in {d['cand']['country'] for d in rep}) or 'none'}.*"]
    if meta.get("notes"):
        L += ["", f"*{meta['notes']}*"]
    return "\n".join(L) + "\n"


def _corder(c):
    return COUNTRY_ORDER.index(c) if c in COUNTRY_ORDER else len(COUNTRY_ORDER)


# ---------------------------------------------------------------- commands

def load_candidates(path):
    data = json.loads(Path(path).read_text())
    if isinstance(data, list):
        return data, {}
    return data.get("candidates", []), data.get("meta", {})


def cmd_migrate(args):
    seen = json.loads(Path(args.seen).read_text())
    state = {"version": 1, "jobs": {}, "meta": {"migrated_from": "seen_jobs.json"}}
    jobs = state["jobs"]
    idx = build_index(jobs)
    rows = sorted(seen.items(), key=lambda kv: kv[1].get("date_found") or "")
    for url, v in rows:
        day = v.get("date_found") or "1970-01-01"
        jid = find_job(jobs, idx, v.get("company", ""), v.get("title", ""), v.get("location", ""))
        if jid is None:
            fp = fingerprint(v.get("company", ""), v.get("title", ""), v.get("location", ""))
            jid = job_id(fp)
            while jid in jobs:
                jid = job_id(jid + "x")
            jobs[jid] = {"co": norm_company(v.get("company", "")), "ti": norm_text(v.get("title", "")),
                         "city": norm_city(v.get("location", "")), "first_seen": day, "status": "active",
                         "reports": [], "urls": []}
            idx[(jobs[jid]["co"], jobs[jid]["ti"])].append(jid)
        j = jobs[jid]
        j.update(title=v.get("title", ""), company=v.get("company", ""), location=v.get("location", ""),
                 last_seen=day, last_reported=day)
        if v.get("country"):
            j["country"] = norm_country(v["country"])
        j.setdefault("country", "")
        if not j.get("city"):
            j["city"] = norm_city(v.get("location", ""))
        if day not in j["reports"]:
            j["reports"].append(day)
        push_url(j, url)
    save_state(state)
    print(f"migrated {len(rows)} URL entries into {len(jobs)} distinct jobs -> {JOBS_FILE}")


def cmd_precheck(args):
    today = parse_date(args.date)
    cands, _ = load_candidates(args.candidates)
    state = load_state()
    ds = evaluate(state, cands, today)
    need = [d for d in ds if d["verdict"] == "report" and d["cand"]["verified"] is None]
    print(f"{len(cands)} candidates -> {sum(d['verdict']=='report' for d in ds)} would be shown, "
          f"{sum(d['verdict']=='suppress' for d in ds)} already known, {sum(d['verdict']=='exclude' for d in ds)} filtered")
    print("\nNEED VERIFICATION (get_job_details for Indeed ids; fill verified/posted/level/note):")
    for d in need:
        c = d["cand"]
        print(f"  [{d['decision']}] {c['title']} | {c['company']} | {c['location']} | {c['url']} | id={c.get('indeed_id','-')}")
    print("\nALREADY KNOWN / FILTERED (no work needed):")
    for d in ds:
        if d["verdict"] != "report":
            c = d["cand"]
            print(f"  [{d['verdict']}] {c['title']} | {c['company']}: {d['reason']}")


def cmd_process(args):
    today = parse_date(args.date)
    cands, meta = load_candidates(args.candidates)
    state = load_state()
    if args.rerun:
        rollback_day(state, today)
    elif state.get("meta", {}).get("last_run") == iso(today):
        sys.exit(f"{today} was already processed; use --rerun to redo it idempotently")
    net = (not args.no_network) and network_ok()
    ds = None
    if net:
        for c in cands:
            if not c.get("verified") and not is_indeed_short(c.get("url", "")) and c.get("url"):
                r = http_check(c["url"], today, c.get("title", ""))
                if r["verdict"] in ("open", "closed"):
                    c["verified"] = r["verdict"]
                    c["verified_by"] = "HTTP: " + r["reason"]
                    if r["posted"] and not c.get("posted"):
                        c["posted"] = r["posted"]
    ds = evaluate(state, cands, today)
    apply_decisions(state, ds, today)
    state["meta"]["last_run"] = iso(today)
    text = render_digest(today, ds, meta)
    n_rep = sum(d["verdict"] == "report" for d in ds)
    if args.dry_run:
        print(text)
        return
    DIGEST_DIR.mkdir(exist_ok=True)
    (DIGEST_DIR / f"{iso(today)}.md").write_text(text)
    save_state(state)
    q_stats = collections.defaultdict(lambda: [0, 0])
    for q in meta.get("queries", []):
        q_stats[q.get("id") or q.get("q", "?")][0] += q.get("results", 0)
    for d in ds:
        if d["verdict"] == "report" and d["cand"].get("query") in q_stats:
            q_stats[d["cand"]["query"]][1] += 1
    log = {"date": iso(today), "network": net, "candidates": len(cands), "shown": n_rep,
           "new": sum(d["verdict"] == "report" and d["decision"] == "new" for d in ds),
           "suppressed": sum(d["verdict"] == "suppress" for d in ds),
           "excluded": sum(d["verdict"] == "exclude" for d in ds),
           "queries": {k: {"results": v[0], "shown": v[1]} for k, v in q_stats.items()}}
    kept = [l for l in (RUN_LOG.read_text().splitlines() if RUN_LOG.exists() else [])
            if json.loads(l).get("date") != iso(today)]
    RUN_LOG.write_text("".join(l + "\n" for l in kept + [json.dumps(log, ensure_ascii=False)]))
    print(json.dumps({k: v for k, v in log.items() if k != "queries"}))
    print(f"digest -> digests/{iso(today)}.md ; state -> {JOBS_FILE.relative_to(ROOT)} (network checks: {'on' if net else 'unavailable'})")


def cmd_check(args):
    today = parse_date(args.date) or dt.date.today()
    for u in args.urls:
        print(u, "->", http_check(u, today))


def cmd_netcheck(args):
    ok = network_ok()
    print("network: reachable" if ok else "network: BLOCKED (HTTP link checks unavailable; unverified policy applies)")


def cmd_plan(args):
    today = parse_date(args.date)
    plan = json.loads(PLAN_FILE.read_text())
    wd = today.weekday()
    print(f"# Search plan for {today} (weekday {wd}); rotation slot {wd % plan['rotation_slots']}")
    n = 0
    for country, cfg in plan["countries"].items():
        cities = cfg["core_cities"] + [c for c, slot in cfg["rotating_cities"] if slot == wd % plan["rotation_slots"]]
        for city in cities:
            for term in cfg["terms"]:
                n += 1
                print(f"INDEED  country_code={cfg['code']} location={city!r} search={term!r}")
    for q in plan["web_queries"]:
        if q.get("weekday") not in (None, wd):
            continue
        n += 1
        doms = ",".join(q.get("allowed_domains", []))
        print(f"WEB     mode={q.get('mode', 'standard')} query={q['query']!r} allowed_domains=[{doms}]")
    wl = plan.get("watchlist", [])
    for i in range(plan.get("watchlist_per_day", 0)):
        w = wl[(today.toordinal() * plan["watchlist_per_day"] + i) % len(wl)]
        n += 1
        print(f"INDEED  country_code={w['code']} location={w['city']!r} search={w['name']!r}   # employer watchlist")
    print(f"# {n} queries. Give each a stable id like 'indeed:{{code}}:{{city}}:{{term}}' for the coverage log.")


def cmd_stats(args):
    if not RUN_LOG.exists():
        print("no run log yet")
        return
    agg = collections.defaultdict(lambda: [0, 0, 0])
    days = 0
    for line in RUN_LOG.read_text().splitlines()[-args.days:]:
        r = json.loads(line)
        days += 1
        for k, v in r.get("queries", {}).items():
            agg[k][0] += 1
            agg[k][1] += v["results"]
            agg[k][2] += v["shown"]
    print(f"last {days} runs: query | runs | results | shown")
    for k, (n, res, sh) in sorted(agg.items(), key=lambda x: -x[1][2]):
        print(f"  {k} | {n} | {res} | {sh}")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("migrate"); p.add_argument("--seen", default=str(SEEN_LEGACY)); p.set_defaults(fn=cmd_migrate)
    for name, fn in (("precheck", cmd_precheck), ("process", cmd_process)):
        p = sub.add_parser(name); p.add_argument("candidates"); p.add_argument("--date", required=True)
        if name == "process":
            p.add_argument("--dry-run", action="store_true"); p.add_argument("--no-network", action="store_true")
            p.add_argument("--rerun", action="store_true")
        p.set_defaults(fn=fn)
    p = sub.add_parser("check"); p.add_argument("urls", nargs="+"); p.add_argument("--date"); p.set_defaults(fn=cmd_check)
    p = sub.add_parser("netcheck"); p.set_defaults(fn=cmd_netcheck)
    p = sub.add_parser("plan"); p.add_argument("--date", required=True); p.set_defaults(fn=cmd_plan)
    p = sub.add_parser("stats"); p.add_argument("--days", type=int, default=14); p.set_defaults(fn=cmd_stats)
    args = ap.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
