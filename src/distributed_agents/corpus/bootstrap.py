"""Package validated source reports as a small, self-contained corpus release.

The release adapters use only the standard library. They are copied into each
capsule so MCP can query a capsule without depending on the source checkout.
This intentionally supports ledger retrieval, not a Claim graph or BM25 index.
"""

from __future__ import annotations

import argparse
from collections import Counter
import csv
from datetime import date
import hashlib
import json
from pathlib import Path
import re
import shutil
import sys
import tempfile
from typing import Any, Sequence


NOTICE = "Synthetic engineering fixture only; no biological or clinical conclusions."
FINDING_FIELDS = ["target_gene", "doc_id", "finding_id", "finding_type", "summary", "why_it_matters", "cell_types", "genes", "comparators", "direction", "confidence", "evidence_ids", "ref_ids", "literature_status", "main_caveats"]
EVIDENCE_FIELDS = ["target_gene", "evidence_id", "evidence_slug", "cell_type", "genes", "statistics", "description"]
REFERENCE_FIELDS = ["target_gene", "ref_id", "ref_slug", "source", "source_type", "citation", "url", "description"]


def _json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="raise")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: "|".join(value) if isinstance(value, list) else value for key, value in row.items()})


def _spec(root: Path, path: Path, kind: str, fmt: str, records: int, **extra: Any) -> dict[str, Any]:
    raw = path.read_bytes()
    media = {"csv": "text/csv", "jsonl": "application/x-ndjson", "json": "application/json", "text": "text/plain"}
    return {"path": str(path.relative_to(root)), "kind": kind, "format": fmt, "media_type": media[fmt], "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw), "records": records, **extra}


def package_reports(
    build_dirs: Sequence[Path],
    output_root: Path,
    release_id: str,
    *,
    synthetic: bool = False,
    source_files: Sequence[Path] = (),
    release_date: str | None = None,
) -> Path:
    """Validate report ledgers and atomically publish a new immutable capsule.

    Refuse replacement: give each changed evidence release a new ID or output
    root. No model is invoked, and no biological conclusions are generated here.
    """
    from distributed_agents.build import BuildError, validate_appendix
    from distributed_agents.corpus.doctor import doctor_release
    from distributed_agents.corpus.registry import _load_release

    if not re.fullmatch(r"[a-z0-9][a-z0-9._-]+", release_id):
        raise ValueError("release_id must contain at least two lowercase letters, digits, dots, underscores or hyphens")
    if not build_dirs:
        raise ValueError("at least one build directory is required")
    output_root = output_root.expanduser().resolve()
    output_root.mkdir(parents=True, exist_ok=True)
    destination = output_root / release_id
    if destination.exists():
        raise FileExistsError(f"refusing to replace existing release: {destination}")
    source_names = [path.name for path in source_files]
    if len(set(source_names)) != len(source_names):
        raise ValueError("source filenames must be unique")
    findings: list[dict[str, Any]] = []
    evidence: list[dict[str, Any]] = []
    references: list[dict[str, Any]] = []
    reports: list[dict[str, Any]] = []
    provenance: list[dict[str, Any]] = []
    targets: set[str] = set()
    for build_dir in build_dirs:
        build_dir = build_dir.expanduser().resolve()
        metadata = json.loads((build_dir / "run.json").read_text(encoding="utf-8"))
        if not isinstance(metadata, dict) or metadata.get("status") != "completed":
            raise ValueError(f"build is not completed: {build_dir}/run.json")
        target = metadata.get("gene_target")
        if not isinstance(target, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", target):
            raise ValueError(f"invalid or missing gene_target in {build_dir}/run.json")
        if target.casefold() in targets:
            raise ValueError(f"duplicate target: {target}")
        targets.add(target.casefold())
        appendix = json.loads((build_dir / "structured_appendix.json").read_text(encoding="utf-8"))
        try:
            validate_appendix(appendix)
        except BuildError as exc:
            raise ValueError(f"invalid appendix for {target}: {exc}") from exc
        if not appendix["biological_findings"]:
            raise ValueError(f"target {target} has no findings")
        report = (build_dir / "report.md").read_text(encoding="utf-8")
        if not report.strip():
            raise ValueError(f"target {target} has an empty report")
        # Re-parse the published narrative so stale sidecars cannot alter evidence.
        from distributed_agents.build import parse_structured_appendix
        try:
            parsed = parse_structured_appendix(report)
        except BuildError as exc:
            raise ValueError(f"invalid source report for {target}: {exc}") from exc
        if parsed != appendix:
            raise ValueError(f"target {target} report and appendix disagree")
        # Revalidation alone cannot establish that these are the builder's
        # original outputs: report and appendix could have changed together.
        # Check the completion receipt and byte hashes before preserving that
        # receipt as release provenance. These are consistency checks, not
        # cryptographic proof of authorship or scientific correctness.
        recorded_artifacts = metadata.get("artifacts")
        if not isinstance(recorded_artifacts, dict):
            raise ValueError(f"target {target} has no builder artifact hashes")
        for name in ("report.md", "structured_appendix.json", "validation.json"):
            spec = recorded_artifacts.get(name)
            digest = spec.get("sha256") if isinstance(spec, dict) else None
            if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
                raise ValueError(f"target {target} has no valid builder hash for {name}")
            actual = hashlib.sha256((build_dir / name).read_bytes()).hexdigest()
            if actual != digest:
                raise ValueError(f"target {target} builder artifact hash mismatch: {name}")
        validation = json.loads((build_dir / "validation.json").read_text(encoding="utf-8"))
        if not isinstance(validation, dict) or validation.get("ok") is not True:
            raise ValueError(f"target {target} builder validation did not pass")
        reports.append({"gene_target": target, "final_report": report})
        findings.extend({"target_gene": target, "doc_id": f"{target}:{row['finding_id']}", **row} for row in appendix["biological_findings"])
        evidence.extend({"target_gene": target, **row} for row in appendix["evidence"])
        references.extend({"target_gene": target, **row, "url": f"artifacts/source/{row['url']}" if row["url"] in source_names else row["url"]} for row in appendix["references"])
        provenance.append({"gene_target": target, "report_sha256": hashlib.sha256(report.encode()).hexdigest(), "builder": metadata})
    with tempfile.TemporaryDirectory(prefix=".bootstrap-", dir=output_root) as staging:
        root = Path(staging) / release_id
        root.mkdir()
        artifacts: dict[str, Any] = {}
        report_path = root / "artifacts/reports.jsonl"
        report_path.parent.mkdir()
        report_path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in reports), encoding="utf-8")
        report_schema = {"type": "object", "required": ["gene_target", "final_report"], "properties": {"gene_target": {"type": "string", "minLength": 1}, "final_report": {"type": "string", "minLength": 1}}, "additionalProperties": False}
        _json(root / "schemas/report.schema.json", report_schema)
        artifacts["reports"] = _spec(root, report_path, "per_target_reports", "jsonl", len(reports), schema="schemas/report.schema.json", target_field="gene_target", text_field="final_report", required_fields=["gene_target", "final_report"])
        for name, rows, fields, id_field in (("findings", findings, FINDING_FIELDS, "finding_id"), ("evidence", evidence, EVIDENCE_FIELDS, "evidence_id"), ("references", references, REFERENCE_FIELDS, "ref_id")):
            if not rows:
                continue
            path = root / f"artifacts/{name}.csv"
            _csv(path, rows, fields)
            artifacts[name] = _spec(root, path, f"{name}_ledger", "csv", len(rows), required_columns=fields, id_column=id_field, scope_column="target_gene")
        for index, source in enumerate(source_files):
            path = root / "artifacts/source" / source.name
            path.parent.mkdir(exist_ok=True)
            shutil.copyfile(source, path)
            if path.suffix == ".csv":
                with path.open(newline="", encoding="utf-8") as handle:
                    reader = csv.DictReader(handle)
                    fields = list(reader.fieldnames or [])
                    count = sum(1 for _ in reader)
                artifacts[f"source_{index}"] = _spec(root, path, "source_fixture" if synthetic else "source_data", "csv", count, required_columns=fields)
            else:
                artifacts[f"source_{index}"] = _spec(root, path, "source_document", "text", 1)
        warning = NOTICE if synthetic else "Curated source-report corpus. Ledger consistency does not independently establish scientific correctness."
        counts = {"reports": len(reports), "targets": len(targets), "findings": len(findings), "evidence": len(evidence), "references": len(references)}
        context_path = root / "artifacts/dataset_context.md"
        context_path.write_text(
            "# Selected corpus context\n\n" + warning + "\n\n"
            + f"This release contains {len(reports)} source reports and {len(findings)} findings. "
            + "Targets: " + ", ".join(row["gene_target"] for row in reports) + ".\n\n"
            + ("The included measurements are invented numbers used to verify report generation, retrieval, and arithmetic. No humans, animals, cancer models, aging samples, or genuine gene perturbations were measured. Do not infer biological significance, a mechanism, or clinical implications.\n\n" if synthetic else "Consult the source reports and supplied data for organism, assay, cohort, and preprocessing details. No dataset design is assumed by the packaging software.\n\n")
            + "The legacy target_gene field identifies a report target. IDs F001, E001 and R001 are local to their target. Calibration confidence is author-assigned, not a probability. No Claim graph, semantic index, or independent validation is available.\n",
            encoding="utf-8",
        )
        artifacts["dataset_context"] = _spec(root, context_path, "dataset_context", "text", 1)
        calibration = {"schema_version": "distributed_agents-bootstrap-calibration-v1", "synthetic": synthetic, "notice": warning, "counts": counts, "sources": provenance, "claim_layer": {"available": False}, "semantics": {"target_gene": "Source report target; synthetic identifiers are not biological genes.", "confidence": "Source author confidence, not a calibrated probability.", "finding_type": "Source author category, not a statistical test.", "local_ids": "Finding, evidence and reference IDs are scoped to target_gene."}}
        calibration_path = root / "artifacts/ledger_calibration.json"
        _json(calibration_path, calibration)
        _json(root / "schemas/calibration.schema.json", {"type": "object", "required": ["schema_version", "counts", "sources", "notice"]})
        artifacts["ledger_calibration"] = _spec(root, calibration_path, "findings_calibration_contract", "json", 1, schema="schemas/calibration.schema.json", required_fields=["schema_version", "counts", "sources", "notice"])
        dictionary = [{"artifact": "findings", "field": key, "value_or_pattern": "*", "meaning": value, "non_meaning": warning} for key, value in calibration["semantics"].items()]
        dictionary_path = root / "artifacts/value_dictionary.csv"
        _csv(dictionary_path, dictionary, ["artifact", "field", "value_or_pattern", "meaning", "non_meaning"])
        artifacts["value_dictionary"] = _spec(root, dictionary_path, "findings_value_dictionary", "csv", len(dictionary))
        tooling = root / "tooling"
        tooling.mkdir()
        shutil.copyfile(Path(__file__), tooling / "bootstrap.py")
        skill = root / "skills/bootstrap-ledger-skill"
        scripts = skill / "scripts"
        scripts.mkdir(parents=True)
        (skill / "SKILL.md").write_text("---\nname: bootstrap-ledger-skill\ndescription: Query a small report-derived evidence corpus.\n---\n\n" + warning + "\n\nUse corpus MCP calibrate, count, query_ledger, and resolve_evidence. Read calibration before interpreting findings. All IDs are target-scoped. No Claim graph or lexical ranking is supplied. Preserve caveats and distinguish measured facts from interpretations.\n", encoding="utf-8")
        for name, operation in (("query_ledger.py", "query"), ("calibrate.py", "calibration"), ("resolve_evidence.py", "resolve")):
            (scripts / name).write_text("import runpy\nimport sys\nfrom pathlib import Path\n" + f"sys.argv[1:1] = ['adapter', '{operation}']\n" + "runpy.run_path(str(Path(__file__).resolve().parents[3] / 'tooling/bootstrap.py'), run_name='__main__')\n", encoding="utf-8")
        manifest = {"schema_version": "distributed_agents-corpus-release-v1", "release_id": release_id, "title": "Synthetic bootstrap evidence corpus" if synthetic else "Bootstrap evidence corpus", "corpus_family": "legacy_reports", "release_date": release_date or date.today().isoformat(), "description": warning, "artifacts": artifacts, "capabilities": {"skills": {"path": "skills", "version": "bootstrap-v1", "names": ["bootstrap-ledger-skill"], "roles": {"ledger": {"skill": "bootstrap-ledger-skill", "entrypoints": {"query": "scripts/query_ledger.py", "calibration": "scripts/calibrate.py", "resolve_evidence": "scripts/resolve_evidence.py"}}}}, "tooling": {"path": "tooling", "version": "bootstrap-v1", "entrypoints": ["bootstrap.py"]}, "projections": {}}, "integrity": {"target_membership": [{"artifacts": [name for name in ("findings", "evidence", "references") if name in artifacts], "field": "target_gene", "reports_artifact": "reports", "report_field": "gene_target"}], "joins": [{"from_artifacts": ["findings"], "field": "evidence_ids", "to_artifacts": ["evidence"], "to_field": "evidence_id", "scope_field": "target_gene"}, {"from_artifacts": ["findings"], "field": "ref_ids", "to_artifacts": ["references"] if references else [], "to_field": "ref_id", "scope_field": "target_gene"}]}, "lineage": {"synthetic": synthetic, "sources": provenance}}
        if not references:
            manifest["integrity"]["joins"].pop()
        _json(root / "release.json", manifest)
        _json(root / "capabilities.json", {"schema_version": "distributed_agents-capability-manifest-v4", "capabilities": [{"id": name, "available": True} for name in ("corpus.calibration", "corpus.findings", "corpus.report_evidence")]})
        report = doctor_release(_load_release(root / "release.json"))
        if not report.ok:
            raise ValueError("release integrity check failed: " + "; ".join(report.errors))
        _json(root / "doctor.json", report.as_dict())
        root.rename(destination)
    return destination / "release.json"


