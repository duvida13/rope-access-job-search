import datetime as dt
import http.server
import json
import sys
import threading
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import jobtool as jt  # noqa: E402

D = dt.date


def cand(**kw):
    base = dict(title="Cordiste H/F", company="PROMAN", location="Lille (59)", country="France",
                url="https://to.indeed.com/aaa", posted="2026-10-01", verified="open", level="entry")
    base.update(kw)
    return base


def state_with(**job):
    j = dict(co="proman", ti="cordiste", city="lille", status="active", first_seen="2026-09-01",
             last_seen="2026-09-10", last_reported="2026-09-10", reports=["2026-09-10"], urls=[])
    j.update(job)
    return {"jobs": {"abc": j}, "meta": {}}


def run(state, c, today):
    return jt.evaluate(state, [c], today)[0]


class Normalisation(unittest.TestCase):
    def test_same_job_different_decoration(self):
        a = jt.fingerprint("Groupe LIP", "CORDISTE URBAIN (H/F)", "Paris 15e (75)")
        b = jt.fingerprint("LIP", "Cordiste urbain H/F", "Paris")
        self.assertEqual(a, b)

    def test_gender_markers(self):
        for t in ("Seilzugangstechniker (m/w/d)", "Seilzugangstechniker m/w/d", "Seilzugangstechniker (M/F/X)"):
            self.assertEqual(jt.norm_text(t), "seilzugangstechniker")

    def test_accents_and_company_suffix(self):
        self.assertEqual(jt.norm_company("Solução Futuro"), jt.norm_company("Solucao Futuro"))
        self.assertEqual(jt.norm_company("Archingegno S.r.l."), "archingegno")

    def test_different_city_is_different_job(self):
        self.assertNotEqual(jt.fingerprint("Proman", "Cordiste", "Lille (59)"), jt.fingerprint("Proman", "Cordiste", "Annemasse (74)"))

    def test_undisclosed_company(self):
        self.assertEqual(jt.norm_company("Not disclosed"), "")


class Dedup(unittest.TestCase):
    def test_new_job(self):
        self.assertEqual(run({"jobs": {}, "meta": {}}, cand(), D(2026, 10, 11))["decision"], "new")

    def test_same_ad_new_indeed_shortlink_is_suppressed(self):
        d = run(state_with(last_reported="2026-10-05", last_seen="2026-10-05"), cand(url="https://to.indeed.com/NEWLINK"), D(2026, 10, 11))
        self.assertEqual(d["verdict"], "suppress")

    def test_old_ad_not_repeated_even_after_cooldown_if_posted_before_last_shown(self):
        s = state_with(last_reported="2026-09-10", last_seen="2026-10-10")
        d = run(s, cand(posted="2026-09-05"), D(2026, 10, 11))
        self.assertEqual(d["verdict"], "suppress")

    def test_repost_when_posting_date_newer_after_cooldown(self):
        d = run(state_with(), cand(posted="2026-10-08"), D(2026, 10, 11))
        self.assertEqual((d["verdict"], d["decision"]), ("report", "repost"))
        self.assertEqual(jt.iso(d["prev"]), "2026-09-10")

    def test_newer_posting_date_inside_cooldown_is_suppressed(self):
        s = state_with(last_reported="2026-10-05", last_seen="2026-10-05")
        self.assertEqual(run(s, cand(posted="2026-10-09"), D(2026, 10, 11))["verdict"], "suppress")

    def test_repost_after_absence_without_date(self):
        s = state_with(last_reported="2026-09-01", last_seen="2026-09-05")
        d = run(s, cand(posted=None), D(2026, 10, 11))
        self.assertEqual((d["verdict"], d["decision"]), ("report", "repost"))

    def test_absence_with_old_posting_date_is_not_a_repost(self):
        s = state_with(last_reported="2026-09-01", last_seen="2026-09-05")
        self.assertEqual(run(s, cand(posted="2026-08-20"), D(2026, 10, 11))["verdict"], "suppress")

    def test_continuously_listed_is_not_repeated(self):
        s = state_with(last_reported="2026-09-01", last_seen="2026-10-10")
        self.assertEqual(run(s, cand(posted=None), D(2026, 10, 11))["verdict"], "suppress")

    def test_closed_job_comes_back_verified_open(self):
        s = state_with(status="closed", closed_on="2026-09-20")
        d = run(s, cand(posted=None), D(2026, 10, 11))
        self.assertEqual((d["verdict"], d["decision"]), ("report", "reopened"))

    def test_closed_job_unverified_stays_suppressed(self):
        s = state_with(status="closed", closed_on="2026-09-20")
        self.assertEqual(run(s, cand(posted=None, verified=None), D(2026, 10, 11))["verdict"], "suppress")

    def test_seen_but_never_shown_is_evaluated_as_new(self):
        s = state_with(last_reported=None, reports=[])
        self.assertEqual(run(s, cand(), D(2026, 10, 11))["decision"], "new")

    def test_duplicate_within_one_batch(self):
        ds = jt.evaluate({"jobs": {}, "meta": {}}, [cand(url="https://to.indeed.com/1"), cand(url="https://to.indeed.com/2")], D(2026, 10, 11))
        self.assertEqual(len(ds), 1)


