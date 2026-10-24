# FRCE continuation handoff

Prepared 2026-10-24. This document is the starting point for a new Codex task on
FRCE (called FRC in the conversation). Read `status.md` next, then `BOOTSTRAP.md`.
The FRCE shell-enabled milestone is complete. The native sandbox probe, two
sequential live Parquet-reading builds, validation, release packaging and direct
native MCP query all passed. See
[the live receipt](examples/bootstrap/frce_verified_run/receipt.json) for exact
versions, commands, usage, hashes and diagnostics. The runbook below supports
reproduction; resuming work does not require rerunning the completed smoke test.

## Objective and current position

Adapt DistributedAgents for systematic investigations of public data relevant
to cancer, aging, or mutations. The intended pattern is many bounded analyses,
validated source reports, a searchable evidence corpus, and evidence-grounded
synthesis. No biological pilot or final research question has been selected.

**Completed first milestone:** repaired the public checkout, generated a tiny
synthetic report with Codex, packaged its evidence, and queried it through the
native MCP interface. Biowulf prohibited user namespaces, so successful live
generation supplied the complete tiny input inline and disabled model shell
and web tools. This established live report authoring and retrieval, but not
shell-based data analysis or parallel scale.

**Completed FRCE milestone:** normal model shell commands read the supplied
Parquet in two sequential live builds, followed by validation, packaging and
one direct native-evidence query. Both framework and native sandboxes remained
enabled; inline input was not used.

**Next milestone:** the user selected cancer and mutations. Review the concrete
[LUAD mutation-pair pilot proposal](pilots/luad_mutation_pairs/README.md), then
agree its specific scope, complete the metadata audit and implement its assay
contract before launch. No biological pilot or parallel scaling experiment has
started; no mutation outcomes were inspected during scoping.

## Repository and materials

- Working fork: https://github.com/shukwong/distributed_agent
- Required branch: **`research/bootstrap-corpus`**. The default `main` still
  follows upstream and does not contain the milestone implementation.
- Existing draft PR: https://github.com/shukwong/distributed_agent/pull/1
- Implementation commit: `8ed5d0364088fb326b0078d371ad6b9b7bc92586`.
- Verified FRCE source: `07a6bfcbbb29009a9db13c72474be51bdc4270f7`.
  Later commits preserve receipts and documentation. For a fresh reproduction,
  use the latest branch tip and record its exact SHA in the run receipt.
- Upstream: https://github.com/jinlabneurogenomics/distributed_agent
  at baseline `c20445d929f5aedce1d539ef6fbd8843b8c06e25`.
- User-supplied motivating preprint:
  https://www.biorxiv.org/content/10.64898/2026.10.15.759436v1
  (background reading, not an input needed for the smoke test).

| Material in this branch | Purpose |
| --- | --- |
| `status.md` | Current state, verification, host diagnosis and next actions |
| `BOOTSTRAP.md` | Implementation overview and earlier Biowulf reproduction |
| `examples/bootstrap/README.md` | Deterministic report/import/MCP example |
| `examples/bootstrap/synthetic_observations.csv` | All 12 invented observations |
| `examples/bootstrap/generate_fixture.py` | Deterministic reference reports |
| `examples/bootstrap/make_parquet.py` | Converts the fixture to live-builder input |
| `examples/bootstrap/probe_outer_python.py` | Checks the actual outer enclosure without a model call |
| `examples/bootstrap/frce_verified_run/` | Shell-enabled FRCE reports, ledgers, query and hashed receipt |
| `examples/bootstrap/frce_preflight/receipt.json` | Earlier FRCE no-model verification |
| `examples/bootstrap/verified_run/report.md` | Previously successful live report |
| `examples/bootstrap/verified_run/query.md` | Previously successful live answer |
| `examples/bootstrap/verified_run/receipt.json` | Versions, usage, hashes and checks |
| `examples/bootstrap/verified_run/structured_appendix.json` | Validated evidence ledgers |
| `examples/bootstrap/verified_run/input_snapshot.json` | Complete previous live input |
| `src/distributed_agents/build/README.md` | Reconstructed builder contract and limits |
| `tests/` and `scripts/smoke_wheel.py` | Regression and packaging checks |