def _rows(root: Path, artifact: str) -> list[dict[str, str]]:
    manifest = json.loads((root / "release.json").read_text(encoding="utf-8"))
    spec = manifest["artifacts"].get(artifact)
    if spec is None:
        return []
    path = (root / spec["path"]).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError("artifact path escapes release")
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _adapter(argv: Sequence[str]) -> int:
    root = Path(__file__).resolve().parent.parent
    parser = argparse.ArgumentParser(description="Read-only bootstrap release adapter")
    parser.add_argument("operation", choices=("query", "resolve", "calibration"))
    parser.add_argument("positionals", nargs="*")
    for option in ("gene", "finding-type", "id", "evidence-id", "ref-id"):
        parser.add_argument("--" + option, action="append", default=[])
    for option in ("finding", "fields", "artifact", "field", "canonical"):
        parser.add_argument("--" + option)
    parser.add_argument("--limit", type=int, default=20)
    for option in ("json", "evidence-only", "refs-only"):
        parser.add_argument("--" + option, action="store_true")
    args = parser.parse_args(argv)
    if not 1 <= args.limit <= 1000:
        raise ValueError("limit must be 1..1000")
    all_findings = _rows(root, "findings")
    genes = {gene.casefold() for gene in args.gene}
    selected = [row for row in all_findings if not genes or row["target_gene"].casefold() in genes]
    if args.operation == "query":
        if args.positionals != ["findings"]:
            raise ValueError("only the findings ledger is available")
        if args.id and any(":" not in value for value in args.id) and not genes:
            raise ValueError("local finding IDs require a gene filter")
        types = {value.casefold() for value in args.finding_type}
        ids = {value.casefold() for value in args.id}
        selected = [row for row in selected if (not types or row["finding_type"].casefold() in types) and (not ids or row["finding_id"].casefold() in ids or row["doc_id"].casefold() in ids)]
        fields = args.fields.split(",") if args.fields else FINDING_FIELDS
        if set(fields) - set(FINDING_FIELDS):
            raise ValueError("unknown finding fields")
        for row in selected[:args.limit]:
            print(json.dumps({key: row[key] for key in fields}, sort_keys=True))
    elif args.operation == "resolve":
        if len(genes) != 1:
            raise ValueError("exactly one gene is required")
        if not selected:
            raise ValueError("unknown target")
        evidence_ids, ref_ids = set(args.evidence_id), set(args.ref_id)
        if args.finding:
            matched = [row for row in selected if args.finding in (row["finding_id"], row["doc_id"])]
            if len(matched) != 1:
                raise ValueError("unknown finding for target")
            evidence_ids.update(filter(None, matched[0]["evidence_ids"].split("|")))
            ref_ids.update(filter(None, matched[0]["ref_ids"].split("|")))
        payload = {}
        filtered = bool(args.finding or args.evidence_id or args.ref_id)
        for name, field, ids in (("evidence", "evidence_id", evidence_ids), ("references", "ref_id", ref_ids)):
            rows = [row for row in _rows(root, name) if row["target_gene"].casefold() in genes]
            if ids - {row[field] for row in rows}:
                raise ValueError(f"unknown {name} IDs for target")
            rows = [row for row in rows if not filtered or row[field] in ids]
            payload[name] = [] if (name == "evidence" and args.refs_only) or (name == "references" and args.evidence_only) else rows
        print(json.dumps(payload, sort_keys=True))
    else:
        calibration = json.loads((root / "artifacts/ledger_calibration.json").read_text(encoding="utf-8"))
        command = args.positionals[0] if args.positionals else ""
        data: Any
        if command == "calibrate" and len(args.positionals) == 2:
            topic = args.positionals[1]
            data = calibration if topic == "summary" else calibration.get(topic.replace("-", "_"), {"available": False, "notice": calibration["notice"]})
        elif command == "describe" and len(args.positionals) == 2:
            query = args.positionals[1].casefold()
            data = [row for row in _rows(root, "value_dictionary") if query in " ".join(row.values()).casefold()][:args.limit]
        elif command == "count":
            if args.artifact != "findings" or args.field not in FINDING_FIELDS:
                raise ValueError("unsupported artifact or field")
            if args.canonical:
                raise ValueError("canonical interpretation counts are unavailable")
            frequencies = Counter(row[args.field] for row in all_findings)
            data = [{"value": value, "count": count} for value, count in sorted(frequencies.items(), key=lambda pair: (-pair[1], pair[0]))[:args.limit]]
        else:
            raise ValueError("unsupported calibration command")
        print(json.dumps({"operation": "corpus." + command, "data": data, "notice": calibration["notice"]}, sort_keys=True))
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    arguments = list(sys.argv[1:] if argv is None else argv)
    if arguments[:1] == ["adapter"]:
        return _adapter(arguments[1:])
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build-dir", type=Path, action="append", required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--release-id", required=True)
    parser.add_argument("--synthetic", action="store_true")
    parser.add_argument("--source-file", type=Path, action="append", default=[])
    parser.add_argument("--release-date")
    args = parser.parse_args(arguments)
    print(package_reports(args.build_dir, args.output_root, args.release_id, synthetic=args.synthetic, source_files=args.source_file, release_date=args.release_date))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, OSError) as error:
        print(f"error: {error}", file=sys.stderr)
        raise SystemExit(2)