class Liveness(unittest.TestCase):
    T = D(2026, 10, 11)

    def test_verified_closed_excluded(self):
        d = run({"jobs": {}, "meta": {}}, cand(verified="closed"), self.T)
        self.assertEqual((d["verdict"], d["reason"]), ("exclude", "verified closed"))

    def test_unverified_recent_goes_to_unverified_section(self):
        d = run({"jobs": {}, "meta": {}}, cand(verified=None, posted="2026-10-01"), self.T)
        self.assertEqual((d["verdict"], d["section"]), ("report", "unverified"))

    def test_unverified_old_dropped(self):
        d = run({"jobs": {}, "meta": {}}, cand(verified=None, posted="2026-07-06"), self.T)
        self.assertEqual(d["verdict"], "exclude")
        self.assertIn("stale", d["reason"])

    def test_unverified_no_date_flagged(self):
        d = run({"jobs": {}, "meta": {}}, cand(verified=None, posted=None), self.T)
        self.assertEqual(d["section"], "unverified")
        self.assertIn("no posting date", d["tags"])

    def test_verified_old_ad_tagged_not_dropped(self):
        d = run({"jobs": {}, "meta": {}}, cand(verified="open", posted="2026-07-06"), self.T)
        self.assertEqual(d["section"], "open")
        self.assertTrue(any("older ad" in t for t in d["tags"]))


class Relevance(unittest.TestCase):
    def test_window_cleaner_filtered(self):
        d = run({"jobs": {}, "meta": {}}, cand(title="Laveur de vitres professionnel(le)"), D(2026, 10, 11))
        self.assertEqual(d["verdict"], "exclude")

    def test_rope_titles_pass(self):
        for t in ("Operaio edile su fune", "Rope Access Technician", "Seilzugangstechniker (m/w/d)",
                  "Técnico de trabajos verticales", "Técnico acesso por cordas", "Industriekletterer"):
            self.assertTrue(jt.relevance({"title": t})[0], t)

    def test_agent_override(self):
        self.assertTrue(jt.relevance({"title": "Muratore", "relevant": True})[0])


class Lifecycle(unittest.TestCase):
    def test_apply_then_rerun_is_idempotent(self):
        s = {"jobs": {}, "meta": {}}
        t = D(2026, 10, 11)
        ds = jt.evaluate(s, [cand()], t)
        jt.apply_decisions(s, ds, t)
        self.assertEqual(len(s["jobs"]), 1)
        j = next(iter(s["jobs"].values()))
        self.assertEqual(j["last_reported"], "2026-10-11")
        jt.rollback_day(s, t)
        self.assertIsNone(j["last_reported"])
        self.assertEqual(jt.evaluate(s, [cand()], t)[0]["decision"], "new")

    def test_only_newest_indeed_shortlink_kept(self):
        j = {"urls": []}
        for u in ("https://to.indeed.com/1", "https://example.com/job/1", "https://to.indeed.com/2"):
            jt.push_url(j, u)
        self.assertEqual(j["urls"], ["https://to.indeed.com/2", "https://example.com/job/1"])

    def test_digest_renders_and_zero_case(self):
        t = D(2026, 10, 11)
        self.assertIn("No new postings found today.", jt.render_digest(t, [], {}))
        s = {"jobs": {}, "meta": {}}
        ds = jt.evaluate(s, [cand(note="note here", verified_by="Indeed job details")], t)
        txt = jt.render_digest(t, ds, {"queries": [{"q": "x", "results": 0}]})
        self.assertIn("## Confirmed open", txt)
        self.assertIn("### France", txt)
        self.assertIn("L1-compatible", txt)
        self.assertIn("checked: Indeed job details", txt)