All smoke-test data and reference outputs are committed. No controlled-access
data, large upstream corpus, Git LFS download, or transfer of Biowulf `runs/`
is needed. Recreate the environment; do not copy the Biowulf virtualenv.
Credentials are not repository material: authenticate normally on FRCE and
never copy authentication files into the repository, logs, or handoff.

The fork reconstructs a missing upstream `distributed_agents.build` package;
it is not the authors' recovered implementation. The bootstrap corpus supports
calibration, ledger lookup and evidence resolution, with no graph or BM25 index.
Full upstream normalization and manuscript reproduction are outside this work.

## What has actually passed

- FRCE source: 50 regression tests and `pip check`; outer Python/Parquet probe
  and deterministic two-target reference path passed.
- Native Codex sandbox probe exited 0. Both live builds used normal shell access
  and successfully read all 12 Parquet rows in completed command event `item_5`.
- Live generation with Codex 0.160.0 and `gpt-5.6-sol`: ALPHA produced two evidence
  rows and two findings; BETA produced three evidence rows and one finding.
  Their group means and differences match the table below.
- Packaged live release: 33 doctor checks, zero errors and zero warnings.
- Direct query: nine successful native MCP calls (`describe`: 3, `calibrate`: 2,
  `query_ledger`: 1, `resolve_evidence`: 3), correct scoped citations and arithmetic.
  It exited 0 with `completed_with_warnings` for the known unknown enterprise
  feature requirement. Both builds recovered from an optional pandas display
  failure using Arrow directly; the native probe's stale `arg0` cleanup warning
  was also nonfatal. The live receipt preserves diagnostics and measured usage.
- Historical Biowulf inline run: 39 tests, wheel build and isolated install/CLI
  smoke passed; its report, query and receipt remain in `examples/bootstrap/verified_run/`.
  Wheel smoke was not repeated for the FRCE runtime-only changes.
- These are synthetic software results, not evidence about real genes or disease.
  Usage is a historical measurement, not a cost or token bound for the next run.

Expected fixture arithmetic:

| Target | Control mean | Perturbed mean | Difference |
| --- | ---: | ---: | ---: |
| SYNTH_ALPHA | 10 | 14 | +4 |
| SYNTH_BETA | 10 | 10 | 0 |

## FRCE host findings and launch context

The user reported successful user-namespace and bubblewrap checks inside
compute allocations on two FRCE nodes. Specific node names and allocation
identifiers are intentionally kept out of this public handoff.

An initial Codex probe, run **through another Codex agent's shell tool**, failed
with `app-server socket directory must be a user-owned directory with mode 0700`
and timeout 124. Codex 0.160.0 masks its reserved daemon socket directory within
its own shell sandbox, so a nested Codex can see a mode-000 directory even if the
host directory is correct. The command also used an obsolete extra `linux`
token. The user subsequently confirmed the corrected direct-terminal probe
worked. Those initial results were user-reported; the original task remained on
Biowulf. The 2026-10-24 FRCE continuation then independently ran the corrected
native probe and complete live workflow through explicitly authorized host
execution, preserving both child isolation layers. All completed successfully.

For Codex 0.160.0, the correct probe is:

```bash
timeout -k 2s 30s env -u CODEX_REMOTE_PAYLOAD \
  "$FRCE_CODEX_BIN" sandbox -- /usr/bin/true
```

Run it and the live workflow from a **regular terminal inside a compute
allocation, outside another Codex shell sandbox**, or an explicitly authorized
host execution facility that preserves the child sandbox. A new Codex task can
prepare the launch script and inspect outputs. Running it from that task's
already-sandboxed shell can reproduce the misleading nested failure.

