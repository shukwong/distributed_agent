"""No-model checks for release context selection and Python runtime portability."""

from __future__ import annotations

import json
from pathlib import Path
import shlex
import subprocess
import sys
import tomllib

import pytest

from distributed_agents.build import BuildError, BuildRequest
from distributed_agents.build import runner
from distributed_agents.corpus.models import CorpusRelease
from distributed_agents.query.access import _codex_runtime_access_plan
from distributed_agents.query.backends.codex import _main_codex_config
from distributed_agents.query.context import (
    canonical_dataset_context_path,
    selected_dataset_context_path,
    snapshot_dataset_context,
)
from distributed_agents.runtime import codex as codex_runtime


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


def test_outer_enclosure_keeps_venv_path_and_mounts_external_python(tmp_path, monkeypatch):
    venv = tmp_path / "venv"
    base = tmp_path / "module-python"
    base_exec = tmp_path / "platform-runtime"
    interpreter = tmp_path / "interpreter/bin/python"
    codex = tmp_path / "codex/bin/codex"
    dataset = tmp_path / "input.parquet"
    for directory in (venv / "bin", base, base_exec, interpreter.parent, codex.parent):
        directory.mkdir(parents=True)
    interpreter.touch()
    codex.touch()
    dataset.touch()
    venv_python = venv / "bin/python"
    venv_python.symlink_to(interpreter)
    monkeypatch.setattr(sys, "executable", str(venv_python))
    monkeypatch.setattr(sys, "prefix", str(venv))
    monkeypatch.setattr(sys, "exec_prefix", str(venv))
    monkeypatch.setattr(sys, "base_prefix", str(base))
    monkeypatch.setattr(sys, "base_exec_prefix", str(base_exec))
    monkeypatch.setattr(codex_runtime.shutil, "which", lambda name: str(codex) if name == "codex" else "/usr/bin/bwrap")

    command = codex_runtime.codex_run_command(
        tmp_path / "run", model="", sandbox="workspace-write",
        codex_executable="codex", auth="chatgpt", bwrap=True,
        input_roots=(dataset,),
    )
    environment = {
        command[index + 1]: command[index + 2]
        for index, value in enumerate(command) if value == "--setenv"
    }
    assert environment["PATH"].split(":")[0] == str(venv / "bin")
    ro_mounts = {
        tuple(command[index + 1:index + 3])
        for index, value in enumerate(command) if value == "--ro-bind"
    }
    for root in (venv, base, base_exec, interpreter.parent, dataset):
        assert (str(root), str(root)) in ro_mounts
    assert command[command.index("--sandbox") + 1] == "workspace-write"


def test_live_task_names_the_selected_python_entrypoint(tmp_path, monkeypatch):
    interpreter = tmp_path / "module-python/bin/python"
    interpreter.parent.mkdir(parents=True)
    interpreter.touch()
    venv_python = tmp_path / "venv with spaces/bin/python"
    venv_python.parent.mkdir(parents=True)
    venv_python.symlink_to(interpreter)
    monkeypatch.setattr(sys, "executable", str(venv_python))
    dataset = tmp_path / "input.parquet"
    dataset.write_text("Synthetic stub; model invocation is intercepted.")

    def inspect_task(request, out, dataset):
        task = (out / "task.md").read_text()
        assert f"```sh\n{shlex.quote(str(venv_python))}\n```" in task
        assert str(interpreter) not in task
        raise BuildError("stopped before model invocation")

    monkeypatch.setattr(runner, "_run_codex", inspect_task)
    with pytest.raises(BuildError, match="stopped before model invocation"):
        runner.build_findings_report(BuildRequest("SYNTH", dataset, tmp_path / "run"))
