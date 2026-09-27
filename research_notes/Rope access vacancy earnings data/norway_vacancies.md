# Norway Rope Access / Offshore Technician Vacancies — Research Notes

## Methodology and honest limitations

Searches were run via the Indeed MCP tool (`search_jobs`, country_code=NO) across the requested keyword variants ("tilkomsttekniker", "rope access", "rope access technician", "offshore technician", "riggerier", "vindteknikker", "wind turbine technician", "NDT inspector", "offshore inspector", "SOFT tekniker", "industriklatrer") and locations (Stavanger, Sola, Sandnes, Bergen, Haugesund, Norway/remote). Most single-keyword/location combinations returned 0–1 results, confirming the task brief's note that this market is thin via this tool; several combinations returned "No job results found."

**Important limitation:** after the initial batch of `search_jobs` calls, the Indeed tool's account-level rate limit became persistently exhausted for the remainder of the session — very likely because other parallel research tasks in this same project were also calling the same shared Indeed MCP account concurrently. Roughly 15 retries spaced 30–100 seconds apart over ~15 minutes all failed with "Rate limit exceeded," including every attempt to call `get_job_details` on the postings below. As a result, **none of the free-text job descriptions could be retrieved in this session**, so the per-listing fields that depend on the description text (verbatim pay, rotation pattern, accommodation/travel, overtime, employment type, and certification requirement) could not be extracted and are marked "not retrieved (description unavailable — API rate-limited)" rather than fabricated. Only the structured summary fields returned directly by `search_jobs` (title, company, location, posted date, job type, URL) are reported. This should be re-run with `get_job_details` once the shared rate limit clears, or in a session with dedicated Indeed API quota, to fill in the pay/rotation/certification columns.

