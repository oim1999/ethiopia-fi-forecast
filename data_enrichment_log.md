# Data Enrichment Log — Task 1

This log documents every record added to the starter dataset
(`ethiopia_fi_unified_data.csv`, 57 records) to produce the enriched dataset
(`data/processed/ethiopia_fi_unified_data_enriched.csv`, 74 records). It follows the
schema's data-entry rules: observations/targets get a `pillar`, events get a `category`
and no `pillar`, and impact_links get a `pillar` (of the affected indicator) plus a
`parent_id` pointing back to their event.

**17 new records added: 9 observations, 1 target, 3 events, 5 impact_links.**

All additions were selected to close specific gaps identified during exploration
(`notebooks/01.ipynb`, Sections 4–7): the missing pre-Telebirr 2020
baseline, the complete absence of the core Findex "digital payment adoption" metric, two
events (NFIS-II and M-Pesa/EthSwitch interoperability) with incomplete or no impact_links,
and a thin evidence base on gender-related policy.

Collected by: **Selam Analytics – Data Team** · Collection date: **2026-07-19**

---

## Observations & Targets

### REC_0034 — Account Ownership Rate, 2020 = 45%
- **pillar:** ACCESS · **indicator_code:** ACC_OWNERSHIP
- **source_url:** https://nbe.gov.et/wp-content/uploads/2023/12/National-Financial-Inclusion-Stratgy-II-2021-2025.pdf
- **original_text:** "financial inclusion levels have increased markedly – from 22% to an estimated 45% in 2020"
- **confidence:** high (primary NBE strategy document)
- **why useful:** The starter dataset jumps from the 2017 Findex point (35%) straight to the
  2021 Findex point (46%), with no marker for where Ethiopia stood immediately *before*
  Telebirr launched (May 2021). This NBE-reported 2020 figure gives Task 3/4 a clean
  pre-intervention baseline for isolating Telebirr's effect from organic pre-existing growth.

### REC_0035 / REC_0036 — Account Ownership by Gender, 2024 (male 56.53% / female 41.62%)
- **pillar:** ACCESS · **indicator_code:** ACC_OWNERSHIP · **gender:** male / female
- **source_url:** https://rsisinternational.org/journals/ijrsi/uploads/vol12-iss10-pg3863-3872-202511_pdf.pdf
- **original_text:** "women in Ethiopia (41.62%) having notably lower ownership rates than men (56.53%) in 2024"
- **confidence:** medium (secondary academic analysis of Findex microdata, n=1,001 — not a
  primary Findex publication table)
- **why useful:** The 2021 wave already has male/female disaggregation in the starter data
  (REC_0004/REC_0005); 2024 didn't. This lets us track the gender gap trend across both
  survey waves rather than relying only on the pre-computed `GEN_GAP_ACC` figures.
- **⚠️ documented discrepancy:** these two values imply a ~14.9pp gender gap for 2024, while
  the starter dataset's REC_0028 (`GEN_GAP_ACC`, direct survey source) reports 18pp for the
  same year. Both are plausible readings of Findex 2024/2025 depending on rounding and
  exact question wording; **we did not reconcile them**, and flag this as a data-quality
  limitation for the EDA / modeling stages rather than silently picking one.

### REC_0037 / REC_0038 — Mobile Subscriptions (count), June 2020 = 74.1M / June 2024 = 269.4M
- **pillar:** ACCESS · **indicator_code:** ACC_MOBILE_SUBS *(new indicator)*
- **source_url:** https://ethiopiafinanceforum.com/wp-content/uploads/2025/05/May_15_Presentation_EFF.pdf
- **original_text:** "Increased from 74.1 mn in June 2020 to 269.4 mn in June 2024 (Ave. Growth of 65.1%)"
- **confidence:** medium (conference/presentation slide rather than a primary NBE report)
- **why useful:** Raw mobile subscription counts are a plausible leading indicator/enabler
  for both mobile-money account growth and digital payment usage, complementing the existing
  `ACC_MOBILE_PEN` percentage (which only has a single 2025 data point).

### REC_0039 / REC_0040 — Digital Payment Adoption Rate, 2021 = 20% / 2024 = 35%
- **pillar:** USAGE · **indicator_code:** USG_DIGITAL_PAYMENT *(new indicator)*
- **source_urls:**
  https://blogs.worldbank.org/en/africacan/mobile-phone-technology-could-expand-equitable-access-financial-services-ethiopia (2021)
  https://www.worldbank.org/en/publication/globalfindex (2024, as cited in the project brief)
