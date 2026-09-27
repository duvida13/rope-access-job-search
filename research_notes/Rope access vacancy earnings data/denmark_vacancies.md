# Denmark Rope Access / Offshore Wind Technician Vacancies — Research Notes
Compiled 2026-09-27

## IMPORTANT METHODOLOGY NOTE — Indeed tool was unusable this session

The `mcp__Indeed__search_jobs` / `mcp__Indeed__get_job_details` tools were called with **~35 varied query/location combinations** across the full requested keyword and location matrix ("rope access technician", "rope access", "blade technician", "vindmølletekniker", "vindmølle servicetekniker", "wind turbine technician", "offshore wind technician", "blade repair technician", "offshore technician" × Esbjerg, Aalborg, Copenhagen, Denmark, Aalborg). Two outcomes occurred:

1. **Direct city queries (Esbjerg, Aalborg) returned "No job results found"** in every case attempted before the rate limit set in.
2. **All subsequent calls failed with a persistent, non-recovering rate-limit error** ("Rate limit exceeded for account 231207884 on toolset claude"), even after waiting 30–90 seconds between attempts and retrying roughly 30 times over ~20 minutes. The cooldown timer never reliably reached zero, indicating the account-level quota was being consumed by concurrent/shared usage outside this session's control, not by this session's own call rate. As a result, **zero usable Indeed search results or job-detail pages were obtained**, and no Indeed job IDs can be cited.
3. `WebFetch` on primary employer career pages (careers.vestas.com, globalwindservice.recruitee.com, jobtek.eu) was also blocked by the network egress proxy in this environment ("EGRESS_BLOCKED"), so full original job-posting text could not be retrieved even for postings identified by URL via web search.

Given these tool failures, per the task instructions ("If the real total is lower, report that honestly" and "do not fabricate or estimate postings"), the vacancy table below is built **only from what WebSearch snippets/aggregators surfaced** — it is thin, incomplete on pay/rotation/employment-type details, and falls short of the 8–12 target. Several rows lack a working direct listing URL because the underlying career-site pages could not be fetched (proxy-blocked). This is disclosed per-row.

## Vacancy Table (real postings found only; no fabricated entries)

| Company | Job title | Location | Posted date | Pay/rate | Rotation/schedule | Accommodation/travel | Overtime | Employment type | Certification required | Source |
|---|---|---|---|---|---|---|---|---|---|---|
| Vestas Wind Systems A/S | Offshore Service Technician (V236-15MW program) | Esbjerg, Denmark (Horns Rev 3 site) | Not disclosed (found via web search, date unknown — page not fetchable) | Not disclosed | Not disclosed in search snippet; general Vestas offshore roles elsewhere reference a 14/14 rotation model, but this was not confirmed specifically for this Esbjerg posting | Not disclosed | Not disclosed | Permanent, described as "Travel Technician" gaining experience as Prototype/Test Technician | Not disclosed (Vestas offshore roles generally require WTG technician background; GWO not explicitly stated in snippet) | careers.vestas.com/job/Esbjerg-Service-Technician-Regi/783110001/ (page blocked by network egress proxy in this session — could not confirm full text, so treat pay/rotation fields as unconfirmed) |
| Global Wind Service | Wind Turbine Blade Technician | Fredericia, Syddanmark, Denmark | Not disclosed | Not disclosed in snippet | Not disclosed | Not disclosed | Described generally as hiring "Blade Repair Technicians" and "Complex Blade Repair Technicians" for ongoing global projects | Rope access / blade repair background implied (GWO/IRATA not explicitly confirmed in snippet) | globalwindservice.recruitee.com/o/wind-turbine-blade-technician (site blocked by egress proxy — could not verify full posting text) |
| iPS Baltic (recruitment agency, client role) | Wind Turbine Technician | Offshore, Esbjerg, Denmark | Not disclosed | "2 weeks on / 2 weeks off" rotation (stated in aggregator summary) | Not disclosed | Not disclosed | Not disclosed | "Danish speakers or fluent English required, blade repair experience, GWO certifications" (per aggregator summary) — GWO confirmed | ips-baltics.com/job-offers/wind-turbine-technicians-4/ (aggregator listing; original client/company not named, so cannot verify independently) |
| ROMO Wind A/S | Wind Turbine Technician (turbine instrumentation/pitch investigation) | Aarhus, Denmark | Not disclosed | Not disclosed | Not disclosed | Not disclosed | Not disclosed | Not disclosed | Found via web search aggregator only; no direct URL retrieved — **excluded from confident count, listed for completeness only** |

