"""Check Python/Parquet access in the builder's outer enclosure without a model call.

Run from an ordinary compute-allocation terminal, not another Codex shell sandbox.
This constructs the actual launch enclosure but replaces Codex with a read-only
Python probe. It does not stage credentials or launch Codex. Native Codex sandbox
startup and successful model tool execution require separate checks.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import subprocess
import sys

from distributed_agents.runtime.codex import codex_run_command
from distributed_agents.runtime.sandbox import clean_env


PROBE = """
import json
from pathlib import Path
import sys

print(json.dumps({"python": sys.executable, "prefix": sys.prefix,
                  "base_prefix": sys.base_prefix}), flush=True)
assert Path(sys.prefix).resolve() == Path(sys.argv[2]).resolve(), (
    "Model-shell PATH selected a different Python environment"
)
import pyarrow.parquet as pq

table = pq.read_table(sys.argv[1])
assert table.num_rows == 12, "Expected the 12-row synthetic fixture"
assert set(table.column("target").to_pylist()) == {"SYNTH_ALPHA", "SYNTH_BETA"}
print(json.dumps({"status": "passed", "rows": table.num_rows,
                  "columns": table.column_names}))
"""


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--parquet-path", type=Path, required=True)
    parser.add_argument("--codex-executable", required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    dataset = args.parquet_path.resolve(strict=True)
    probe_dir = args.out_dir.resolve()
    probe_dir.mkdir(parents=True, exist_ok=True)
    command = codex_run_command(
        probe_dir, model="", sandbox="workspace-write",
        codex_executable=args.codex_executable, auth="chatgpt", bwrap=True,
        input_roots=(dataset,), ephemeral=True, strict_config=True,
        ignore_rules=True,
    )
    # Keep the helper-generated mounts and PATH, never its Codex command.
    separator = command.index("--")
    command = command[:separator + 1] + [
        "python", "-c", PROBE, str(dataset), sys.prefix,
    ]
    subprocess.run(command, env=clean_env(), check=True, timeout=30)


if __name__ == "__main__":
    main()
