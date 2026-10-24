# Verified FRCE shell-enabled smoke

This synthetic run completed on 2026-10-24 using runtime commit
`07a6bfcbbb29009a9db13c72474be51bdc4270f7`, Codex 0.160.0, and `gpt-5.6-sol`.
Both the framework enclosure and native `workspace-write` sandbox remained
enabled. Each model read the supplied Parquet through its shell; inline mode
was disabled.

- [ALPHA report](SYNTH_ALPHA/report.md): control 10, perturbed 14, difference +4.
- [BETA report](SYNTH_BETA/report.md): control 10, perturbed 10, difference 0.
- [Query answer](query.md): retrieves both reports and resolves target-scoped evidence.
- [Receipt](receipt.json): versions, source revision, hashes, usage, checks and limitations.
- [Native tool calls](native_tool_calls.json): nine completed evidence calls.
- [Live release doctor](doctor-live.json): 33 checks, zero errors or warnings.

Each target directory also includes its structured appendix, validation result,
and completed shell events. Both models recovered from an initial optional
pandas import failure using pyarrow and the standard library. The query retains
a nonfatal unknown enterprise-feature warning. Three valid dictionary searches
returned no matches; the numeric results came from ledger and evidence retrieval.

Reports, appendices and the query are exact generated outputs. In event snapshots,
absolute project/run paths are replaced with `<PROJECT_ROOT>` and `<RUN_DIR>`;
the receipt retains hashes of the original local files. Full raw logs and exact
launch scripts remain in ignored run storage. No credentials are included.

The three model runs used 193,531 total tokens, including 125,184 cached input
tokens. These measurements are not a price estimate or a future budget guarantee.
This establishes two sequential synthetic builds and evidence retrieval, with
no biological result, independent replication, or parallel-scale validation.
Follow [the runbook](../../../FRCE_HANDOFF.md) to reproduce the workflow.