**Honest count: only 2–3 of the above rows (Vestas Esbjerg, Global Wind Service Fredericia, iPS Baltic/Esbjerg) have a location, company and role specific enough to call a real, identifiable vacancy — and even those could not be verified against the full original posting text due to tool/proxy failures. This falls well short of the 8–12 target.** A company also seen repeatedly in "top hirers for wind roles in Denmark" aggregator summaries but with no specific individual vacancy pinned down: Ørsted (Fredericia/Copenhagen offices, per its own careers site structure), Vattenfall, RWE Offshore Wind, Siemens Gamesa, Cadeler (offshore crew, Danish-operated vessels — general "join our fleet" recruiting language, not a specific job req). RTS Wind Group's rope-access "Rotor Blade Technician" roles were found via web search but confirmed to be posted for Portugal/UK/Germany/Austria, **not Denmark** — correctly excluded here rather than assumed.

## What could not be established (gaps)
- Verbatim pay/day-rate figures for any specific Denmark posting — none of the sources returned in this session disclosed a rate.
- Rotation patterns for Vestas Esbjerg and Global Wind Service Fredericia specifically (only the iPS Baltic-brokered role stated a rotation: 2 on/2 off).
- Accommodation/travel provisions, overtime terms, and IRATA/SPRAT (vs GWO) certification requirements for any of the above roles.
- Posting/listing dates for all rows.
- A working, fetchable original job-posting page for any row (career pages were blocked by the sandbox's network egress proxy: careers.vestas.com, globalwindservice.recruitee.com, jobtek.eu all returned EGRESS_BLOCKED).

**Recommendation for the project:** re-run the Indeed tool searches in a later session when the account-level rate limit is not being contended by concurrent usage, and/or have a human check jobindex.dk, jobnet.dk (Denmark's public job bank) and workindenmark.dk directly, since this session could not reach them (jobindex blocked per earlier project notes; jobnet/workindenmark not reachable via the tools available here).

---

## Denmark Income Tax Facts (2026) — for Net Pay Calculations

All figures below are for 2026 and correspond to a single filer, no dependents, ordinary employment income (not covering special expat/researcher tax schemes).

### 1. AM-bidrag (Labour Market Contribution) — flat 8%
- A flat **8%** is deducted from gross personal income (salary, etc.) **before** any other income tax is calculated. It applies to essentially all earned income. — [The Local DK, 2026 tax brackets](https://www.thelocal.dk/20251113/middle-top-and-top-top-how-denmarks-tax-brackets-are-changing-in-2026)

### 2. Bundskat (Bottom/base tax) — 12.01%
- The base state tax rate for 2026 is **12.01%**, applied to income remaining after AM-bidrag and above the personfradrag (personal allowance). — [The Local DK](https://www.thelocal.dk/20251113/middle-top-and-top-top-how-denmarks-tax-brackets-are-changing-in-2026)

### 3. New multi-tier top-tax structure effective January 2026
Denmark's parliament restructured the former single "topskat" bracket into three tiers, effective from 2026:
- **Mellemskat (Middle tax): 7.5%** on income between **DKK 641,200 and DKK 777,900** (in addition to bundskat + municipal tax).
- **Topskat (Top tax): 7.5%** on income **above DKK 777,900**.
- **Top-topskat (Top-top tax): 5%** on income **above DKK 2,592,700**.
— [The Local DK, "Middle, top and top-top": How Denmark's tax brackets are changing in 2026](https://www.thelocal.dk/20251113/middle-top-and-top-top-how-denmarks-tax-brackets-are-changing-in-2026); corroborated by [Schjødt law firm, "Danish top-top tax is a reality from 2026"](https://schjodt.com/news/danish-top-top-tax-is-a-reality-from-2026)

### 4. Kommuneskat (Municipal tax) — average ~25.05% (varies by municipality)
- The **national average municipal tax rate for 2026 is 25.049%** (≈25.05%), down slightly from 25.1% in 2025. Rates set independently by each of Denmark's 98 municipalities range from **23.39% (Copenhagen)** up to **26.30%** in the highest-taxing municipalities. — [Expat Finance, Municipality Tax Rates 2026](https://expatfinance.dk/taxes/municipality-tax-rates-2026/)
- **Esbjerg** (Denmark's main offshore wind hub, and the most relevant municipality for this project) has a 2026 municipal tax rate of **26.1%**, up 0.3 percentage points from 25.8% in 2025, per local budget reporting. — [tvSyd, "Esbjerg hæver skatten fra næste år"](https://www.tvsyd.dk/esbjerg/esbjerg-haever-skatten-fra-naeste-ar)

### 5. Personfradrag (Personal allowance) — DKK 54,100
- The 2026 personfradrag is **DKK 54,100** (up from DKK 51,600 in 2025), automatically applied so the first DKK 54,100 of income is untaxed for state and municipal tax purposes (church tax too, where applicable). Unused allowance can be transferred to a spouse. Note: **AM-bidrag (8%) is calculated on gross income before the personfradrag is applied** — the allowance only reduces bundskat/mellemskat/topskat/kommuneskat, not the labour-market contribution. — [Skatteberegneren.dk, "Personfradrag 2026"](https://skatteberegneren.dk/artikler/personfradrag-2026/)

### 6. Combined marginal/average rate at a typical offshore-wind-technician income (~DKK 400,000–600,000/year)
Putting the above together for a single filer with no dependents, using Esbjerg's 26.1% municipal rate:
- **Income up to ~DKK 641,200/year** (after AM-bidrag and above the personfradrag): combined rate ≈ 8% (AM-bidrag) + effective (bundskat 12.01% + kommuneskat 26.1%) on the remainder ≈ roughly a **38–42% marginal rate band** for most of this income range, before mellemskat kicks in. (There is a statutory ceiling — "skatteloft" — that caps the combined bundskat+mellemskat+topskat+top-topskat so total marginal state+local tax cannot exceed set limits, but the exact 2026 ceiling percentage was not retrieved in this session — see Gaps below.)
- **Income between DKK 641,200 and DKK 777,900/year**: an additional **7.5% mellemskat** applies on top of the above, pushing the marginal rate on that slice toward roughly **45–49%**.
- **Income above DKK 777,900/year**: an additional **7.5% topskat** applies (mellemskat converts/topskat begins), pushing marginal rates on the top slice higher still, in the roughly **50%+** range — consistent with Denmark's well-known reputation for a very high marginal income tax rate on upper-middle and higher earned incomes, funded alongside a broad-based 25% VAT (moms) rather than differentiated consumption taxes.
- For a technician earning in the DKK 400,000–600,000/year range specifically, most or all of the income falls **below** the DKK 641,200 mellemskat threshold, so the applicable combined marginal rate is the AM-bidrag (8%) plus bundskat (12.01%) plus kommuneskat (~25–26%) band — i.e., **no mellemskat/topskat applies unless the technician's total taxable income (including any overtime/bonus pay) pushes them over DKK 641,200/year.** Overtime-heavy earners near the top of this range (DKK 550,000–600,000+) should be flagged as being close to, but generally still under, the mellemskat threshold.

### Gaps (tax section)
- The exact 2026 statutory tax ceiling ("skatteloft") percentage that caps combined bundskat + mellemskat + topskat + top-topskat was referenced by sources but its specific numeric value for 2026 was not retrieved in this session — needed for a fully precise marginal-rate calculation near/above the mellemskat threshold.
- Church tax (kirkeskat) was not researched; it is optional (only paid by members of the Danish national church) and varies by municipality (typically ~0.7–1.3%), so it was excluded from the "combined" figures above as most non-Danish or non-member workers would not pay it — flag this explicitly for the report writer since some Danish nationals in the workforce sample may pay it.
- No official skat.dk primary-source page was directly fetched (web search results summarizing skat.dk and third-party tax-guide sites were used instead); a follow-up session with working access to skat.dk directly would let the primary AM-bidrag/bundskat/personfradrag rates be confirmed against the government source rather than secondary aggregators.

## Sources
- [The Local DK — "Middle, top and top-top": How Denmark's tax brackets are changing in 2026](https://www.thelocal.dk/20251113/middle-top-and-top-top-how-denmarks-tax-brackets-are-changing-in-2026)
- [Schjødt — Danish top-top tax is a reality from 2026](https://schjodt.com/news/danish-top-top-tax-is-a-reality-from-2026)
- [Expat Finance — Municipality Tax Rates 2026](https://expatfinance.dk/taxes/municipality-tax-rates-2026/)
- [tvSyd — Esbjerg hæver skatten fra næste år](https://www.tvsyd.dk/esbjerg/esbjerg-haever-skatten-fra-naeste-ar)
- [Skatteberegneren.dk — Personfradrag 2026: Beløb og skatteværdi forklaret](https://skatteberegneren.dk/artikler/personfradrag-2026/)
- [tax.dk — Personfradrag](https://tax.dk/skat/personfradrag.htm)
- [PwC Tax Summaries — Denmark, Individual, Taxes on personal income](https://taxsummaries.pwc.com/denmark/individual/taxes-on-personal-income)
- [ips-baltics.com — Wind turbine technicians job offers](https://ips-baltics.com/job-offers/wind-turbine-technicians-4/)
- [Vestas careers — V236-15MW Offshore Service Technician, Esbjerg](https://careers.vestas.com/job/Esbjerg-Service-Technician-Regi/783110001/) (page content could not be fetched from this session — egress-blocked)
- [Global Wind Service — Wind Turbine Blade Technician](https://globalwindservice.recruitee.com/o/wind-turbine-blade-technician) (page content could not be fetched from this session — egress-blocked)
- [RTS Wind Group — Rotor Blade Technician vacancies](https://www.rts-wind.com/vacancies/rotor-blade-technician-onshore-rope-access/) (confirmed NOT Denmark-located; excluded from table)
