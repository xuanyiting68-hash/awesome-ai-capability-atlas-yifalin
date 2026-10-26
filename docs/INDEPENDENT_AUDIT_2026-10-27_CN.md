# 2026-10-27 Independent Quality Audit — YIFALIN Global AI Capability Atlas

**Scope:** GitHub `main` at `1a2a1325a6d26921c7244b66cfe1a99700c887fc`; historical PR #3/#4/#5; independently inspected repository tree, release allowlist, tests, data provenance and workflows. Repair branch: `fix/atlas-restore-project-blueprints-pages`, Draft PR #6.

## 1. Verified baseline vs. unverified claims

| Check | Observation | Evidence |
| --- | --- | --- |
| PR #3 | MERGED (not an open Draft) | https://github.com/xuanyiting68-hash/awesome-ai-capability-atlas-yifalin/pull/3 |
| Prior live release | Pages + online smoke succeeded for main `1a2a132...` | https://github.com/xuanyiting68-hash/awesome-ai-capability-atlas-yifalin/actions/runs/40324578773 |
| Catalog | 5,000 index rows per committed provenance and CI tests; 133 editor-curated and 4,867 candidates | `data/provenance.json` |
| GitHub metadata | 133 curated repositories; 33 without recognized SPDX identification | `data/repo_metadata.json`, snapshot 2026-10-26T12:42Z |
| Top 30 | 30 research priorities, 30 HOLD decisions, no reviewed licenses, no demonstrated sandbox reproductions | `data/top30_evaluation.csv`, `data/top30_evidence.json` |
| Browser | Existing Top 30 suite has 17 passing Chrome scenarios in PR #6; staged Pages smoke newly confirms 10 blueprint cards + project detail at 1440/768/390 | https://github.com/xuanyiting68-hash/awesome-ai-capability-atlas-yifalin/actions/runs/40344426390 |
| Visual inspection | Chrome screenshots are uploaded by CI; this audit did not manually inspect screenshots pixel by pixel | Screenshot artifact in the linked workflow |
| Current repair production | **NOT DEPLOYED.** PR #6 is Draft and `main` is unchanged by this branch | PR #6 |

**Source interpretation:** a metadata URL, SPDX indication, star count, or recent push is neither evidence of safety nor evidence of a granted commercial-use license. An illustrative blueprint is not a working external automation.

## 2. Findings and disposition

### P0 — Broken published routes / incomplete shipped functionality
- **Observed:** historical `project.html`, `blueprints.html`, `data/business_use_cases.json` existed on `feat/v1-4-top30-evaluation`, but were absent from newer `main` and the release allowlist. Top 30 had no project details links, so the historical delivery was not accessible on the published artifact.
- **Repair:** selectively recover only those three assets, add live Top 30/home links, extend the Pages allowlist and add build-time correspondence checks across project CSV, metadata, evidence and domain blueprints. Tested with real Chrome against the staged artifact.
- **Status:** repaired in PR #6; merge/deploy still gated.

### P1 — Evidence-driven usability and trust
- **Incomplete:** 0/30 reviewed or reproduced Top 30 projects; all remain HOLD. 33/133 repository metadata records lack a recognized SPDX code. These gaps must be surfaced as *unknown/unreviewed*, not interpreted as unsafe or permitted.
- **Incomplete:** cards predominantly use text, initial-letter logo tiles and metadata; there are no traced official project demos or reproducible worked examples. Add authorized media with attribution and dated references only.
- **Incomplete:** `index.html` is a ~110 KB single-document implementation with deeply coupled inline JS, embedded curated seed data and duplicated source information. Progressive modularization is advised, with snapshot/URL/bookmark backward compatibility tests.
- **Incomplete:** homepage, project-detail and blueprint copy are primarily Chinese; Top 30 supports an English workspace. A sitewide locale model is needed instead of cosmetic labels.
- **Incomplete:** video production, CRM, finance research, and the wider lead-to-CRM pipeline remain static proposals. They must retain their illustrative status. A narrower **first-party synthetic consent gate / rule-based triage / human-review output** demonstration is implemented under `examples/consent_lead_triage` with standard-library CLI and CI tests; it is not an external integration.
- **Fixed in PR #6:** homepage formerly pointed to `github.com/new` rather than this project, hid the recovered blueprint page, and displayed an initial hardcoded 30-source count before data load.

### P2 — Catalog and long-term architecture
- **Provenance concentration:** three sources account for 3,336 of 4,867 candidates (OpenClaw 1,286; sickn33 1,100; n8n 950), approximately 68.5% of the discovery-only pool. A 5,000-row capacity is a cap, not full global coverage.
- **Content depth:** project descriptions/strengths are editorial research hypotheses. No objective setup, benchmark, failed run, or security experiment is available for most entries.
- **Automation:** data collectors write to main, protected by serial execution and rebase rather than force-push; prior stale-checkout failure was recorded and repaired in PR #5. Reassess branch protection, pinned action integrity, stable snapshots and full rollback procedures in a separate security track.

## 3. Quality tier requirements

Promotions must be justified by **separately stored, immutable and traceable evidence**, not popularity:

| Tier | Minimum promotion gate | Current baseline |
| --- | --- | --- |
| Discovery | canonical source URL, identity, source retrieval timestamp, deduplication | 4,867 external candidates |
| Curated | editorial use case and target audience, researched alternatives and decision rationale | 133 editor-selected repositories; not safety-reviewed |
| Reviewed | checked LICENSE text and scope, dependency/asset terms, maintenance, permission and security desk review | no validated promotions |
| Reproduced | sandbox environment, pinned commit/digests, documented command, inputs, expected vs observed output, failures, cost and independent rerun | no validated promotions |
| Production Candidate | reproducible functional results, deployment/rollback plan, legal/privacy/security gate, operational owner and cost constraints | no validated promotions |

**Important:** the 30 Top 30 entries are an evaluation queue, not 30 reproduced or production-approved projects.

## 4. Next engineering work (do not inflate version numbers)

1. Keep Draft PR #6 isolated until its exact-head tests and screenshot artifacts are checked and Owner merges/reviews for publication.
2. Split site data and UI into testable modules. Preserve `atlas_favorites_v1`, URL filters, CSV formula neutralization, page URLs and stable catalog IDs.
3. Introduce a typed evidence schema with links, last-checked timestamps, reviewers, test fixtures and explicit UNKNOWN states; migrate selected records incrementally.
4. Expand the tested synthetic consent-gate pilot toward a fully offline, synthetic opt-in form → lead-to-CRM adapter with realistic revocation propagation and security controls; keep production service integration disabled. Separately implement a first-party video subtitle pipeline with authorized inputs.
5. Build one finance research workflow from redistributable public data with provenance, time-split baseline, traceable citations and no live trading connection.

## 5. Boundaries
No production credentials used, no upstream skills executed, no financial services integrations, no external customer messaging. Historical illustrative site content was restored and one new synthetic first-party CLI example was added; no third-party software execution, licensing or security conclusions are implied. A passing staged smoke test is not evidence of a successful **new production deployment**.
