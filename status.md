# Status

Last updated: 2026-10-24 EDT

## Goal

The FRCE shell-enabled synthetic milestone is complete: generate two reports
from Parquet through normal model shells, validate and package their evidence,
and query it through native MCP tools. Next: select one public cancer/mutation
or aging pilot and define its protocol before launch. A biological pilot and
parallel scaling have not started.

## Current State

- Fork: https://github.com/shukwong/distributed_agent
- Branch: `research/bootstrap-corpus`; the default `main` still follows upstream.
- Draft PR: https://github.com/shukwong/distributed_agent/pull/1
- Upstream baseline: `c20445d929f5aedce1d539ef6fbd8843b8c06e25`.
- Original implementation: `8ed5d03`. Verified FRCE source:
  `07a6bfcbbb29009a9db13c72474be51bdc4270f7`; later commits preserve receipts and
  documentation. Record the exact source SHA for any fresh reproduction.
- Reconstructed the missing report builder, added validated ledger packaging,
  release-owned dataset context, optional graph handling and interpreter fixes.
- FRCE live synthetic generation, release doctor and direct native MCP query
  succeeded. Public evidence: `examples/bootstrap/frce_verified_run/`.
  The earlier Biowulf inline example remains in `examples/bootstrap/verified_run/`.
- `FRCE_HANDOFF.md` contains the verified reproduction runbook and acceptance
  criteria. The smoke test is complete; do not repeat it merely to resume.
- `examples/bootstrap/probe_outer_python.py` checks the actual outer enclosure's
  Python and Parquet access without launching a model or staging credentials.
- FRCE continuation repaired venv selection, external Python mounts, explicit
  task interpreter context, and propagation of positive thread caps. The actual
  outer enclosure reads the 12-row fixture successfully. Two deterministic
  reference builds package and pass the corpus doctor. Receipt:
  `examples/bootstrap/frce_preflight/receipt.json`.
- The native sandbox probe and both live builds ran through authorized host
  execution with framework and native sandboxes enabled. Each build successfully
  read the declared Parquet in shell event `item_5`; neither used inline input.
- Live reports contain three supported findings and five evidence rows in total.
  The direct query retrieved both targets and resolved correctly scoped evidence.
  All results are synthetic software checks, with no biological conclusion.

## Host Diagnosis and FRCE Follow-up

- The original Biowulf execution environment disables new user namespaces.
  Namespace creation failures were not a disk-space shortage or a demonstrated
  leak. No host settings were changed and no support message was sent.
- Historical Biowulf live generation used `--inline-small-input`, supplying the
  complete bounded input and disabling model shell/web tools. Native sandboxing
  remained configured. This does not prove ordinary shell execution works.
- The user reported namespace and bubblewrap checks passing on two FRCE compute
  nodes. An initial Codex test ran through another Codex agent's shell tool and
  failed with `app-server socket directory must be a user-owned directory with
  mode 0700` plus a timeout.
- Exact-version source for Codex 0.160.0 shows its reserved daemon directory is
  masked within its shell sandbox. Nested execution is the likely explanation;
  no host permission repair was established as necessary. `FRCE_HANDOFF.md`
  links the source and gives the corrected `codex sandbox -- COMMAND` syntax.
- The corrected native probe was independently rerun on FRCE and exited 0;
  shell-enabled builds and query then completed. Future runs should use an
  ordinary allocation terminal or authorized host execution that preserves
  the child sandbox. No host permission or namespace-setting changes were needed.

## Durable Outputs

- All required test input, generators and representative successful outputs are
  committed under `examples/bootstrap/`; no external dataset transfer is needed.
- Original raw logs and environment receipts remain under ignored `runs/bootstrap/`
  in the original checkout. They are not required to resume on FRCE.
- Historical outputs include `live_build_inline/SYNTH_ALPHA/`,
  `releases/bootstrap_live_v1/`, `live_query/`, and the deterministic
  `releases/bootstrap_synthetic_v1/` beneath that run root.
