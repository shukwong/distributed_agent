# Tiny new evidence corpus

This is a deterministic **synthetic software validation fixture**. The two
identifiers are not real genes. The invented measurements show a mean difference
of +4 for SYNTH_ALPHA and 0 for SYNTH_BETA. They support no biological claims,
statistical significance, or discoveries about cancer, aging, or mutations.

The fixture exercises the repaired source-report builder, release packaging,
corpus integrity checks, and the repository's existing MCP query service. Its
reports are computed by a script; running this example does **not** demonstrate
LLM-generated scientific discovery or thousands of concurrent agents.

From an installed checkout, use a fresh run directory (the builder and packager
refuse to replace existing results):

```bash
python examples/bootstrap/generate_fixture.py --output-dir runs/bootstrap/inputs
python -m distributed_agents build SYNTH_ALPHA --report-path runs/bootstrap/inputs/SYNTH_ALPHA.md --out-dir runs/bootstrap/builds
python -m distributed_agents build SYNTH_BETA --report-path runs/bootstrap/inputs/SYNTH_BETA.md --out-dir runs/bootstrap/builds
python -m distributed_agents.corpus.bootstrap \
  --build-dir runs/bootstrap/builds/SYNTH_ALPHA \
  --build-dir runs/bootstrap/builds/SYNTH_BETA \
  --output-root runs/bootstrap/releases \
  --release-id bootstrap_synthetic \
  --synthetic \
  --source-file examples/bootstrap/synthetic_observations.csv
```

Select the new release through the existing registry:

```bash
export DISTRIBUTED_AGENTS_CORPUS_RELEASE_ROOTS="$PWD/runs/bootstrap/releases"
export DISTRIBUTED_AGENTS_CORPUS_RELEASE=bootstrap_synthetic
python -m distributed_agents.corpus doctor
```

Query through the native MCP server. Supply one JSON object per stdin line:

```bash
python -m distributed_agents.corpus.mcp.application \
  --release-manifest runs/bootstrap/releases/bootstrap_synthetic/release.json \
  --capabilities runs/bootstrap/releases/bootstrap_synthetic/capabilities.json <<'JSONL'
{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"calibrate","arguments":{"topic":"summary"}}}
{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"query_ledger","arguments":{"ledger":"findings"}}}
{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"resolve_evidence","arguments":{"gene":"SYNTH_ALPHA","finding":"F001"}}}
JSONL
```

Available capabilities are calibration, exact ledger lookup and evidence
resolution. The capsule has no graph or BM25 index. Its release-local adapters
are standard-library scripts copied into the capsule. Their code and data can be
inspected independently of an LLM. Source CSV bytes are copied into the capsule;
recorded evidence and reference descriptions carry their SHA-256 hash.

Tests (`python -m pytest -q tests/test_bootstrap_corpus.py`) verify exact numeric
results, target-local IDs, native MCP transport, truncation, rejected stale or
duplicate inputs, immutable releases and detection of artifact tampering.
