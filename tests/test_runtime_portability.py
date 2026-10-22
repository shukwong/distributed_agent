"""No-model checks for release context selection and the MCP Python runtime."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tomllib

import pytest

from distributed_agents.corpus.models import CorpusRelease
from distributed_agents.query.access import _codex_runtime_access_plan
from distributed_agents.query.backends.codex import _main_codex_config
from distributed_agents.query.context import (
    canonical_dataset_context_path,
    selected_dataset_context_path,
    snapshot_dataset_context,
)


@pytest.fixture
def context_release(tmp_path):
    root = tmp_path / "synthetic_release"
    root.mkdir()
    for directory in ("skills", "tooling"):
        (root / directory).mkdir()
    context = root / "dataset_context.md"
    context.write_text("Synthetic numeric observations; no biological conclusions.\n")
    manifest = {
        "artifacts": {"dataset_context": {"path": context.name}},
        "capabilities": {
            "skills": {"path": "skills", "roles": {}},
            "tooling": {"path": "tooling", "entrypoints": []},
        },
    }
    manifest_path = root / "release.json"
    manifest_path.write_text(json.dumps(manifest))
    return CorpusRelease("synthetic", root, manifest_path, manifest)


def test_release_context_is_snapshotted_instead_of_legacy_portrait(context_release, tmp_path):
    skills = tmp_path / "legacy_skills"
    legacy_context = canonical_dataset_context_path(skills)
    legacy_context.parent.mkdir(parents=True)
    legacy_context.write_text("Unrelated mouse-brain Perturb-seq experiment.\n")
    selected = selected_dataset_context_path(context_release, skills)
    snapshot = tmp_path / "run/dataset_context.md"
    manifest = snapshot_dataset_context(selected, snapshot, tmp_path / "run/context.json")
    assert snapshot.read_text() == context_release.artifact("dataset_context").read_text()
    assert "Perturb-seq" not in snapshot.read_text()
    assert manifest["source_path"] == str(selected)
    assert manifest["snapshot_sha256"] == manifest["source_sha256"]


def test_legacy_release_keeps_skill_context_fallback(context_release, tmp_path):
    context_release.manifest["artifacts"].pop("dataset_context")
    assert selected_dataset_context_path(context_release, tmp_path) == canonical_dataset_context_path(tmp_path)


def test_declared_missing_context_does_not_fall_back(context_release, tmp_path):
    context_release.artifact("dataset_context").unlink()
    selected = selected_dataset_context_path(context_release, tmp_path)
    with pytest.raises(FileNotFoundError, match="dataset context source is missing"):
        snapshot_dataset_context(selected, tmp_path / "snapshot.md", tmp_path / "context.json")


def test_mcp_uses_current_environment_and_mounts_its_runtime(context_release, tmp_path):
    config = tomllib.loads(_main_codex_config(
        "Inspect the selected corpus.",
        local_skills=[],
        reasoning_effort="high",
        multi_agent=False,
        max_threads=1,
        corpus_release=context_release,
        capability_manifest=tmp_path / "capabilities.json",
    ))
    mcp = config["mcp_servers"]["distributed_agents_corpus"]
    assert mcp["command"] == str(Path(sys.executable).absolute())
    # Exercise the actual MCP entrypoint without invoking a model or network.
    completed = subprocess.run(
        [mcp["command"], mcp["args"][0], "--help"],
        text=True, capture_output=True, check=True,
    )
    assert "--release-manifest" in completed.stdout
    access = _codex_runtime_access_plan([], {}, corpus_release=context_release)
    assert Path(sys.prefix).absolute() in access.effective_roots
    assert Path(sys.base_prefix).absolute() in access.effective_roots
