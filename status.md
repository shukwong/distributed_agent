# Status

Last updated: 2026-10-22 19:31 EDT

## Goal

First milestone: fork DistributedAgents, obtain a working baseline, generate
and query a tiny new corpus before choosing a biological pilot or scaling.
That milestone is complete. Current follow-up: diagnose and repair the model
shell namespace failure without weakening isolation.

## Current State

- Milestone implementation and verification complete locally. Fork:
  https://github.com/shukwong/distributed_agent. Branch: `research/bootstrap-corpus`.
  Upstream base: `c20445d929f5aedce1d539ef6fbd8843b8c06e25`.
- Reconstructed missing report builder, validated ledger packaging, release-owned
  dataset context, optional graph and interpreter portability implemented.
- Live synthetic report generation and native MCP query succeeded. See
  `examples/bootstrap/verified_run/` for the reviewable outputs and hashes.
- Published implementation commit: `8ed5d03`. Draft review PR:
  https://github.com/shukwong/distributed_agent/pull/1 (base is this fork, not upstream).
  First milestone complete; no research process remains running.
- No biological discovery, real-dataset pilot or thousand-agent scaling claimed.
- Namespace diagnosis complete: cn1073 has `user.max_user_namespaces=0`, also
  explicitly configured in root-owned `/etc/sysctl.conf:86`. This disables new
  user namespaces; it is not a demonstrated leak or disk-space shortage.
  Harmless `unshare` and `bwrap` probes both reproduce ENOSPC. Host repair needs
  an administrator-approved namespace-enabled environment; not resolved locally.
- Diagnostic receipt: `runs/namespace_diagnosis/receipt.json`. Ready-to-send
  support draft: `runs/namespace_diagnosis/hpc-support-request.md`. No message
  has been sent and no host settings have been changed.

## Runtime and Durable Outputs

- Host: `cn1073`; allocation `33084292`, 4 CPUs / 8 GiB, expires
  2026-10-22 21:32:46 EDT. Used active allocation; no new scheduler job submitted.
- Cwd: `/data/DCEG_REBC_CH/wendy/projects/distributed_agent`
  (physical alias `/vf/users/DCEG_REBC_CH/wendy/projects/distributed_agent`).
- Python: `.venv/bin/python` (3.12.8); dependency receipt:
  `runs/bootstrap/environment.txt`.
- Native CLI: `/spin1/home/linux/wongs6/.codex/packages/standalone/releases/0.160.0-x86_64-unknown-linux-musl/bin/codex`.
- All run outputs/logs: `runs/bootstrap/` (ignored by Git, persistent storage).
  Important outputs: `live_build_inline/SYNTH_ALPHA/`,
  `releases/bootstrap_live_v1/`, `live_query/query.md` and `live_query/run.json`.
- Deterministic two-report release: `releases/bootstrap_synthetic_v1/`.
  Earlier `bootstrap_synthetic` predates the release-specific portrait; use v1.

The successful build command was:

```bash
.venv/bin/python -m distributed_agents build SYNTH_ALPHA --parquet-path runs/bootstrap/live_input/synthetic_observations.parquet --out-dir runs/bootstrap/live_build_inline --inline-small-input --codex-executable /spin1/home/linux/wongs6/.codex/packages/standalone/releases/0.160.0-x86_64-unknown-linux-musl/bin/codex --no-codex-bwrap --model gpt-5.6-sol --reasoning-effort low --timeout-seconds 240
```

The live query task is preserved in `runs/bootstrap/live_query/task.md`; its
exact launch command/config is in `live_query/run.json` and `codex_runtime/`.
It selected `bootstrap_live_v1`, direct mode, low reasoning, 240-second timeout,
model shell disabled, web disabled, and native workspace-write sandbox retained.
Reproduction commands for fresh directories are in `BOOTSTRAP.md`.

## Verification

- `python -m pytest -q tests`: **39 passed** (`runs/bootstrap/tests.log`).
- Live release doctor: **37 checks**, zero errors (`doctor-live.json`).
- Wheel build and isolated install/import/CLI smoke: passed
  (`wheel-build.log`, `wheel-smoke.log`); `pip check`: passed.
- Live build: two evidence rows and two findings; constructed differences +4
  and 0 match input. Usage: 15,668 total tokens (including 13,615 input).
- Live query: seven successful native MCP calls; correct scoped citations and
  numeric values. Usage: 65,635 total tokens, including 48,640 cached input.
  Status `completed_with_warnings`: CLI ignored unknown enterprise feature
  requirement `ultrafast_mode`; no evidence-tool failure.
- Initial shell-based generation could not read input because namespace creation
  failed with ENOSPC. It returned an honest empty report, excluded from the
  successful release. Log: `live-build.log`. No sandbox bypass was used.

## Next Actions

1. For shell execution, ask NIH HPC whether it offers an approved namespace-enabled
   environment or can support the required setting for an isolated allocation.
   Use the saved support draft. Restarting agents or freeing disk cannot change
   a configured zero limit. Once provided, rerun the harmless namespace probes
   and native sandbox smoke before another model call.
2. Review draft PR #1; the implementation is on `research/bootstrap-corpus`.
   The fork's default `main` still follows upstream until the PR is merged.
3. Before resuming runs, inspect existing manifests and scheduler state; use new
   run directories rather than overwriting or rerunning completed outputs.
4. Choose one public cancer/mutation or aging dataset and adapt the source-report
   task to that assay. Define independent replication and null checks before
   a modest parallel pilot. Original prompt remains Perturb-seq-specific.

## Lessons Learned

- 2026-10-22: Upstream unanchored `build/` ignore rule hides source packages.
  Keep it anchored as `/build/`; do not mistake the reconstruction for recovered code.
- 2026-10-22: System `/usr/bin/python3` is 3.6.8; MCP must use the active Python
  environment. A nested venv does not inherit parent-venv dependencies; wheel
  smoke tests must install declared dependencies in their isolated environment.
- 2026-10-22: A configured zero user-namespace limit blocks both outer bwrap and
  native model shell commands; initial ENOSPC wording was misleading. The bounded complete-input mode disables shell/web rather
  than weakening the native sandbox. Large-input shell execution remains unverified.
- 2026-10-22: This is a sparse, LFS-skipping checkout. Do not run `git ls-tree -l`
  on a partial clone just to list paths; it fetches missing blobs. Use `--name-only`.
- 2026-10-22: The bootstrap packager accepts textual source companions, not binary
  Parquet attachments. Preserve original input hashes in builder provenance.
