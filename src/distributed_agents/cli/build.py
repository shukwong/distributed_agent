"""Corpus-authoring build subcommand."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from ..build import (
    BUILD_REASONING_EFFORTS,
    BuildError,
    BuildRequest,
    DEFAULT_BUILD_MODEL,
    build_findings_report,
)


def add_parser(subcommands: argparse._SubParsersAction) -> None:
    parser = subcommands.add_parser(
        "build",
        help="Build one findings-centered source report for corpus construction.",
    )
    parser.add_argument("gene_target", help="Gene symbol, for example BDNF.")
    parser.add_argument(
        "--parquet-path",
        default="",
        help="Perturb-seq parquet for live generation (optional for report import).",
    )
    parser.add_argument(
        "--max-turns",
        type=int,
        default=None,
        help="Legacy option; unsupported by reconstructed Codex backend. Use --timeout-seconds.",
    )
    parser.add_argument(
        "--reasoning-effort",
        choices=BUILD_REASONING_EFFORTS,
        default="high",
    )
    parser.add_argument(
        "--out-dir",
        default="results/distributed_agents/build",
        help="Output root; build artifacts land in <out-dir>/<gene>/.",
    )
    parser.add_argument(
        "--report-path", default="",
        help="Import and validate an existing caller-owned report; invokes no model.",
    )
    parser.add_argument("--codex-executable", default="codex")
    parser.add_argument("--codex-auth", choices=("chatgpt", "apikey"), default="chatgpt")
    parser.add_argument(
        "--no-codex-bwrap", dest="codex_bwrap", action="store_false", default=True,
        help="Disable the outer enclosure only inside another trusted sandbox.",
    )
    parser.add_argument(
        "--timeout-seconds", type=float, default=900,
        help="Wall-clock limit for live Codex generation (default 900).",
    )
    parser.add_argument(
        "--inline-small-input", action="store_true",
        help="Supply complete tiny Parquet data inline (<=100 rows, <=64 KiB JSON); disable shell and web tools.",
    )
    parser.add_argument("--deliverable-path", default="")
    parser.add_argument("--model", default=DEFAULT_BUILD_MODEL)
    parser.add_argument("--skills-destination", default="")
    parser.add_argument("--skills-index-container-path", default="")
    parser.set_defaults(func=run)


def run(args: argparse.Namespace, _parser: argparse.ArgumentParser) -> int:
    out = Path(args.out_dir) / args.gene_target
    try:
        build_findings_report(
            BuildRequest(
                gene_target=args.gene_target,
                parquet_path=Path(args.parquet_path) if args.parquet_path else None,
                out_dir=out,
                model=args.model,
                report_path=Path(args.report_path) if args.report_path else None,
                codex_executable=args.codex_executable,
                codex_auth=args.codex_auth,
                codex_bwrap=args.codex_bwrap,
                timeout_seconds=args.timeout_seconds,
                inline_small_input=args.inline_small_input,
                max_turns=args.max_turns,
                reasoning_effort=args.reasoning_effort,
                skills_destination=args.skills_destination,
                skills_index_container_path=args.skills_index_container_path,
                deliverable_path=(
                    Path(args.deliverable_path) if args.deliverable_path else None
                ),
            )
        )
    except (BuildError, OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(f"wrote {out}")
    return 0
