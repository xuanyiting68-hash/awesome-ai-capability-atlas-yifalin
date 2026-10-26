# Consent-aware lead triage — first-party synthetic demonstration

**Scope:** a deterministic, local-only illustration of **explicit opt-in → purpose verification → deduplication/revocation → simple intent rule → human-review queue → auditable counts**.

This is *not* a deployed CRM, AI classifier, outbound marketing system, customer contact engine or legal clearance for personal-data processing.

## Run

Requires Python 3.10+ standard library; does not install anything or access the network.

```bash
python examples/consent_lead_triage/run_demo.py examples/consent_lead_triage/synthetic_leads.json --as-of 2026-10-27T00:00:00Z
python -m unittest scripts.test_consent_lead_triage -v
```

Expected sample result: **8 input records**, **3 eligible anonymous human-review suggestions**, **5 blocked**, **0 external actions**. IDs are invented; no contact information is present. Duplicate `demo-003` is rejected in both copies, including its opt-out record.

## Rules and limitations

- Only strict boolean `consent=true`, exact `contact_requested` purpose, non-opt-out and timezone-aware consent from the preceding 90 days qualify.
- Duplicate anonymous IDs are **all rejected**, including conflicting consent or withdrawals. No deduplication silently reactivates a user.
- Unknown or multi-topic requests go to `manual_review`. Keyword rules are deliberately NOT represented as an AI model.
- Personal messages are never copied to output. The report includes only anonymous IDs, heuristic category, block counts and human-review suggestions.
- No SMTP, CRM API, telephony, customer database, credentials or third-party libraries are used.
- Real deployments require documented consent notices, retention/deletion policy, regional legal review, lawful identity handling, withdrawal propagation, access controls, audit evidence, rate limits, and an independent privacy/security review.

**Acceptance benchmark:** check eligible count, opt-out, expired/future consent, repeated identity, absence of raw free text and zero outbound operations; tests are recorded in CI.
