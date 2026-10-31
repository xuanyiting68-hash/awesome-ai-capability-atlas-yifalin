# Industry × Occupation Taxonomy V1.3 — 2026-11-01

**Scope:** Extend the existing YIFALIN Atlas V1.2 instead of replacing its curated 32-sector application layer, 64 workflow pilots, 225 editorial role labels and 50 proposed emerging AI role families.

## Two independent classification axes

- **Economic activity / industry:** the organization's activities, rather than which occupations it employs. `industry_97_v13.csv` and `taxonomy_v13.json` provide **20 of 20 sections and 97 of 97 divisions** from the named GB/T 4754—2017 scheme. The **473 intermediate categories and 1,382 four-digit classes are NOT imported**; these are official published counts, not project data counts.
- **Occupation / tasks:** the work performed by a person. The Chinese 2022 official publication reports **1,639 occupations and eight major groups**. The public community mirror offers 8 major, 79 middle, 450 minor groups and 1,639 occupations. This project's `taxonomy.html` retrieves it **only after the user explicitly clicks** or accepts a local JSON upload, validates count and code uniqueness, then displays searchable records. Nothing is pre-populated as a purported verified dataset. The original source publication must be used for cross-checks. The mirror's claimed 450 minor groups must not be equated to older pre-release figures of 449/1,636.
- **Company job titles / synonyms:** these are not standardized occupations. Crosswalk by verified code (and location/time) before advertising coverage.
- **Emerging AI roles:** 50 editorial candidate roles in `career.html`, not a list of officially recognized professions or confirmed vacancies. No job demand/salary claims are imported here.

## Important provenance and rights

GB/T 4754—2017: https://www.stats.gov.cn/zs/tjws/tjbz/202301/t20230101_1903769.html

Chinese occupational taxonomy official release: https://www.ndrc.gov.cn/fggz/jyysr/jysrsbxf/202210/t20221031_1340470_ext.html

External community mirror: https://github.com/Optima-Chat/china-jobs — `data/occupations_raw.json` only. Its README says MIT but the repository root LICENSE was not found in this inspection. The project **does not copy/relicense the 1,639 records** or the site's subjective AI replacement-risk scores. Verify redistribution rights, code-name discrepancies and version updates before inclusion in a commercial product.

Official global expansion gateways: UN ISIC Rev.5 (https://unstats.un.org/unsd/classifications/Econ/isic), ILO ISCO-08 (https://isco.ilo.org/en/isco-08/), Australia OSCA 2024 v1 (https://www.abs.gov.au/statistics/classifications/osca-occupation-standard-classification-australia/2024-version-1-0/comparison-isco-08), US O*NET 31.0 (https://www.onetcenter.org/database.html), EU ESCO (https://esco.ec.europa.eu/en/use-esco/download). These are **source gateways only**, not imported foreign taxonomies. O*NET 31.0 contains 1,016 occupation data rows and permits attribution-based reuse under CC BY 4.0 (verify scope and attribution before use).

## Interactive use

1. Open `taxonomy.html` and filter by 20 industries, 97 industry divisions, name or code. Export filtered results to CSV.
2. On the occupation tab, click "load community mirror" if network allows, or obtain the JSON from the source and upload it using the file picker. The file is processed locally; this page does not transmit occupation searches or personal information.
3. Filter occupations by major group, middle group, code or name; display an **editorial task-level AI starter pilot** rather than an unsupported replacement probability.
4. Link to `career.html` for emerging AI-role study and `expert.html` for scenario pilots.

## Current omissions and next research gates

| Layer | Current state | Gap |
| --- | --- | --- |
| China industries | 20 sections / 97 divisions in local data | 473 groups / 1,382 classes not loaded |
| China occupations | 8 major groups encoded; full 1,639 source import enabled | individual official record verification; 79 middle groups are loaded from mirror, not built in offline |
| Global taxonomy | verified source gateway references | actual official data import/crosswalk missing |
| Company role titles | previous 225 role labels | synonyms, alternative titles, organizational mappings not evidence-backed |
| AI new roles | previous 50 editorial families | employer evidence, labor market frequency, skills validation missing |
| AI pilots | major-group illustrative primers | per-occupation *task* assessment, consent, time/cost/quality baselines missing |

**Do not conflate:** published classification breadth, imported directory rows, checked source links, actual role demand, skill qualification equivalence, safe automation readiness and proven productivity impact.

## Tests

- `python build_taxonomy_v13.py` — regenerates 20/97 taxonomy JSON and CSV.
- `python build_taxonomy_ui_v13.py` — regenerates standalone HTML.
- `python check_taxonomy_v13.py` — counts, identifiers and Playwright Desktop/390px browser interactions, including a **synthetic** 1,639-record import fixture. The synthetic test records are never shipped as real occupational data.

**Publication HOLD** until code QA, source and license review, more detailed official standard layers, and real-user industry testing. No external connectors, model APIs, dangerous actions, transactions or orders are executed.