The reserved directory is `realpath(/tmp)/codex-daemon-<effective UID>`;
changing `TMPDIR` or `CODEX_HOME` does not relocate it. Do not chmod a masked
directory, delete Codex state, disable isolation, or change host sysctls to
work around the nested probe. Inspect actual host metadata only if a probe
from the ordinary allocation terminal still fails.

Source for this exact-version diagnosis:
[daemon directory](https://github.com/openai/codex/blob/rust-v0.160.0/codex-rs/uds/src/daemon_directory.rs),
[sandbox masking](https://github.com/openai/codex/blob/rust-v0.160.0/codex-rs/linux-sandbox/src/bwrap.rs#L855).
For another installed Codex version, inspect its help/source before assuming
these internals or command syntax are identical.

## Requirements and fresh checkout

Use persistent project storage, an active FRCE compute allocation, Git,
bubblewrap, Python >=3.11 (previous run used 3.12.8), and an authenticated native
Codex executable. Use a small CPU allocation for the fixture and respect the
actual FRCE allocation and local scheduling policy. Package install
and model calls need their respective network endpoints. No GPU is needed for
this fixture. No API key is required when using the normal Codex ChatGPT login.

The sparse checkout avoids downloading the original large data and corpus:

```bash
GIT_LFS_SKIP_SMUDGE=1 git clone --filter=blob:none --no-checkout \
  --single-branch --branch research/bootstrap-corpus \
  https://github.com/shukwong/distributed_agent.git
cd distributed_agent
git sparse-checkout set --no-cone \
  '/*' '!/data/' '!/notebook/' \
  '!/src/distributed_agents/corpus/releases/' \
  '/src/distributed_agents/corpus/releases/*/release.json' \
  '/src/distributed_agents/corpus/releases/*/provenance/'
GIT_LFS_SKIP_SMUDGE=1 git checkout research/bootstrap-corpus
git rev-parse HEAD
```

For an existing checkout, inspect its branch, changes and outputs first; do not
replace local work. Do not use `git ls-tree -l` merely to list a partial clone:
it can fetch large missing blobs. Use `--name-only` instead.

Load a suitable Python using FRCE's available tools, then from the repo root:

```bash
python3 --version
python3 -m venv .venv
# FRCE's Python module injects shared packages; keep the venv self-contained.
unset PYTHONHOME PYTHONPATH
.venv/bin/python -m pip install -e '.[analysis]' pytest build wheel setuptools
.venv/bin/python -m pip check
.venv/bin/python -m pytest -q tests
```

Discover the **FRCE-local native Codex binary** and select a model available to
the authenticated account. Do not copy a Biowulf binary path. A host wrapper
that performs synchronization is not necessarily the native executable. Check
`type -a codex`, the installed launcher and `codex --version` as needed. Query
model defaults in upstream code may be unavailable account-specific names, so
always pass an explicit model.

Set these in the ordinary allocation terminal, replacing the two placeholders:

```bash
set -euo pipefail
unset PYTHONHOME PYTHONPATH
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
export FRCE_CODEX_BIN='/absolute/path/to/native/codex'
export FRCE_MODEL='YOUR_AVAILABLE_MODEL'
"$FRCE_CODEX_BIN" --version
mkdir -p runs
export FRCE_RUN_DIR="$(mktemp -d "$PWD/runs/frce-smoke.XXXXXX")"
.venv/bin/python -m pip freeze > "$FRCE_RUN_DIR/environment.txt"
git rev-parse HEAD > "$FRCE_RUN_DIR/commit.txt"
.venv/bin/python examples/bootstrap/make_parquet.py \
  --output "$FRCE_RUN_DIR/input/synthetic_observations.parquet"
```

Record hostname, allocation/job ID, cwd, launch command and native CLI version
alongside these receipts. Keep the same environment variables for subsequent
steps. Run the corrected sandbox probe above and inspect its exit status.

### Verified Python portability repair

Before spending model tokens, verify the exact outer enclosure can run its
selected Python, import `pyarrow.parquet`, and read the declared input:

```bash
.venv/bin/python examples/bootstrap/probe_outer_python.py \
  --parquet-path "$FRCE_RUN_DIR/input/synthetic_observations.parquet" \
  --codex-executable "$FRCE_CODEX_BIN" \
  --out-dir "$FRCE_RUN_DIR/shell_probe" \
  2>&1 | tee "$FRCE_RUN_DIR/shell-probe.log"
```

This helper constructs the real builder enclosure, replaces the Codex command
with a Python read probe, and checks the selected environment and 12-row input.
It stages no credentials and makes no model call. It tests only the outer
layer; the native sandbox and live model shell still need their own checks.
The helper now passes on FRCE with Python 3.12.0 and pyarrow 26.0.0: it selects
the project venv, imports pyarrow, and reads all 12 declared rows.

A host venv import alone is insufficient. The runtime now retains the venv bin
directory with `.absolute().parent` and mounts the Python prefix, base prefixes,
and interpreter directory read-only. Non-inline live tasks name the selected
interpreter explicitly. Focused regressions cover external module installations
and shell quoting. Explicit positive numerical thread caps also survive the
framework and query-shell environment filters.

On a fresh host, still run this probe before model calls. Unset `PYTHONHOME` and
`PYTHONPATH` during both installation and execution: the FRCE module can otherwise
make pip accept shared packages that disappear inside the enclosure. Passing
this outer probe does not prove native model-shell execution works.

Keep both the framework enclosure and native `workspace-write` sandbox enabled,
as in the successful FRCE run. Their combined execution path is now verified for
this tiny fixture in the recorded environment.
Do not substitute `--inline-small-input` or disable shell tools to make this
particular acceptance test pass.

## Runbook after the host and Python probes pass

The following commands use fresh subdirectories under `$FRCE_RUN_DIR`. Run
sequentially and stop to inspect any failure before continuing. The 240-second
options bound each model invocation's wall time; they are not spending caps.

First verify the deterministic path without a model:

```bash
.venv/bin/python examples/bootstrap/generate_fixture.py \
  --output-dir "$FRCE_RUN_DIR/reference_inputs"
for FRCE_TARGET in SYNTH_ALPHA SYNTH_BETA; do
  .venv/bin/python -m distributed_agents build "$FRCE_TARGET" \
    --report-path "$FRCE_RUN_DIR/reference_inputs/$FRCE_TARGET.md" \
    --out-dir "$FRCE_RUN_DIR/reference_builds"
done
.venv/bin/python -m distributed_agents.corpus.bootstrap \
  --build-dir "$FRCE_RUN_DIR/reference_builds/SYNTH_ALPHA" \
  --build-dir "$FRCE_RUN_DIR/reference_builds/SYNTH_BETA" \
  --output-root "$FRCE_RUN_DIR/releases" \
  --release-id frce_reference_v1 --synthetic \
  --source-file examples/bootstrap/synthetic_observations.csv
export DISTRIBUTED_AGENTS_CORPUS_RELEASE_ROOTS="$FRCE_RUN_DIR/releases"
export DISTRIBUTED_AGENTS_CORPUS_RELEASE=frce_reference_v1
.venv/bin/python -m distributed_agents.corpus doctor --json \
  > "$FRCE_RUN_DIR/doctor-reference.json"
```

Generate two real model-authored reports with normal shell access:

```bash
for FRCE_TARGET in SYNTH_ALPHA SYNTH_BETA; do
  .venv/bin/python -m distributed_agents build "$FRCE_TARGET" \
    --parquet-path "$FRCE_RUN_DIR/input/synthetic_observations.parquet" \
    --out-dir "$FRCE_RUN_DIR/live_builds" \
    --codex-executable "$FRCE_CODEX_BIN" --codex-auth chatgpt \
    --model "$FRCE_MODEL" --reasoning-effort low --timeout-seconds 240
done
```

Inspect each `run.json`, `validation.json`, `report.md`, `events.jsonl` and
`runner.log`. Require evidence of successful shell input reads and nonempty,
correct synthetic findings. Schema validation alone can accept an honest empty
report after an input-read failure; that does not satisfy this milestone.

Only package reports after that inspection succeeds:

```bash
.venv/bin/python -m distributed_agents.corpus.bootstrap \
  --build-dir "$FRCE_RUN_DIR/live_builds/SYNTH_ALPHA" \
  --build-dir "$FRCE_RUN_DIR/live_builds/SYNTH_BETA" \
  --output-root "$FRCE_RUN_DIR/releases" \
  --release-id frce_live_v1 --synthetic \
  --source-file examples/bootstrap/synthetic_observations.csv
export DISTRIBUTED_AGENTS_CORPUS_RELEASE=frce_live_v1
.venv/bin/python -m distributed_agents.corpus doctor --json \
  > "$FRCE_RUN_DIR/doctor-live.json"
.venv/bin/python -m distributed_agents query \
  'Use describe and calibrate, retrieve SYNTH_ALPHA and SYNTH_BETA findings with query_ledger, and resolve their evidence. Report control and perturbed means and differences with target-scoped evidence citations. Explain the limits of these synthetic observations.' \
  --mode direct --backend codex --corpus-release frce_live_v1 \
  --out-dir "$FRCE_RUN_DIR/live_query" \
  --codex-executable "$FRCE_CODEX_BIN" --codex-auth chatgpt \
  --codex-sandbox workspace-write --model "$FRCE_MODEL" \
  --codex-reasoning-effort low --codex-timeout-seconds 240 \
  --codex-config-override 'web_search="disabled"'
```

The source companion is CSV, not binary Parquet: the current packager only
accepts textual companions. Builder provenance records the original input hash.

## Acceptance, outputs and continuation

The recorded FRCE run satisfies these acceptance criteria. Apply them again
when reproducing on another environment:

1. Normal model shell commands actually read the declared input; no inline mode.
2. Live reports validate, contain supported findings and reproduce the +4 and 0
   differences with the correct group means. Both invented labels remain explicit.
3. The packaged live release passes the corpus doctor with zero errors.
4. The query log records successful native evidence-tool calls and the answer
   has correct target-scoped citations and numbers, with no biological inference.
5. Save exact commands, version/environment receipt, usage, failures/warnings,
   input/output hashes, and a small representative report/query in the branch.
   Keep bulk raw outputs in persistent `runs/` storage. Never commit credentials.
6. Record host, cwd, allocation/job ID, logs, outputs and next
   check in a local, ignored run receipt. Keep public `status.md` focused on
   reproducible commands, results and remaining work; omit internal node names,
   allocation identifiers and machine-specific paths from GitHub commits.
   If a job must outlive the active allocation, use the site's scheduler.
   On resume, check job state and existing outputs before creating a fresh run.

Run the focused tests after any runtime fix. Repeat wheel smoke only if packaging
or dependency behavior changes. Preserve failed-run diagnostics and use fresh
output directories; the builder/packager refuse to overwrite completed results.

Next, complete the proposed **cancer/mutation** pilot scope in
`pilots/luad_mutation_pairs/`; the specific LUAD protocol remains proposed and
no pilot has launched. Agree on the independent unit of analysis,
covariates, null controls, multiple-testing
procedure and independent replication/holdout before launching a screen. The
current source-report prompt is Perturb-seq-specific and needs an assay-specific
contract; arbitrary transcriptomics or microbiome data are not drop-in inputs.
Processed public data may suffice, but access requirements depend on the chosen
files. Controlled-access individual-level data are not needed for this smoke test
and no such access has been arranged for a later pilot.

Then run a small bounded parallel pilot to measure correctness, failure/retry
behavior, evidence quality, scheduler fit, model rate limits and per-task cost.
Define a total budget and restart strategy before larger deployment. A scheduler
for thousands of independent builds is not implemented or validated by this
milestone. Use this fork's `distributed_agents build`/`query` commands as the
research runtime; Codex is the execution backend and development assistant, not
proof that a thousand-task research sweep is already configured.
