"""The public Codex operator must remain closed after native isolation failures."""

import json
from pathlib import Path

import pytest

from qualia.ai.backends import codex_cli
from qualia.ai.backends.process import BackendError


@pytest.mark.parametrize('model', [None, 'gpt-6-astra', 'gpt-6-luna'])
def test_codex_operator_never_launches_despite_installed_classifier(monkeypatch, tmp_path, model):
    def forbidden(*args, **kwargs):
        pytest.fail('blocked operator touched native dispatch or model metadata')

    monkeypatch.setattr(codex_cli, 'resolve_command', forbidden)
    monkeypatch.setattr(codex_cli, 'load_catalog', forbidden)
    monkeypatch.setattr(codex_cli, 'run_process', forbidden)
    assert codex_cli.operator_available() is False
    with pytest.raises(BackendError) as failure:
        codex_cli.run_operator(tmp_path, 'Synthetic operator request.', model=model,
                               report_path='experiments/0001.md')
    assert failure.value.code == 'operator_unavailable'
    assert list(tmp_path.iterdir()) == []


def test_gate_reason_matches_recorded_runtime_failure():
    evidence = json.loads((Path(__file__).parent / 'fixtures/codex-operator-isolation.json').read_text())
    assert evidence['verified_cli_version'] == codex_cli.VERIFIED_VERSION
    assert evidence['status'] == 'blocked'
    assert evidence['model_service_requests'] == 0
    assert evidence['authorization_header_present'] is False
    reason = codex_cli.OPERATOR_UNAVAILABLE_REASON.lower()
    assert 'outside the project' in reason
    assert 'loopback' in reason
    assert 'classification' in reason