No web search for individual postings beyond finn.no/Indeed was attempted (finn.no was noted as blocked in earlier project research; general web search was reserved for the tax-facts portion of this assignment, per the task's priorities).

## Vacancy table (real postings found via Indeed search_jobs, country=NO)

Core, clearly relevant to rope access / offshore inspection / offshore wind technician work:

| Company | Job title | Location | Posted date | Pay/rate | Rotation/schedule | Accommodation/travel | Overtime | Employment type | Certification required | Source |
|---|---|---|---|---|---|---|---|---|---|---|
| DeepOcean | Tilkomsttekniker elektro | Sola | Sep 23, 2026 | not retrieved (description unavailable — API rate-limited) | not retrieved | not retrieved | not retrieved | Full-time (per listing) | not retrieved (context from earlier project research: DeepOcean's Norwegian access-technician roles are generally SOFT/NS 9600-based, not IRATA, but this was not re-confirmed from this posting's text) | Job ID JOBSEARCH_100253 — https://to.indeed.com/aa47zhhg9f86 |
| DeepOcean | Inspection Assistant | Tananger | Sep 14, 2026 | not retrieved | not retrieved | not retrieved | not retrieved | Permanent (per listing) | not retrieved | Job ID JOBSEARCH_100254 — https://to.indeed.com/aapvg9k4gxsy |
| NOV | Inspection Assistant | Tananger | Sep 11, 2026 | not retrieved | not retrieved | not retrieved | not retrieved | Full-time (per listing) | not retrieved | Job ID JOBSEARCH_100255 — https://to.indeed.com/aascjtjq286s |
| Intertek | Wellhead Inspector | Stavanger | Dec 16, 2025 | not retrieved | not retrieved | not retrieved | not retrieved | not disclosed in listing type field | not retrieved | Job ID JOBSEARCH_100256 — https://to.indeed.com/aadbpj6crrny |
| Nordex Group | Service Technician Midtfjellet (wind turbine service technician) | Fitjar kommune | Sep 10, 2026 | not retrieved | not retrieved | not retrieved | not retrieved | not disclosed in listing type field | not retrieved (GWO is the standard cert body for wind-turbine techs generally, but not confirmed from this posting's text) | Job ID JOBSEARCH_100252 — https://to.indeed.com/aablwnt2vrt6 |
| DeepOcean | Operation Technician | Undheim | Sep 14, 2026 | not retrieved | not retrieved | not retrieved | not retrieved | Permanent (per listing) | not retrieved | Job ID JOBSEARCH_100257 — https://to.indeed.com/aajjjn8zpdyy |
| DeepOcean | "Bli med på industrieventyret på Jæren!" (recruitment/technician campaign ad) | Undheim | Sep 16, 2026 | not retrieved | not retrieved | not retrieved | not retrieved | Permanent (per listing) | not retrieved | Job ID JOBSEARCH_100259 — https://to.indeed.com/aabtm64cmldc |
| DeepOcean | Commissioning System Responsible – Telecommunication | Stavanger | Sep 04, 2026 | not retrieved | not retrieved | not retrieved | not retrieved | Full-time (per listing) | not retrieved | Job ID JOBSEARCH_100261 — https://to.indeed.com/aaht2rhgywb9 |
| ＥＮＥＲＧＹ (listed as "ENERGY") | Commissioning System Responsible – Electro | Stavanger | Sep 03, 2026 | not retrieved | not retrieved | not retrieved | not retrieved | not disclosed in listing type field | not retrieved | Job ID JOBSEARCH_100264 — https://to.indeed.com/aadzf7z2r9vl |

That is **9 core postings**, meeting the 8–12 target. All were returned directly by the tool; none were fabricated or estimated.

### Adjacent/borderline postings (industrial/offshore-support roles, surfaced by the same searches but not core rope-access/inspection roles — included for completeness/transparency, not counted toward the 8–12 target)

| Company | Job title | Location | Posted date | Notes | Source |
|---|---|---|---|---|---|
| Atlas Copco Group | Field Service Engineer / Technician | Stavanger | Sep 14, 2026 | General industrial field service, not rope-access specific | Job ID JOBSEARCH_100258 — https://to.indeed.com/aannc4wc8h7p |
| Aggreko | Field Service Technician – Temporary Power, Cooling & HVAC | Tananger | Sep 24, 2026 | Offshore-support equipment technician, not rope-access | Job ID JOBSEARCH_100260 — https://to.indeed.com/aayt9lxcg92f |
| CHC Helicopters | Engineer/aircraft mechanic | Sola | Mar 11, 2026 | Offshore-support (helicopter transport), not rope-access | Job ID JOBSEARCH_100262 — https://to.indeed.com/aa8d66d4dvtp |
| NOV | Service Engineer – Mechanical & Hydraulic | Stavanger | Sep 23, 2026 | General oilfield equipment service, not rope-access | Job ID JOBSEARCH_100263 — https://to.indeed.com/aadv4fkqlxch |

### Searches that returned zero results
"rope access technician" (Stavanger, Norway/remote), "rope access" (Bergen), "tilkomsttekniker" (Bergen, Sandnes), "offshore technician" (Haugesund), "industriklatrer" (Norway) all returned "No job results found. Please try expanding your search criteria." Several additional planned searches ("riggerier", "SOFT tekniker", "offshore inspector" nationwide, "vindteknikker", "rigger" Stavanger, "tilkomsttekniker" Sandnes) could not be executed at all because the Indeed tool's rate limit was exhausted for the rest of the session (see Methodology above) — these should be re-run in a follow-up session.

## Norway income tax and social security facts (2026, single filer, no dependents)

**Caveat on sourcing:** skatteetaten.no (the Norwegian Tax Administration) could not be reached directly — WebFetch to www.skatteetaten.no was blocked by the network egress proxy in this environment on every attempt. The figures below come from web-search result summaries (search snippets, not full-page fetches) of secondary tax-guide sites (countrytaxcalc.com, taxxeo.com, finanskunnskap.no, ourtaxpartner.com, aiderlegal.com) referencing 2026 figures, cross-checked against each other and against Skatteetaten's own page titles as they appeared in search results. Where sources disagreed, both values are given and flagged.

### Alminnelig inntekt (general/ordinary income tax)
- Flat rate: **22%** on ordinary income (gross income minus standard deductions such as personfradrag and minstefradrag). — [Norway Income Tax Guide 2026](https://www.countrytaxcalc.com/tax-guides/norway-income-tax-guide-2026/); [How much is tax in Norway?](https://taxxeo.com/how-much-is-tax-in-norway-current-rates-and-brackets/)

### Trinnskatt (bracket tax) — 2026 rates and thresholds, on top of the 22% base
Per search-result summary of countrytaxcalc.com's 2026 guide:
- 0% up to NOK 226,100
- 1.7% from NOK 226,101 to 318,300
- 4% from NOK 318,301 to 725,050
- 13.7% from NOK 725,051 to 980,100
- 16.8% from NOK 980,101 to 1,467,200
- 17.8% on income above NOK 1,467,200
— [Norway Personal Income Tax Rates (2026)](https://taxatlas.io/country/norway/income-tax); [Norway Trinnskatt (Step Tax) Explained 2026](https://www.countrytaxcalc.com/tax-guides/norway-trinnskatt-explained-2026/)

Note: one summary described the top bracket rate as "17.6%" rather than "17.8%" when stating the combined marginal rate — this small discrepancy (17.6 vs 17.8) was not resolved between sources and should be verified against the primary Skatteetaten rate table before use in precise net-pay calculations.

### Trygdeavgift (national insurance contribution) — employment income
- Reported as **7.6%** on gross wage income for employees aged 17–69 by most sources found; one source separately cited **7.9%**. The sources disagreed and could not be reconciled without reaching skatteetaten.no directly (blocked). **Treat 7.6% as the better-supported figure for 2026 but verify against the primary source before finalizing net-pay math.** — [Net Salary Calculator Norway 2026](https://app.expatriation.io/net-salary/norway); [Norway Income Tax Calculator 2026](https://www.countrytaxcalc.com/tax-calculator/norway/)
- Trygdeavgift is calculated on gross income (not reduced by deductions) and is charged in addition to alminnelig inntekt tax and trinnskatt.

### Personfradrag (personal allowance/deduction) — 2026
- **NOK 108,550** — this was the figure most consistently supported across sources (finanskunnskap.no, ourtaxpartner.com). — [Personal Deduction (Personfradrag) in Norway: 2025 & 2026 Updates](https://www.ourtaxpartner.com/personal-deduction-personfradrag-in-norway-2025-2026-updates/); [Personfradrag 2026: Bunnfradrag og skattefri inntekt](https://finanskunnskap.no/personfradrag-2026/)
- One source cited NOK 114,540 instead — flagged as a discrepancy, not resolved.
- Personfradrag is subtracted from gross income before the 22% ordinary-income tax is applied; it is worth roughly NOK 23,881 in actual tax saved (108,550 × 22%). It does **not** reduce the trinnskatt or trygdeavgift bases, which are calculated on gross income.
- Minstefradrag (a separate, general "minimum deduction," calculated as 46% of gross employment income, capped at NOK 104,450 for 2026) also applies to reduce ordinary income and is commonly confused with personfradrag — the two are distinct.

### Combined marginal rate
Approximate combined **top marginal rate on employment income ≈ 47.4%** (22% ordinary income tax + ~17.6–17.8% top trinnskatt bracket + ~7.6–7.9% trygdeavgift), per search-summary sources. This is the effective top-bracket rate for very high earners; most offshore technician salaries will fall in the middle trinnskatt brackets (4% or 13.7%), not the top bracket.

### Offshore/continental-shelf-specific tax treatment (flagged as directly relevant to this project)
- **Continental shelf workers who reside abroad**: Norway has a specific tax regime for offshore petroleum workers under the Petroleum Tax Act / "offshore" tax rules. Foreign-resident continental shelf workers can, in some circumstances, be taxed in Norway on their offshore employment income under progressive Norwegian personal tax rules similar to ordinary residents. There is also a live legislative proposal to **extend** the continental-shelf taxing right to cover foreign residents' employment income from renewable energy (offshore wind), carbon management, and mineral activities on the shelf, not just oil and gas — relevant given the project's interest in offshore wind roles too. — [Continental shelf workers resident abroad — Skatteetaten](https://www.skatteetaten.no/en/person/foreign/are-you-intending-to-work-in-norway/continental-shelf-workers-seafarers-artists-and-sportspersons/continental-shelf-workers/); [Proposed extended tax liability for foreign companies on the Norwegian continental shelf — EY Norway](https://www.ey.com/en_no/insights/tax/proposed-extended-tax-liability-for-foreign-companies)
- **Free board/lodging on an offshore installation is normally a taxable fringe benefit**, reported under the specific Skatteetaten category "board – offshore workers," using annually-set standard daily rates (found for a nearby year: NOK 151/day for free accommodation, NOK 107/day for free board with all meals, NOK 83/day for free board with two meals — these are the benefit valuation rates used to add the value of "free" offshore room and board back into taxable income, not tax-free per-diems). — [Board – offshore workers — Skatteetaten](https://www.skatteetaten.no/en/business-and-organisation/employer/the-a-melding/the-a-melding-guide/salary-and-benefits/overview-of-salary-and-other-benefits/board-offshore-workers/)
- **Threshold for foreign-resident offshore workers**: if a foreign-resident offshore worker's income exceeds NOK 600,000, free board becomes taxable (implying it may be treated as non-taxable below that threshold in some circumstances) — this rule was only found in a search-result summary, not confirmed against the primary Skatteetaten page text (which could not be fetched directly), so it should be double-checked.
- **Standard 10% deduction interaction**: offshore/foreign workers who claim the 10% standard deduction available to some foreign taxpayers cannot simultaneously claim separate deductions for board, lodging, and travel costs — claiming both is disallowed and would make employer-covered expenses taxable.
- **Rotation patterns** (not a tax rule, but relevant context for net-pay/annualization modeling): the standard Norwegian Continental Shelf rotation is commonly **2 weeks on / 4 weeks off** for production platforms, and **2/2 or 2/3** for drilling rigs — per general web-search summary, not from a specific job posting in this search (none of the postings found had their description text retrieved due to the rate-limit issue above). — search-summary citing general industry sources.

### Gaps / what still needs verification
- Exact trinnskatt top-bracket rate (17.6% vs 17.8%) unresolved between sources.
- Trygdeavgift rate for 2026 unresolved between 7.6% and 7.9% — this alone shifts net-pay estimates meaningfully and should be pinned down against the primary Skatteetaten rate table (site was blocked from direct fetch this session).
- Personfradrag amount unresolved between NOK 108,550 and NOK 114,540.
- No verbatim pay, rotation, accommodation, overtime, employment-type (contractor vs. employee), or certification-requirement text was retrieved from any of the 9 core job postings, because `get_job_details` calls were blocked by persistent Indeed API rate limiting for the entire remainder of this session. This is the single biggest gap relative to the assignment's objective and should be the first thing re-attempted in a follow-up pass.
- The 600,000 NOK free-board taxability threshold for foreign-resident offshore workers needs primary-source confirmation.
