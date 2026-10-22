"""Bounded inline data must be complete and must not require a model shell."""
import json
from pathlib import Path
import tomllib

import pytest

from distributed_agents.build import BuildError, BuildRequest
from distributed_agents.build import runner

pa = pytest.importorskip('pyarrow')
pq = pytest.importorskip('pyarrow.parquet')


def test_inline_snapshot_preserves_all_rows_and_source_hash(tmp_path):
    path = tmp_path / 'fixture.parquet'
    rows = [{'sample': 'one', 'value': 4.0}, {'sample': 'two', 'value': 0.0}]
    pq.write_table(pa.Table.from_pylist(rows), path)
    snapshot = json.loads(runner._small_input_snapshot(path))
    assert snapshot['complete'] is True
    assert snapshot['rows'] == rows
    assert snapshot['row_count'] == 2
    assert snapshot['source_sha256'] == runner._sha256_file(path)


@pytest.mark.parametrize('rows,match', [
    ([{'value': n} for n in range(101)], '100 rows'),
    ([{'value': 'x' * 70000}], '64 KiB'),
    ([{'value': float('nan')}], 'finite'),
])
def test_inline_snapshot_refuses_truncation_and_nonfinite_data(tmp_path, rows, match):
    path = tmp_path / 'fixture.parquet'
    pq.write_table(pa.Table.from_pylist(rows), path)
    with pytest.raises(BuildError, match=match):
        runner._small_input_snapshot(path)


def test_inline_run_disables_shell_and_web_but_keeps_native_sandbox(tmp_path, monkeypatch):
    monkeypatch.setattr(runner.shutil, 'which', lambda _: '/usr/bin/true')
    monkeypatch.setattr(runner, 'stage_chatgpt_codex_state', lambda _: ())
    observed = {}

    def fake_process(command, **kwargs):
        observed['command'] = command
        observed['config'] = tomllib.loads((Path(kwargs['env']['CODEX_HOME']) / 'config.toml').read_text())
        (tmp_path / 'last_message.txt').write_text('Report placeholder; this test checks launch policy only.')
        kwargs['stdout_path'].write_text(json.dumps({'type': 'turn.completed'}) + '\n')
        return 0

    monkeypatch.setattr(runner, 'run_subprocess_with_log', fake_process)
    request = BuildRequest('SYNTH', tmp_path/'fixture.parquet', tmp_path,
                           inline_small_input=True, codex_bwrap=False)
    runner._run_codex(request, tmp_path, request.parquet_path)
    assert observed['config']['features']['shell_tool'] is False
    assert observed['config']['web_search'] == 'disabled'
    command = observed['command']
    assert command[command.index('--sandbox') + 1] == 'workspace-write'


@pytest.mark.parametrize('nested', [False, True])
def test_inline_rejects_duplicate_fields_instead_of_losing_values(tmp_path, nested):
    arrays = [pa.array([1]), pa.array([2])]
    if nested:
        array = pa.StructArray.from_arrays(arrays, names=['value', 'value'])
        table = pa.Table.from_arrays([array], names=['nested'])
    else:
        table = pa.Table.from_arrays(arrays, names=['value', 'value'])
    path = tmp_path / 'duplicates.parquet'
    pq.write_table(table, path)
    with pytest.raises(BuildError, match='duplicate Parquet field names'):
        runner._small_input_snapshot(path)
