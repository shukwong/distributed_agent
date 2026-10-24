# Proposed public-data pilot: LUAD mutation associations

Status: scoped on 2026-10-24; protocol agreement and implementation remain pending.
The user selected cancer and mutations. No mutation outcomes were inspected and
no biological analysis or model report has run for this pilot. This is a concrete
proposal for the next milestone, not a completed analysis or a registered study.

## Question and scope

Which pairwise somatic mutation associations among **BRAF, EGFR, KEAP1, KRAS,
STK11 and TP53** are supported in primary lung adenocarcinoma after specified
burden/context adjustment, and corroborated in a held-out external cohort?

Test all 15 unordered pairs, chosen before outcome retrieval. This first public
pilot measures reproducibility, denominator handling and evidence quality.
Literature-known patterns provide context; recovering a particular association
is not a pass condition and does not establish novelty, mechanism or therapy.
Survival, drug response, copy-number changes and fusions are outside this pilot.

## Sources verified so far

| Role | cBioPortal study | Advertised sequenced samples | Setting |
| --- | --- | ---: | --- |
| Development | `luad_tcga_pan_can_atlas_2018` | 566 | TCGA LUAD; restrict to eligible primary stage I–III cases |
| External holdout | `luad_mskcc_2020` | 604 | Resected stage I–III LUAD; published primary-tumor cohort |