- **original_text (2021):** "Only 42% of account holders – 20% of adults – used their accounts for digital payments"
- **original_text (2024):** "Made or received digital payment: ~35%"
- **confidence:** medium for both (2021 figure is from a WB blog post rather than the primary
  Findex table; 2024 figure is taken from the assignment brief's own citation and not
  independently re-verified against raw microdata)
- **why useful — this is the single most important addition.** "Digital Payment Adoption
  Rate" is explicitly named in the assignment brief as one of the **two core forecasting
  targets** (alongside Account Ownership), yet it was **completely absent** from the starter
  dataset, which only contained proxy/operator metrics (P2P transaction counts, Telebirr
  users, etc.). Without this addition, Task 4's Usage forecast would have had no direct
  Findex-comparable target series to model.

### REC_0041 — Used Account to Receive Wages, 2024 = 15%
- **pillar:** USAGE · **indicator_code:** USG_WAGE_DIGITAL *(new indicator)*
- **source_url:** https://www.worldbank.org/en/publication/globalfindex
- **original_text:** "Used account to receive wages: ~15%"
- **confidence:** medium (brief-cited Findex figure, not independently re-verified)
- **why useful:** A "depth of usage" indicator tied to formal-sector employment; per the
  Data Enrichment Guide (Sheet B/C), wage digitization is a direct-correlation indicator for
  Usage and a plausible feature for distinguishing "opened an account" from "actively uses
  it," which is central to explaining the 2021–2024 slowdown.

### REC_0042 — Target: Account Ownership Gender Gap = 10pp by 2025
- **record_type:** target · **pillar:** GENDER · **indicator_code:** GEN_GAP_ACC
- **source_url:** https://nbe.gov.et/wp-content/uploads/2025/05/WFISC.pdf
- **original_text:** "halving the account ownership gap – from 19 percentage points in 2020 to 10 percentage points by 2025"
- **confidence:** high (primary NBE strategy document)
- **why useful:** The starter dataset had ACCESS and GENDER share-related targets
  (REC_0031, REC_0033) but no explicit gender-*gap* target, even though gender gap is a
  named pillar and a headline NFIS-II commitment. Complements REC_0035/REC_0036 for
  gender-gap trend analysis.

---

## Events

### EVT_0011 — Bank Corporate Governance Directive (SBB/91/2024)
- **category:** regulation · **pillar:** *(intentionally empty)*
- **source_url:** https://nbe.gov.et/wp-content/uploads/2024/06/SBB912024-BANK-CORPORATE-GOVERNANCE-.pdf
- **date:** 2024-06-12 · **confidence:** high
- **original_text:** "Bank Corporate Governance (SBB/91/2024): including independent directors and board gender diversity"
- **why useful:** A concrete, dated regulatory event tied to Ethiopia's gender-inclusion
  push (mandatory female board representation at banks), giving the GENDER pillar its first
  linked policy event in the dataset.

### EVT_0012 — National Digital Payments Strategy, Phase One
- **category:** policy · **pillar:** *(intentionally empty)*
- **source_url:** https://nbe.gov.et/nbe_news/ethiopia-launches-phase-two-of-national-digital-payments-strategy-building-on-strong-momentum-from-phase-one/
- **date:** 2021-01-01 (approximate — see note) · **confidence:** medium
- **original_text:** "the first phase strategy (NDPS 2021–2024), which significantly expanded access to digital financial services nationwide"
- **note on date:** the source only specifies the strategy's 2021–2024 window, not an exact
  launch day; 2021-01-01 is used as a placeholder for "start of the period," and confidence
  is set to medium (not high) to reflect that imprecision.
- **why useful:** A major national policy event contemporaneous with Telebirr's launch;
  useful for disentangling "policy effect" from "Telebirr effect" in Task 3.

### EVT_0013 — National Digital Payments Strategy, Phase Two (NDPS 2.0)
- **category:** policy · **pillar:** *(intentionally empty)*
- **source_url:** https://nbe.gov.et/nbe_news/ethiopia-launches-phase-two-of-national-digital-payments-strategy-building-on-strong-momentum-from-phase-one/
- **date:** 2025-04-03 · **confidence:** high
- **original_text:** "the National Bank of Ethiopia today announced the launch of Phase Two of the National Digital Payments Strategy (NDPS 2.0)"
- **why useful:** The most recent major national policy event in the dataset — directly
  relevant to the 2025–2027 forecast window that Task 4 targets.

---

## Impact Links

