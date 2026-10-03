import json

from typer.testing import CliRunner

from qualia.cli import app
from qualia.workspace import init_project, read_config


def test_jev_readiness_does_not_enable_or_expose_key_and_policy_is_explicit(tmp_path, monkeypatch):
    monkeypatch.setenv('QUALIA_HOME', str(tmp_path / 'home'))
    monkeypatch.setenv('TYPESAFE_API_KEY', 'synthetic-private-test-key')
    path = init_project('study', tmp_path / 'home')
    original = read_config(path)
    runner = CliRunner()
    result = runner.invoke(app, ['jev', 'check', '--project', 'study'])
    assert result.exit_code == 0, result.output
    assert 'synthetic-private-test-key' not in result.output
    record = json.loads(result.output)
    assert record['key_configured'] and record['network_requests'] == 0
    assert not record['allow_external'] and not record['jev_enabled']
    assert read_config(path) == original
    assert runner.invoke(app, ['jev', 'enable', '--project', 'study']).exit_code == 0
    enabled = read_config(path)
    assert enabled['allow_external'] and enabled['jev_enabled']
    assert {key: value for key, value in enabled.items() if key not in ('allow_external', 'jev_enabled')} == {
        key: value for key, value in original.items() if key not in ('allow_external', 'jev_enabled')}
    assert runner.invoke(app, ['jev', 'disable', '--project', 'study']).exit_code == 0
    assert read_config(path) == original