These are source inventory counts, not final analysis denominators. Both mutation
profiles are sample-level `MUTATION_EXTENDED`/MAF, reported as hg19. Metadata and
file-size evidence are recorded in [sources.json](sources.json). The MSK paper
describes 604 resected patients; resection does not establish absence of prior
treatment. [TCGA metadata](https://www.cbioportal.org/api/studies/luad_tcga_pan_can_atlas_2018),
[MSK metadata](https://www.cbioportal.org/api/studies/luad_mskcc_2020),
[Caso et al.](https://pmc.ncbi.nlm.nih.gov/articles/PMC7704768/).

MSK uses IMPACT341 (8 samples), IMPACT410 (190) and IMPACT468 (406). All six
genes occur in every observed panel. Use actual member lists, not panel-name
numbers; IMPACT468 currently returns 469 gene records. TCGA profiling flags and
its WES description provide nominal assay eligibility, not per-base coverage.
[Panel documentation](https://docs.cbioportal.org/file-formats/#gene-panel-data).

Clinical fields exist for age, sex, pathologic stage and burden in both cohorts.
MSK also exposes smoking history and pack-years. **The current TCGA clinical
schema does not expose smoking history.** Completeness, category harmonization,
treatment history and per-sample coverage have not been audited. They must not
be presented as verified or fully controlled.

DepMap remains a useful later functional extension. The current standard Broad
CRISPR matrix includes Project Score, making an unqualified Sanger validation
non-independent. Its download/version and donor-source separation also need
additional work. [Official integration note](https://forum.depmap.org/t/organoid-dependency-data/4671/7).

## Analysis population and mutation definition

- Independent observation: one patient. Report task: one gene pair, with both
  cohorts kept distinct. Never count variants, biopsies or agents as replicates.
- Require explicit sample-to-patient mapping, mutation-profile membership and
  nominal assay coverage of both genes. Missing profiling/panel information is
  unknown, not an unaltered observation. Flag calls inconsistent with panels.
- Include primary stage I–III LUAD. Prefer a documented primary resection sample;
  resolve repeated eligible samples by earliest recorded collection date, then
  lexical sample ID. If dates are unavailable, use lexical ID and disclose that
  it is a reproducible choice, not proof of the first or untreated sample.
- Map stage to I/II/III with a frozen dictionary. Exclude unknown stage and
  nonprimary/ambiguous cases; retain exclusion counts. Establish mappings using
  metadata only before any pairwise results are viewed.
- Use the fixed nonsynonymous SNV/small-indel classification list in
  [protocol.json](protocol.json). Exclude silent/noncoding calls, CNA, structural
  variants and fusions. Use the source's somatic-call provenance; do not infer
  germline status from population frequency.
- Deduplicate repeated annotations of the same sample/variant key; a patient
  contributes at most one positive observation per gene. Broad nonsynonymous
  status includes variants of uncertain function and does not mean oncogenicity.
- Use the label **no qualifying mutation detected among nominally assayed cases**,
  not biological wild type. Actual detection sensitivity remains uncertain.

## Deterministic statistics

Analyze each cohort separately. Do not pool their patients to manufacture power.
For every pair, retain all four patient counts, assay/clinical exclusions,
mutation frequencies, unadjusted odds ratio, interval and two-sided Fisher p.
Fisher results are descriptive comparators, not the selection criterion.

The proposed primary model is Firth logistic regression: alphabetically first
gene as exposure and second as outcome; age in decades, recorded sex, stage
I/II/III, and `log1p(background_variant_count)` as covariates. Add panel as a
categorical covariate in MSK. Use penalized profile-likelihood tests and 95%
intervals, record convergence and finite/infinite bounds, and pin the R/package
versions during implementation. Remove constant covariates using a fixed rule;
do not select covariates using p values. Firth estimation addresses separation,
but cannot remove unmeasured confounding or make sparse data informative.
[Maintainer documentation](https://georgheinze.r-universe.dev/logistf).

Compute background count from the **same filtered variant records** within the
intersection of the observed IMPACT panels, excluding all six hypothesis genes.
Apply that identical gene set to TCGA. This is a panel-restricted count, not
mutations per megabase. It avoids subtracting incompatible counts from the
provider's `MUTATION_COUNT` and reduces direct coupling with the tested calls.
Do not pool panel TMB and exome TMB as interchangeable measurements. Heterogeneous
mutation propensity can create apparent co-occurrence; adjustment remains a
model assumption, not proof that all such bias is removed.
[Methodological motivation](https://doi.org/10.1186/s13059-016-1114-x).

Primary fits use complete covariate cases. Require at least 100 eligible patients,
at least 20 mutation-positive and 20 negative observations for each gene, and
at least 80% retention after clinical missingness exclusions (complete cases
divided by the pair's eligible, deduplicated and assay-qualified patients before
clinical covariate exclusion). These are proposed
stability gates, not a power calculation. Otherwise retain descriptive counts
and mark the adjusted test `not_evaluable`; do not expand the cohort or gene list.
Rank-deficient or nonconvergent fits are also `not_evaluable`.

Report Holm correction over the fixed 15 two-sided tests within each cohort.
For external statistical support, form `p_conjunction=max(p_TCGA,p_MSK)` for
each pair and apply Holm across the 15 conjunction p values; require corrected
p≤0.05 and matching adjusted effect signs. This intersection-union test requires
support in both cohorts and does not assume independence of their p values.
Use p=1 for unavailable tests in correction, while retaining their missing
status. Separate within-cohort corrections alone are not the replication rule.
Report every pair, including failures and nulls. Failure to reject does not
establish absence of association.

Mandatory sensitivity omits background burden from the primary model on the
same cases, since burden and stage can reflect disease biology as well as
confounding. A direction reversal is labeled sensitivity-conflicted.
Mandatory MSK sensitivity adds harmonized smoking history (never/ever) on cases
with known history; compare the base and extended models on the same subset.
Report pack-years and histologic-subtype sensitivities only if the corresponding
metadata mapping was frozen before outcomes. They are exploratory and cannot
rescue a failed primary test. Smoking sensitivity is supported only if its
effect sign agrees with both the same-subset base model and full primary model,
and its 95% interval excludes 1; an interval crossing 1 is
inconclusive, and failed eligibility is not evaluable. A sign reversal is
sensitivity-conflicted. These labels do not change the primary p values.
TCGA residual smoking confounding remains
explicit even if MSK sensitivity agrees. Prior treatment, purity and detection
differences also limit interpretation.

## Holdout and controls

Freeze the protocol, source versions, code, metadata mappings and eligibility
rules before retrieving MSK mutation outcomes. Develop using synthetic fixtures
and TCGA only. Restrict the analysis workers' mounts so they cannot see withheld
MSK files. Release the holdout once, after the implementation review; changes
made after observing it require a new protocol version and exploratory labels.
Published literature is already known, so scientific expectations are not blinded.

Different TCGA/MSK identifiers do not prove different people. Audit cohort
provenance, available crosswalks and duplicate sample identifiers. Review any
available cross-cohort duplicate flags before testing; retain an overlap
exclusion ledger. Claim **independent replication** only if disjointness is
adequately supported. Otherwise use **external corroboration with unresolved
overlap**; do not silently substitute another MSK or TCGA release as replication.
[cBioPortal overlap guidance](https://docs.cbioportal.org/user-guide/faq/).

Required implementation checks include known synthetic independence/association,
separation, duplicate patients, multiple variants per gene, unassayed genes,
missing covariates, variant-class exclusion and source-hash mismatch. Run a
bounded synthetic global-null simulation (100 replicates, seed 20261024), report
the familywise rejection rate and its interval, and stop to investigate if the
interval's lower bound exceeds 0.05. This is a coarse diagnostic, not a proof of
calibration. Do not invent a real gene pair as a guaranteed biological null or
tune the method to recover a literature relationship.

## Agent contract and bounded workload

The current builder describes mouse-brain Perturb-seq. **Do not feed these
patient data to that prompt.** Implement a separate versioned contract using
[report_contract.md](report_contract.md), preserve the legacy contract, and add
an explicit contract selector before live runs. This pilot is not executable
with the current builder unchanged.

Deterministic code computes and validates all 15 pair results. Models receive
only aggregate, hashed Parquet inputs and a small curated source packet, never
patient IDs or raw clinical rows. The first agent batch covers three predeclared
pairs: EGFR–KRAS, KRAS–STK11 and KEAP1–STK11. Each report summarizes the two cohorts
and their caveats. Generate fixed-template reports for the other 12 pairs from
the deterministic table; label their provenance `report_import`. Thus the final
corpus covers all 15 pairs, with three model-authored and 12 deterministic reports.
Unevaluable pairs retain evidence-backed feasibility findings, not biological
negative claims. Run one native query over the complete corpus and require it to
account for all 15 pairs, including exclusions and unsupported associations.

Proposed limits: ≤512 MiB selected input download, ≤2 GiB working outputs,
one CPU/8 GiB RAM and a 90-minute stage wall limit; no GPU. Stream the mutation
files instead of loading the full TCGA table into memory. No full study archives
or RNA matrices are needed. The two advertised MAFs total about 234 MB; their
LFS SHA-256 values are in the source manifest. Verify downloaded bytes before use.

At most three live report builds plus one query, each ≤240 seconds, sequential,
with both sandboxes enabled and no automatic model retry. A 300,000 total-token
launch-stop threshold is proposed: check reported aggregate usage before each
next invocation. **It is not a hard token or spending cap**, and one invocation
can overshoot it. Record actual usage; no additional model calls without review.
Parallel scale is a separate later milestone requiring an adequate allocation.

## Next concrete steps

1. Agree this tumor/question, fixed family, holdout rules and bounded scope.
2. Pin source commits/payload hashes; audit metadata completeness, sample mapping,
   stage/sex/smoking categories, overlap evidence and data terms. Keep outcomes
   withheld. Resolve failed gates before freezing protocol version 1.
3. Implement the deterministic loader/statistics and new report contract, validate
   with synthetic controls, and inspect the metadata-only eligibility receipt.
4. Run TCGA, freeze the reviewed implementation, release MSK once, and then run
   the bounded report/query batch. Save all outcomes, exclusions and failures.

No clinically actionable or causal conclusion follows from this pilot alone.