| record_id | parent event | pillar | related_indicator | direction | magnitude | evidence_basis | rationale (abridged) |
|---|---|---|---|---|---|---|---|
| IMP_0015 | EVT_0011 (SBB/91/2024) | GENDER | GEN_GAP_ACC | decrease | low | theoretical | Gender board quotas are an institutional enabler, not a direct account-level driver — small, slow effect. |
| IMP_0016 | EVT_0009 (NFIS-II) | ACCESS | ACC_OWNERSHIP | increase | high | empirical | **Closes a gap found in EDA**: NFIS-II had zero impact_links in the starter data despite being a headline policy. Magnitude (+25pp) is NFIS-II's own stated target (45%→70%). |
| IMP_0017 | EVT_0009 (NFIS-II) | GENDER | GEN_GAP_ACC | decrease | medium | empirical | NFIS-II's explicit gender target: halve the gap from 19pp (2020) to 10pp (2025). |
| IMP_0018 | EVT_0013 (NDPS 2.0) | USAGE | USG_DIGITAL_PAYMENT | increase | medium | theoretical | Too recent (Apr 2025) for empirical Ethiopian evidence; magnitude set by analogy to Phase One's contribution, scaled down since Phase Two targets usage depth rather than first-time access. |
| IMP_0019 | EVT_0007 (M-Pesa/EthSwitch interop) | ACCESS | ACC_MM_ACCOUNT | increase | low | theoretical | Starter data only linked this event to USAGE (IMP_0011/IMP_0012); interoperability plausibly also lowers the barrier to opening a *first* mobile money account, at smaller magnitude. |

All five follow the schema's `impact_link` rules: `parent_id` references the event's
`record_id`, and `pillar` is set to the pillar of the **affected indicator**, never
pre-assigned to the event itself.

---

## Known Remaining Data Gaps (not addressed in this pass)

Documented here rather than filled with unverified numbers, per the project's
"don't force interpretation onto data" principle:

- **QUALITY, DEPTH, and TRUST pillars have zero observations.** No reliable Ethiopia-specific
  source was found for e.g. mobile money complaint/fraud rates, savings/credit product
  penetration, or system uptime in the time available.
- **No genuine 2011 Findex data point exists for Ethiopia.** Contrary to the "2011 = 14%"
  figure referenced in the project brief's own trajectory table, the Global Findex 2014
  report documentation states Ethiopia was **first included in the 2014 edition, not 2011**
  (source: gflec.org Global Findex 2014 report, listing "Ethiopia" among the 9 economies
  newly added in 2014). We therefore did **not** fabricate a 2011 record — this appears to
  be an inconsistency in the assignment brief itself, worth raising with stakeholders.
- **Urban/rural disaggregation** for account ownership was not located in the time available
  (only national and, for a subset of years, gender splits exist).
- **EthSwitch's underlying cross-domain Instant Payment System (IPS) launch date** is
  referenced in secondary literature (AfricaNenda) as having occurred sometime between 2013
  and 2023, but no primary source with an exact date was found — we chose not to add this as
  an event with a fabricated date. This is distinct from `EVT_0008` (EthioPay), a related but
  separate, precisely-dated infrastructure launch already in the starter dataset.

---

## Addendum — Record Added During Task 3 (Event Impact Modeling)

### IMP_0020 — Telebirr Launch → ACC_MM_ACCOUNT (+4.75pp, empirical)
- **parent_id:** EVT_0001 (Telebirr Launch) · **pillar:** ACCESS · **related_indicator:** ACC_MM_ACCOUNT
- **impact_estimate:** +4.75pp · **evidence_basis:** empirical · **lag_months:** 30
- **collected_by:** Selam Analytics – Data Team · **collection_date:** 2026-07-19
- **why added here, not in Task 1:** validating the model against real Ethiopian data
  (`notebooks/04_event_impact_modeling.ipynb`, Section 5) surfaced that the starter dataset's
  only Telebirr impact_link targets overall `ACC_OWNERSHIP`, leaving Telebirr's most direct,
  most obvious effect — mobile money account ownership itself (4.7% in 2021 → 9.45% in
  2024) — completely unlinked. The magnitude (+4.75pp) is not an assumption or
  literature-borrowed figure; it is the **directly observed change** in `ACC_MM_ACCOUNT`
  over that window, making this the single highest-confidence impact_link in the dataset.
  Added transparently and disclosed here rather than folded silently into the Task 1 log,
  since it was identified through the Task 3 validation exercise, not the original
  enrichment pass.

