"""Integration checks for importing, packaging, and querying new evidence."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import pytest

from distributed_agents.build import BuildRequest, build_findings_report
from distributed_agents.corpus.bootstrap import package_reports
from distributed_agents.corpus.doctor import doctor_release
from distributed_agents.corpus.mcp.binding import ReleaseBinding
from distributed_agents.corpus.mcp.errors import CorpusToolError
from distributed_agents.corpus.mcp.policy import CapabilityPolicy
from distributed_agents.corpus.mcp.service import CorpusService
from distributed_agents.corpus.registry import get_release, _load_release
from distributed_agents.query.adaptive import prepare_adaptive_context
from distributed_agents.skills.registry import RUNTIME_SKILLS_DIR


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "examples/bootstrap"


@pytest.fixture
def builds(tmp_path):
    spec = importlib.util.spec_from_file_location("generate_bootstrap_fixture", FIXTURE / "generate_fixture.py")
    generator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(generator)
    paths = generator.generate(tmp_path / "inputs")
    result = []
    for source in paths:
        destination = tmp_path / "builds" / source.stem
        build_findings_report(BuildRequest(gene_target=source.stem, parquet_path=None, out_dir=destination, report_path=source))
        result.append(destination)
    return result


def package(builds, tmp_path):
    return package_reports(builds, tmp_path / "releases", "test_synthetic", synthetic=True, source_files=[FIXTURE / "synthetic_observations.csv"], release_date="2026-10-22")


def service(manifest):
    return CorpusService(ReleaseBinding.load(manifest), CapabilityPolicy.load(manifest.parent / "capabilities.json"))


def test_package_doctor_registry_and_target_scoped_evidence(builds, tmp_path):
    manifest = package(builds, tmp_path)
    release = get_release("test_synthetic", environ={"DISTRIBUTED_AGENTS_CORPUS_RELEASE_ROOTS": str(manifest.parent.parent)})
    assert doctor_release(release).ok
    assert release.manifest["lineage"]["synthetic"] is True
    corpus = service(manifest)
    assert {tool["name"] for tool in corpus.tools()} == {"describe", "calibrate", "count", "query_ledger", "resolve_evidence"}
    assert "no biological" in corpus.call("calibrate", {"topic": "summary"})["notice"]
    findings = corpus.call("query_ledger", {"ledger": "findings"})["records"]
    assert len(findings) == 2
    assert {row["direction"] for row in findings} == {"increased", "unchanged"}
    # Both reports intentionally reuse E001/F001: these IDs must never cross targets.
    for target, expected_difference in (("SYNTH_ALPHA", 4), ("SYNTH_BETA", 0)):
        result = corpus.call("resolve_evidence", {"gene": target, "finding": "F001"})
        assert len(result["evidence"]) == len(result["references"]) == 1
        assert result["evidence"][0]["target_gene"] == target
        assert f"mean_difference={expected_difference};" in result["evidence"][0]["statistics"]
        source = manifest.parent / result["references"][0]["url"]
        assert source.read_bytes() == (FIXTURE / "synthetic_observations.csv").read_bytes()
    with pytest.raises(CorpusToolError, match="gene filter"):
        corpus.call("query_ledger", {"ledger": "findings", "ids": ["F001"]})
    with pytest.raises(CorpusToolError, match="unknown evidence"):
        corpus.call("resolve_evidence", {"gene": "SYNTH_ALPHA", "evidence_ids": ["E999"]})


def test_native_mcp_stdio_query_and_truncation(builds, tmp_path):
    manifest = package(builds, tmp_path)
    requests = [
        {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
        {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
        {"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": "query_ledger", "arguments": {"ledger": "findings", "limit": 1}}},
        {"jsonrpc": "2.0", "id": 4, "method": "tools/call", "params": {"name": "resolve_evidence", "arguments": {"gene": "SYNTH_BETA", "finding": "F001"}}},
    ]
    completed = subprocess.run([sys.executable, "-m", "distributed_agents.corpus.mcp.application", "--release-manifest", str(manifest), "--capabilities", str(manifest.parent / "capabilities.json")], input="".join(json.dumps(row) + "\n" for row in requests), text=True, capture_output=True, check=True)
    responses = [json.loads(line) for line in completed.stdout.splitlines()]
    assert len(responses) == 4
    assert responses[0]["result"]["serverInfo"]["name"] == "distributed_agents_corpus"
    query = json.loads(responses[2]["result"]["content"][0]["text"])
    assert query["truncation"]["truncated"] is True
    assert query["truncation"]["emitted"] == 1
    assert responses[3]["result"]["isError"] is False
    resolved = json.loads(responses[3]["result"]["content"][0]["text"])
    assert "mean_difference=0;" in resolved["evidence"][0]["statistics"]


def test_prepare_ledger_only_context_without_graph_projection(builds, tmp_path):
    manifest = package(builds, tmp_path)
    release = _load_release(manifest)
    assert release.manifest["capabilities"]["projections"] == {}
    task = tmp_path / "task.md"
    task.write_text("Describe the synthetic findings and their supporting evidence.")
    context = prepare_adaptive_context(
        mode="adaptive",
        release=release,
        task_path=task,
        dataset_context_path=release.artifact("dataset_context"),
        pipeline_dir=tmp_path / "pipeline",
        skills_destination=str(RUNTIME_SKILLS_DIR.parent),
        runtime_env={},
        input_roots=release.runtime_roots(),
        declared_inputs=(),
    )
    payload = json.loads(context.capability_manifest.read_text())
    capabilities = {row["id"]: row for row in payload["capabilities"]}
    for name in ("corpus.calibration", "corpus.findings", "corpus.report_evidence"):
        assert capabilities[name]["available"] is True
        assert capabilities[name]["mcp_server"] == "distributed_agents_corpus"
    for name in ("corpus.graph", "corpus.claim_relations"):
        assert capabilities[name]["available"] is False
        assert capabilities[name]["installed"] is False
    assert payload["source_paths"]["corpus_release_id"] == release.release_id
    assert payload["runtime_preflight"]["neo4j"]["configured"] is False


def test_reject_duplicate_target_without_publishing(builds, tmp_path):
    with pytest.raises(ValueError, match="duplicate target"):
        package_reports([builds[0], builds[0]], tmp_path / "releases", "duplicates")
    assert not (tmp_path / "releases/duplicates").exists()


def test_reject_stale_appendix_without_publishing(builds, tmp_path):
    sidecar = builds[0] / "structured_appendix.json"
    appendix = json.loads(sidecar.read_text())
    appendix["biological_findings"][0]["summary"] = "A stale or fabricated conclusion."
    sidecar.write_text(json.dumps(appendix))
    with pytest.raises(ValueError, match="report and appendix disagree"):
        package(builds, tmp_path)
    assert not (tmp_path / "releases/test_synthetic").exists()


def test_capsule_immutable_and_doctor_detects_tampering(builds, tmp_path):
    manifest = package(builds, tmp_path)
    with pytest.raises(FileExistsError, match="refusing to replace"):
        package(builds, tmp_path)
    path = manifest.parent / "artifacts/evidence.csv"
    path.write_text(path.read_text().replace("mean_difference=4", "mean_difference=99"))
    report = doctor_release(_load_release(manifest))
    assert not report.ok
    assert any("sha256" in error.lower() for error in report.errors)


@pytest.mark.parametrize("status", ["failed", "running", None])
def test_reject_noncompleted_builder_receipt(builds, tmp_path, status):
    receipt = builds[0] / "run.json"
    metadata = json.loads(receipt.read_text())
    metadata["status"] = status
    receipt.write_text(json.dumps(metadata))
    with pytest.raises(ValueError, match="build is not completed"):
        package(builds, tmp_path)
    assert not (tmp_path / "releases/test_synthetic").exists()


def test_reject_jointly_modified_report_and_appendix(builds, tmp_path):
    sidecar = builds[0] / "structured_appendix.json"
    report = builds[0] / "report.md"
    appendix = json.loads(sidecar.read_text())
    original_summary = appendix["biological_findings"][0]["summary"]
    new_summary = "A changed conclusion whose report and appendix still agree."
    appendix["biological_findings"][0]["summary"] = new_summary
    sidecar.write_text(json.dumps(appendix))
    report.write_text(report.read_text().replace(original_summary, new_summary))
    with pytest.raises(ValueError, match="builder artifact hash mismatch"):
        package(builds, tmp_path)
    assert not (tmp_path / "releases/test_synthetic").exists()


def test_reject_missing_builder_hash(builds, tmp_path):
    receipt = builds[0] / "run.json"
    metadata = json.loads(receipt.read_text())
    del metadata["artifacts"]["report.md"]
    receipt.write_text(json.dumps(metadata))
    with pytest.raises(ValueError, match="no valid builder hash"):
        package(builds, tmp_path)


def test_reject_failed_validation_even_with_updated_hash(builds, tmp_path):
    import hashlib

    validation_path = builds[0] / "validation.json"
    validation_path.write_text(json.dumps({"ok": False, "errors": ["Invalid output"]}))
    receipt = builds[0] / "run.json"
    metadata = json.loads(receipt.read_text())
    metadata["artifacts"]["validation.json"]["sha256"] = hashlib.sha256(validation_path.read_bytes()).hexdigest()
    receipt.write_text(json.dumps(metadata))
    with pytest.raises(ValueError, match="builder validation did not pass"):
        package(builds, tmp_path)
