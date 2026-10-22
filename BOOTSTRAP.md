# Bootstrap milestone

This research fork starts from upstream commit
`c20445d929f5aedce1d539ef6fbd8843b8c06e25`. Its first milestone is a working
source-report → validated evidence corpus → native evidence query path on new
inputs. The fixture is entirely synthetic: SYNTH_ALPHA has a mean difference
of +4 and SYNTH_BETA has 0. Neither is a biological gene or a discovery.

The public upstream tree omitted the `distributed_agents.build` package, so
its CLI could not import. This fork reconstructs a minimal builder using the
released findings prompt, a new schema/validator and the existing Codex runtime.
It is not a recovery of the authors' implementation or a reproduction of their
experiments. The root ignore pattern is anchored so it no longer hides source
packages named `build`.

## What is implemented

- Fixed, hashed report contracts; six ordered ledgers; grounded cross-reference
  validation; provenance, usage and failure records; refusal to overwrite runs.
- Deterministic report import and bounded live Codex generation.
- A small standalone release packager with hash checks, explicit provenance,
  calibration, exact ledger retrieval and target-scoped evidence resolution.
- Release-specific dataset descriptions, optional graphs and the active Python
  interpreter for MCP. Synthetic inputs do not inherit the original mouse-brain
  experiment's description.
- An opt-in complete tiny-input snapshot for live tests without shell access.

## Reproduce the deterministic path

Use Python 3.11 or newer. On Biowulf, load the appropriate Python module first.
No manuscript files or Git LFS data are needed for this fixture.

```bash
python -m venv .venv
.venv/bin/python -m pip install -e '.[analysis]' pytest build wheel setuptools
```

Follow [examples/bootstrap/README.md](examples/bootstrap/README.md), using the
virtual environment's Python. It shows report generation, import, release
packaging, corpus doctor and native MCP queries. Use a fresh output directory
for each run. Tests need `pytest`; the `analysis` extra provides `pyarrow` for
the optional live input.

## Reproduce a bounded live build

Authenticate your normal Codex CLI, then create the tiny Parquet:

```bash
.venv/bin/python examples/bootstrap/make_parquet.py \
  --output runs/live/input/synthetic_observations.parquet
.venv/bin/python -m distributed_agents build SYNTH_ALPHA \
  --parquet-path runs/live/input/synthetic_observations.parquet \
  --out-dir runs/live/builds --inline-small-input \
  --model YOUR_AVAILABLE_MODEL --reasoning-effort low --timeout-seconds 240
```

If a host wrapper does extra synchronization, `--codex-executable` can point
to the installed native executable. The optional `--no-codex-bwrap` disables
only the framework's additional enclosure; the native workspace-write sandbox
remains configured. Use it only where the execution environment supplies the
required isolation. No sandbox-bypass flag is used by these examples.

`--inline-small-input` is intentionally bounded: at most 100 rows, a 1 MiB
Parquet file and 64 KiB of JSON-compatible finite data. It includes every row,
records the input hash, and disables model shell and web tools. It rejects
larger inputs instead of sampling them. This tests live authoring; it is not a
large-dataset execution strategy.

Package the successful build with `corpus.bootstrap` as in the deterministic
example. Supply CSV or JSON source companions; the current packager does not
support binary source attachments such as Parquet. Its manifest retains the
builder's original input hash. Select the resulting release via
`DISTRIBUTED_AGENTS_CORPUS_RELEASE_ROOTS` and `--corpus-release`.

For a minimal live retrieval check:

```bash
.venv/bin/python -m distributed_agents query \
  'Use describe and calibrate, retrieve SYNTH_ALPHA findings, and resolve their evidence. State the constructed mean difference and why it is not biological evidence.' \
  --mode direct --corpus-release YOUR_RELEASE_ID --out-dir runs/live/query \
  --model YOUR_AVAILABLE_MODEL --codex-reasoning-effort low \
  --codex-timeout-seconds 240 \
  --codex-config-override features.shell_tool=false \
  --codex-config-override 'web_search="disabled"'
```

## Verified result

The live smoke test completed on 2026-10-22 with Codex 0.160.0 and
`gpt-5.6-sol`: one generated report, two grounded findings, and seven successful
native MCP calls in the subsequent direct query. Both constructed differences
were recovered correctly. See the [generated report](examples/bootstrap/verified_run/report.md),
[query answer](examples/bootstrap/verified_run/query.md), and
[hashed receipt](examples/bootstrap/verified_run/receipt.json).

All 39 regression tests passed, the live release passed 37 integrity checks,
and the wheel imported and launched successfully from a clean virtual
environment. The query completed with a nonfatal warning about an unknown
enterprise CLI feature requirement; evidence calls and the answer succeeded.

## Verification and next scope

Run the focused regression suite and wheel check:

```bash
.venv/bin/python -m pytest -q tests
.venv/bin/python -m build --wheel --no-isolation --outdir dist
.venv/bin/python scripts/smoke_wheel.py
```

[status.md](status.md) records the actual run results, paths, host limitations
and next action. Model narratives are checked for schema and internal grounding;
that does not prove scientific accuracy or novelty. The source-report prompt
still reflects the original Perturb-seq use case. Before applying this to
cancer, aging or mutations, select a public pilot dataset and implement its
assay-specific analysis contract, independent replication and null checks.

No thousand-agent execution, biological validation, graph construction, full
upstream normalization or manuscript reproduction is claimed by this milestone.
