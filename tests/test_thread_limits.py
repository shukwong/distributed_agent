"""Caller-selected thread caps survive the runtime's environment filters."""

from __future__ import annotations

import json
import subprocess
import sys
import tomllib

import pytest

from distributed_agents.query.backends.codex import _main_codex_config
from distributed_agents.runtime.codex import codex_env
from distributed_agents.runtime.sandbox import THREAD_LIMIT_ENV_KEYS, clean_env


def test_runtime_child_inherits_explicit_thread_caps_without_unrelated_env(monkeypatch, tmp_path):
    expected = {key: str(index) for index, key in enumerate(THREAD_LIMIT_ENV_KEYS, 1)}
    for key, value in expected.items():
        monkeypatch.setenv(key, value)
    monkeypatch.setenv("UNRELATED_PRIVATE_SETTING", "must not reach the child")
    environment = codex_env(auth="chatgpt", cwd=tmp_path, fairness_sandbox=True)
    completed = subprocess.run(
        [sys.executable, "-c", "import json, os; print(json.dumps(dict(os.environ)))"],
        env=environment, text=True, capture_output=True, check=True,
    )
    observed = json.loads(completed.stdout)
    assert {key: observed[key] for key in expected} == expected
    assert "UNRELATED_PRIVATE_SETTING" not in observed


@pytest.mark.parametrize("value", ["", "0", "-1", "auto", "1.5", "1,2"])
def test_clean_environment_does_not_inherit_invalid_thread_caps(monkeypatch, value):
    for key in THREAD_LIMIT_ENV_KEYS:
        monkeypatch.setenv(key, value)
    assert not set(THREAD_LIMIT_ENV_KEYS).intersection(clean_env())


def test_clean_environment_does_not_invent_thread_caps(monkeypatch):
    for key in THREAD_LIMIT_ENV_KEYS:
        monkeypatch.delenv(key, raising=False)
    assert not set(THREAD_LIMIT_ENV_KEYS).intersection(clean_env())


def test_query_shell_preserves_thread_caps_after_native_environment_filter():
    config = tomllib.loads(_main_codex_config(
        "Inspect the selected corpus.", local_skills=[], reasoning_effort="low",
        multi_agent=False, max_threads=1,
    ))
    policy = config["shell_environment_policy"]
    assert policy["inherit"] == "all"
    assert set(THREAD_LIMIT_ENV_KEYS).issubset(policy["include_only"])