class Classifier(unittest.TestCase):
    T = D(2026, 10, 11)
    LIVE = "<html><title>Rope Access Technician - Acme</title><body>" + ("<p>Rope Access Technician IRATA role at Acme inspecting structures, apply now.</p>" * 20) + "</body></html>"

    def c(self, status=200, final="https://acme.com/jobs/123-rope", orig="https://acme.com/jobs/123-rope", body=LIVE):
        return jt.classify_response(status, final, orig, body, self.T, "Rope Access Technician")

    def test_404_410(self):
        self.assertEqual(self.c(404)["verdict"], "closed")
        self.assertEqual(self.c(410)["verdict"], "closed")

    def test_blocked_is_unknown_not_closed(self):
        for s in (403, 429, 999, 503):
            self.assertEqual(self.c(s)["verdict"], "unknown")

    def test_closed_phrase_languages(self):
        for ph in ("This job is no longer available", "Cette offre n’est plus disponible", "Diese Stelle ist leider nicht mehr verfügbar",
                   "Esta oferta ya no está disponible", "Esta oferta já não está disponível", "Questo annuncio non è più disponibile",
                   "Deze vacature is niet meer beschikbaar", "Stillingen er ikke lenger tilgjengelig", "No longer accepting applications"):
            self.assertEqual(self.c(body=f"<html><title>Jobs</title><h1>{ph}</h1></html>")["verdict"], "closed", ph)

    def test_phrase_deep_in_page_does_not_trigger(self):
        body = "<html><title>Rope Access Technician</title><body>" + ("<p>Rope Access Technician IRATA wanted for inspection.</p>" * 200) + "<footer>page not found links</footer></body></html>"
        self.assertEqual(self.c(body=body)["verdict"], "open")

    def test_json_ld_valid_through(self):
        ld = lambda vt: '<script type="application/ld+json">{"@type":"JobPosting","title":"x","validThrough":"%s","datePosted":"2026-09-01"}</script>' % vt
        self.assertEqual(self.c(body=ld("2026-10-01"))["verdict"], "closed")
        r = self.c(body=ld("2026-12-01"))
        self.assertEqual((r["verdict"], r["posted"]), ("open", "2026-09-01"))

    def test_json_ld_in_graph(self):
        body = '<script type="application/ld+json">{"@graph":[{"@type":"JobPosting","validThrough":"2026-01-01"}]}</script>'
        self.assertEqual(self.c(body=body)["verdict"], "closed")

    def test_soft_redirect_to_listing(self):
        self.assertEqual(self.c(final="https://acme.com/jobs", orig="https://acme.com/jobs/123-rope")["verdict"], "closed")
        self.assertEqual(self.c(final="https://acme.com/", orig="https://acme.com/careers/123")["verdict"], "closed")

    def test_login_wall_unknown(self):
        self.assertEqual(self.c(final="https://www.linkedin.com/authwall?trk=x", orig="https://www.linkedin.com/jobs/view/1")["verdict"], "unknown")

    def test_js_shell_unknown(self):
        self.assertEqual(self.c(body="<html><title>Careers</title><div id=app></div><script>app()</script></html>")["verdict"], "unknown")

    def test_live_page_open(self):
        self.assertEqual(self.c()["verdict"], "open")


class _H(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_GET(self):
        if self.path == "/gone":
            self.send_response(404); self.end_headers(); return
        if self.path == "/moved/123-job":
            self.send_response(302); self.send_header("Location", "/jobs"); self.end_headers(); return
        body = (b"<html><title>Jobs</title><p>All vacancies</p></html>" if self.path == "/jobs" else
                ("<html><title>Rope Access Technician</title>" + "<p>Rope Access Technician IRATA role.</p>" * 40 + "</html>").encode())
        self.send_response(200); self.send_header("Content-Type", "text/html"); self.end_headers(); self.wfile.write(body)


class LiveHttp(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.srv = http.server.HTTPServer(("127.0.0.1", 0), _H)
        cls.base = f"http://127.0.0.1:{cls.srv.server_port}"
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown()

    def test_end_to_end(self):
        t = D(2026, 10, 11)
        self.assertEqual(jt.http_check(self.base + "/gone", t)["verdict"], "closed")
        self.assertEqual(jt.http_check(self.base + "/moved/123-job", t)["verdict"], "closed")
        self.assertEqual(jt.http_check(self.base + "/job/9", t, "Rope Access Technician")["verdict"], "open")
        self.assertEqual(jt.http_check("http://127.0.0.1:1/x", t)["verdict"], "unknown")


if __name__ == "__main__":
    unittest.main(verbosity=1)
