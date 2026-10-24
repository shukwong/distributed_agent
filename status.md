# Status

Last updated: 2026-10-24 EDT

## Goal

First milestone is complete: fork DistributedAgents, generate a tiny new
synthetic corpus, and query it with native evidence tools. Next: verify normal
model shell input access and the complete tiny workflow on FRCE. A biological
pilot and parallel scaling have not started.

## Current State

- Fork: https://github.com/shukwong/distributed_agent
- Branch: `research/bootstrap-corpus`; the default `main` still follows upstream.
- Draft PR: https://github.com/shukwong/distributed_agent/pull/1
- Upstream baseline: `c20445d929f5aedce1d539ef6fbd8843b8c06e25`.
- Milestone implementation commit: `8ed5d03`; subsequent commits document the
  diagnosis and continuation. Use the latest branch tip and record its SHA.
- Reconstructed the missing report builder, added validated ledger packaging,
  release-owned dataset context, optional graph handling and interpreter fixes.
- Live synthetic generation and native MCP query succeeded. Committed evidence:
  `examples/bootstrap/verified_run/`. No research process remains running in
  the originating task.
- Start FRCE continuation with `FRCE_HANDOFF.md`. It contains materials, sparse
  checkout, setup, commands, known runtime issues and acceptance criteria.
- `examples/bootstrap/probe_outer_python.py` checks the actual outer enclosure's
  Python and Parquet access without launching a model or staging credentials.

## Host Diagnosis and FRCE Follow-up

- The original Biowulf execution environment disables new user namespaces.
  Namespace creation failures were not a disk-space shortage or a demonstrated
  leak. No host settings were changed and no support message was sent.
- Successful live generation used `--inline-small-input`, which supplies the
  complete bounded input and disables model shell/web tools. Native sandboxing
  remained configured. This does not prove ordinary shell execution works.
- The user reported namespace and bubblewrap checks passing on two FRCE compute
  nodes. An initial Codex test ran through another Codex agent's shell tool and
  failed with `app-server socket directory must be a user-owned directory with
  mode 0700` plus a timeout.
- Exact-version source for Codex 0.160.0 shows its reserved daemon directory is
  masked within its shell sandbox. Nested execution is the likely explanation;
  no host permission repair was established as necessary. `FRCE_HANDOFF.md`
  links the source and gives the corrected `codex sandbox -- COMMAND` syntax.
- The user subsequently confirmed the corrected direct-terminal sandbox probe
  worked. This is user-reported, not independently rerun by the originating task.
- Complete shell-enabled DistributedAgents execution on FRCE is still unverified.
  Prepare launches with Codex, but execute this smoke from an ordinary allocation
  terminal or an authorized host launch that preserves the child sandbox.

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

## Verification

- 39 regression tests passed. Wheel build and isolated install/CLI smoke passed;
  `pip check` passed.
- Live release doctor: 37 checks, zero errors.
- Live build: two evidence rows and two findings; differences +4 and 0 match the
  synthetic input. Codex 0.160.0, model `gpt-5.6-sol`, 15,668 total tokens.
- Live query: seven successful native MCP calls, correct scoped citations and
  arithmetic. 65,635 total tokens, including 48,640 cached input.
  `completed_with_warnings` reflected an unknown enterprise feature requirement;
  no evidence-tool failure occurred.
- An earlier shell-based generation failed to read input and returned an honest
  empty report; it was excluded from the successful release.
- FRCE handoff: eight Bash blocks passed syntax checks, diagnostic helper passed
  compile/help checks, all four reference artifact hashes match the receipt.
  Diagnostic execution and the live FRCE workflow await FRCE.

## Next Actions

1. Read `FRCE_HANDOFF.md` and inspect the new host's allocation and existing work.
2. Verify the actual outer enclosure's Python/Parquet access before model calls.
   `runtime/codex.py` resolves the venv interpreter for PATH and omits the explicit
   `sys.base_prefix` builder mount. Fix these portability issues if the probe
   fails, preserving the intended interpreter and read-only runtime mounts.
3. Complete two shell-enabled synthetic builds, package the release, run its
   doctor and a direct native-evidence query. Inspect actual input-read calls and
   numeric findings; schema success with empty ledgers is not milestone success.
4. Preserve reproducible receipts, update the draft PR and status, and keep
   internal host details in ignored local artifacts.
5. Select one public cancer/mutation or aging pilot. Adapt the Perturb-seq-specific
   report contract and define null checks, independent replication and a bounded
   parallel pilot before considering thousands of tasks.

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
