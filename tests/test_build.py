"""Scientific-grounding and failure-preservation checks for reconstructed authoring."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

import pytest

from distributed_agents.build import (
    BuildError, BuildRequest, LEDGER_HEADINGS, build_findings_report,
    parse_structured_appendix, validate_appendix,
)
from distributed_agents.build import runner


@pytest.fixture
def appendix():
    return {
        "evidence": [{"evidence_id": "E001", "evidence_slug": "synthetic_difference",
                      "cell_type": "synthetic", "genes": ["SYNTH"],
                      "statistics": "Constructed difference = 2",
                      "description": "Software fixture, not a biological observation."}],
        "references": [],
        "biological_findings": [{
            "finding_id": "F001", "finding_type": "other", "summary": "Synthetic difference",
            "why_it_matters": "Tests evidence linkage only.", "cell_types": ["synthetic"],
            "genes": ["SYNTH"], "comparators": None, "direction": "positive",
            "confidence": "exploratory", "evidence_ids": ["E001"], "ref_ids": [],
            "literature_status": None, "main_caveats": "No biological interpretation.",
        }],
        "literature_comparisons": [], "pathways": [], "cell_type_specificity": [],
    }


def render(appendix):
    report = "# Synthetic report\n\n## Key Biological Findings\n\n[F001] uses [E001].\n"
    report += "\n## Missed-Finding Audit\n\nSoftware fixture only.\n\n## Structured Appendix\n"
    for key, title in LEDGER_HEADINGS.items():
        report += f"\n### {title}\n\n```jsonl\n"
        report += "".join(json.dumps(row) + "\n" for row in appendix[key])
        report += "```\n"
    return report


def test_import_roundtrip_with_provenance(tmp_path, appendix, monkeypatch):
    source = tmp_path / "source.md"
    source.write_text(render(appendix))
    monkeypatch.setattr(runner, "_run_codex", lambda *a: pytest.fail("import invoked model"))
    out = build_findings_report(BuildRequest("SYNTH", None, tmp_path / "build", report_path=source))
    assert json.loads((out / "structured_appendix.json").read_text()) == appendix
    manifest = json.loads((out / "run.json").read_text())
    assert manifest["status"] == "completed"
    assert manifest["backend"] == "report_import"
    assert manifest["gene_target"] == "SYNTH"
    assert manifest["usage"] is None
    assert manifest["inputs"]["source_report"]["sha256"] == hashlib.sha256(source.read_bytes()).hexdigest()
    assert len(manifest["contracts"]) == 3
    assert (out / "references.jsonl").read_text() == ""
    assert "not verified" in manifest["validation_scope"]
    with pytest.raises(ValueError, match="nonempty"):
        build_findings_report(BuildRequest("SYNTH", None, out, report_path=source))


@pytest.mark.parametrize("kind", ["duplicate", "dangling", "ungrounded", "literature"])
def test_rejects_invalid_grounding(appendix, kind):
    if kind == "duplicate":
        appendix["evidence"].append(copy.deepcopy(appendix["evidence"][0]))
    elif kind == "dangling":
        appendix["biological_findings"][0]["evidence_ids"] = ["E999"]
    elif kind == "ungrounded":
        appendix["biological_findings"][0]["evidence_ids"] = []
    else:
        appendix["biological_findings"][0]["literature_status"] = "supports_known_mechanism"
    with pytest.raises(BuildError):
        validate_appendix(appendix)


def test_derived_view_cannot_introduce_genes(appendix):
    appendix["pathways"] = [{"pathway": "Synthetic", "finding_ids": ["F001"],
                             "cell_type": ["synthetic"], "genes": ["UNSUPPORTED"],
                             "direction": None, "evidence_ids": ["E001"]}]
    with pytest.raises(BuildError, match="absent from cited findings"):
        validate_appendix(appendix)


@pytest.mark.parametrize("kind", ["order", "duplicate_key", "nan", "narrative"])
def test_parser_rejects_ambiguous_or_dangling_report(appendix, kind):
    report = render(appendix)
    if kind == "order":
        report = report.replace("### Evidence JSONL", "### References JSONL", 1)
    elif kind == "duplicate_key":
        report = report.replace('"evidence_id": "E001"', '"evidence_id": "E001", "evidence_id": "E002"', 1)
    elif kind == "nan":
        report = report.replace('"evidence_id": "E001"', '"evidence_id": NaN', 1)
    else:
        report = report.replace("[E001]", "[E999]", 1)
    with pytest.raises(BuildError):
        parse_structured_appendix(report)


def test_failed_validation_preserves_report_and_status(tmp_path, appendix):
    source = tmp_path / "bad.md"
    appendix["biological_findings"][0]["evidence_ids"] = ["E999"]
    source.write_text(render(appendix))
    out = tmp_path / "failed"
    with pytest.raises(BuildError, match="preserved diagnostics"):
        build_findings_report(BuildRequest("SYNTH", None, out, report_path=source))
    assert (out / "report.md").read_text() == source.read_text()
    assert not (out / "structured_appendix.json").exists()
    assert json.loads((out / "run.json").read_text())["status"] == "failed"
    assert json.loads((out / "validation.json").read_text())["ok"] is False


def test_fake_codex_backend_checks_completion_and_timeout(tmp_path, appendix, monkeypatch):
    dataset = tmp_path / "input.parquet"
    dataset.write_text("Synthetic stub; subprocess is mocked.")
    observed = {}
    monkeypatch.setattr(runner.shutil, "which", lambda command: "/usr/bin/true")
    monkeypatch.setattr(runner, "stage_chatgpt_codex_state", lambda destination: ())

    def fake_process(command, **kwargs):
        observed.update(kwargs)
        observed["command"] = command
        out = kwargs["cwd"]
        (out / "last_message.txt").write_text(render(appendix))
        kwargs["stdout_path"].write_text(json.dumps({"type": "turn.completed", "usage": {"input_tokens": 10, "output_tokens": 4}}) + "\n")
        kwargs["log_path"].write_text("Mocked Codex execution.\n")
        return 0

    monkeypatch.setattr(runner, "run_subprocess_with_log", fake_process)
    out = build_findings_report(BuildRequest("SYNTH", dataset, tmp_path / "live", codex_bwrap=False, timeout_seconds=7))
    assert observed["timeout_seconds"] == 7
    assert "--strict-config" in observed["command"]
    assert "workspace-write" in observed["command"]
    assert json.loads((out / "run.json").read_text())["usage"]["total_tokens"] == 14
    assert not Path(observed["env"]["CODEX_HOME"]).exists()


def test_contract_hash_mismatch_fails_before_output(tmp_path, appendix, monkeypatch):
    source = tmp_path / "source.md"
    source.write_text(render(appendix))
    monkeypatch.setitem(runner._RESOURCE_HASHES, "prompts/findings_report.md", "wrong")
    with pytest.raises(BuildError, match="hash mismatch"):
        build_findings_report(BuildRequest("SYNTH", None, tmp_path / "out", report_path=source))
    assert not (tmp_path / "out").exists()


def test_legacy_limit_not_silently_ignored(tmp_path):
    with pytest.raises(ValueError, match="cannot enforce"):
        build_findings_report(BuildRequest("SYNTH", None, tmp_path / "out", max_turns=2))


def test_grouped_narrative_citations_are_validated(appendix):
    report = render(appendix).replace("[F001] uses [E001].", "[F001, E001] [ordinary Markdown label]")
    assert parse_structured_appendix(report) == appendix
    with pytest.raises(BuildError, match="E999"):
        parse_structured_appendix(report.replace("[F001, E001]", "[F001, E001, E999]"))


def test_literature_comparison_can_attach_existing_reference(appendix):
    appendix["references"] = [{
        "ref_id": "R001", "ref_slug": "fixture_source", "source": "Fixture",
        "source_type": "other", "citation": "Synthetic software fixture only.",
        "url": "fixture.csv", "description": "Invented engineering test data.",
    }]
    appendix["literature_comparisons"] = [{
        "comparison_id": "LC001", "finding_id": "F001", "comparison_scope": "test",
        "dataset_claim": "Synthetic difference", "literature_claim": "Synthetic comparison",
        "relationship_to_literature": "fixture_only", "context_match": "synthetic",
        "evidence_ids": ["E001"], "ref_ids": ["R001"], "confidence": "exploratory",
    }]
    # Upstream allows a comparison to attach sources to a finding. It restricts
    # pathway/cell-type derived views, not comparison rows, to parent subsets.
    validate_appendix(appendix)
    appendix["literature_comparisons"][0]["ref_ids"] = ["R999"]
    with pytest.raises(BuildError, match="unresolved ref_ids"):
        validate_appendix(appendix)