- Full host-specific handoff details remain in ignored `runs/frce_handoff_private/`
  locally. Keep hostnames, allocation IDs and absolute machine-specific paths in
  local run receipts, not public GitHub commits. Recreate the environment on FRCE.
- FRCE raw diagnostics, exact launch scripts and environment receipt are under
  ignored `runs/frce-smoke.*/`; the local workspace `status.md` identifies the
  completed run, allocation and next action. Inspect it before creating a new run.
- Public commands, versions, usage, input/output hashes, diagnostics and compact
  report/query artifacts are recorded in `examples/bootstrap/frce_verified_run/`.
  Keep full raw logs and machine-specific execution details in local receipts.

## Verification

- FRCE: 50 regression tests passed, `pip check` passed, outer Python/Parquet probe
  passed, and the deterministic two-target release doctor passed with zero errors.
- Native sandbox probe exited 0. Two sequential shell-enabled builds validated:
  ALPHA has control/perturbed means 10/14 and difference +4; BETA has means 10/10
  and difference 0. Their successful shell reads were independently inspected.
- Live release doctor: 33 checks, zero errors or warnings. Direct query: exit 0,
  nine successful native MCP calls, correct target-scoped citations and arithmetic.
  The query completed with the known nonfatal unknown-enterprise-feature warning.
- Both builds recovered from missing optional pandas during display by reading
  Arrow records directly. The native probe's stale `arg0` cleanup warning was
  nonfatal. See the live receipt for exact diagnostics and per-run token usage.
- Historical Biowulf wheel build and isolated install/CLI smoke passed. They
  were not repeated for these runtime-only changes.
- An earlier shell-based generation failed to read input and returned an honest
  empty report; it was excluded from successful releases. Historical inline
  verification remains documented in `examples/bootstrap/verified_run/receipt.json`.

## Next Actions

1. Read `FRCE_HANDOFF.md`, the local workspace handoff, and the existing run
   outputs; verify the current allocation before resuming.
2. Resolve the pending pilot choice: public cancer/mutation data or aging data.
   No dataset, biological research question or pilot launch has been selected.
3. Before launch, define the independent analysis unit, covariates, null controls,
   multiple-testing procedure, replication/holdout and assay-specific report
   contract. The current prompt assumes Perturb-seq and is not a general assay contract.
4. Set a bounded compute/model budget and restart strategy for the selected pilot.
   Only then evaluate small-scale parallel execution, failure handling and cost;
   the synthetic workflow does not establish parallel-scale readiness.

## Lessons Learned

- Anchor `/build/` in `.gitignore`; an unanchored rule hid the upstream source
  package. This fork's builder is a reconstruction, not recovered author code.
- Use the active Python for MCP; an isolated wheel-test venv must install declared
  dependencies. A resolved venv symlink in shell PATH can select the wrong Python.
- A configured zero namespace limit cannot be repaired by restarting agents or
  freeing disk. Test nested and ordinary-terminal contexts separately.
- Avoid `git ls-tree -l` on a partial clone just to list paths; it fetches blobs.
  Use `--name-only`. The fixture needs no upstream LFS corpus.
- The bootstrap packager accepts textual companions, not binary Parquet. Preserve
  original input hashes in builder provenance.
- FRCE `python/3.12` injects `PYTHONHOME` and shared-package `PYTHONPATH`. Unset
  both for venv installs and launches; confirm dependencies inside the actual
  outer enclosure, not only in the module-loaded host shell.
- Environment scrubbing must retain explicitly chosen numerical thread caps;
  parent exports alone do not bound the model shell if filters drop them.
- The `analysis` extra supplies Arrow, not pandas. For small Parquet inspections,
  `read_table(...).to_pylist()` avoids an unnecessary optional display dependency.
- Validate actual successful input-read and MCP events, numeric evidence and
  target-scoped citations; schema or completed-turn status alone is insufficient.
