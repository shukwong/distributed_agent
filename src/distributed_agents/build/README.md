# Reconstructed authoring path

This package is a minimal reconstruction added by the research fork. The
upstream public source omitted its build package. This is not recovered
upstream code and does not reproduce the paper's generation experiment.

The fixed findings task is copied from the released Shi generation prompt.
The base scientific contract, six-ledger schema, parser, cross-reference
validation, provenance recorder, and Codex integration are new. Their exact
resource hashes are checked at runtime and recorded with every report.

`distributed_agents build TARGET --report-path REPORT.md --out-dir RESULTS`
imports a caller-owned report without running a model. The report must include
`Key Biological Findings`, `Missed-Finding Audit`, and `Structured Appendix`
Markdown headings and the six ordered JSONL blocks specified by the task.

Omit `--report-path` and supply `--parquet-path` for live Codex generation.
Use `--timeout-seconds` for the enforced wall-clock limit. `--max-turns` and
custom skill staging were part of the old interface but have no reconstructed
implementation; setting them fails explicitly. The default model is the
account's configured Codex model. Authentication is staged in a temporary
isolated directory outside persistent research artifacts.

For a small smoke test, `--inline-small-input` reads the complete Parquet on the
host and includes a hashed snapshot in the task. It accepts at most 100 rows,
a 1 MiB source file and 64 KiB of finite JSON-compatible data; larger inputs
fail without sampling. Shell and web tools are disabled in this mode, while
the native sandbox remains configured. Install the `analysis` extra for this
optional mode. This is a bounded input mode, not a large-dataset analysis path.

Each successful output contains `report.md`, `structured_appendix.json`, six
normalized JSONL files, `validation.json`, and `run.json`. Live execution also
records Codex events, its last message, and usage. A failed validation retains
the raw report and diagnostics. Existing nonempty output folders are refused.

Validation checks schema, unique IDs, internal references, and derived-view
membership. It does not establish scientific truth, literature accuracy,
statistical validity, or novelty. Synthetic inputs must remain explicitly
labeled as software tests with no biological conclusions.

The upstream `normalization` and `reference_normalization` modules remain
unavailable and are outside this first milestone.
