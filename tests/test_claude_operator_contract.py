"""Public Claude operator authentication, bounded dispatch and failure accounting."""

import json

import pytest

from qualia.ai.backends import claude_cli
from qualia.ai.backends.process import BackendError, ProcessResult


@pytest.fixture
def operator(tmp_path, monkeypatch):
    project = tmp_path / 'project'
    (project / 'config/prompts').mkdir(parents=True)
    (project / 'experiments').mkdir()
    (project / 'config/prompts/classify.txt').write_text('Apply supplied frozen codes.')
    (project / 'config/prompts/.env.local').write_text('PRIVATE_SYNTHETIC_SECRET')
    (project / 'config/routing.yaml').write_text('{}')
    (project / 'config/segmentation.yaml').write_text('{}')
    monkeypatch.setattr(claude_cli, 'resolve_command', lambda: ['synthetic-claude.exe'])
    return project


def result_fixture(**extra):
    return {'result': '{"hypothesis":"Clarify the coding instructions."}',
            'usage': {'input_tokens': 10, 'cache_read_input_tokens': 20,
                      'cache_creation_input_tokens': 30, 'output_tokens': 5}, **extra}


def install_runner(monkeypatch, *, version=b'2.1.284', auth=None, result=None):
    calls = []
    if auth is None:
        auth = {'loggedIn': True, 'authMethod': 'claude.ai', 'apiProvider': 'firstParty'}
    if result is None:
        result = ProcessResult(0, json.dumps(result_fixture()).encode(), b'')

    def runner(argv, **kwargs):
        calls.append((argv, kwargs))
        if '--version' in argv:
            return ProcessResult(0, version, b'')
        if 'auth' in argv:
            return ProcessResult(0, json.dumps(auth).encode(), b'')
        return result

    monkeypatch.setattr(claude_cli, 'run_process', runner)
    return calls


def test_public_operator_requires_subscription_and_returns_observed_usage(operator, monkeypatch):
    calls = install_runner(monkeypatch)
    result = claude_cli.run_operator(operator, 'Improve implementation only.')
    assert result == {'hypothesis': 'Clarify the coding instructions.', 'input_tokens': 60,
                      'output_tokens': 5, 'cli_version': '2.1.284'}
    assert len(calls) == 3
    argv, options = calls[-1]
    assert argv[argv.index('--model') + 1] == 'opus'
    assert argv[argv.index('--max-turns') + 1] == '4'
    assert options['timeout_seconds'] == 90 and options['max_output_bytes'] == 262144
    assert options['env']['CLAUDE_CODE_MAX_OUTPUT_TOKENS'] == '8192'
    assert options['env']['CLAUDE_CODE_MAX_RETRIES'] == '0'
    assert options['cwd'] == operator


def test_operator_task_names_permitted_context_without_exposing_secrets(operator, monkeypatch):
    calls = install_runner(monkeypatch)
    claude_cli.run_operator(operator, 'Improve implementation only.')
    task = calls[-1][1]['prompt']
    # Prevent uninformed discovery: the constrained operator must know the exact files it can read.
    inventory = json.loads(task.split('Readable implementation files: ', 1)[1].split('\n', 1)[0])
    assert inventory == ['config/prompts/classify.txt', 'config/routing.yaml', 'config/segmentation.yaml']
    assert 'PRIVATE_SYNTHETIC_SECRET' not in task
    assert '.env.local' not in task
    assert 'Do not read directories' in task
    assert 'experiments/0001.md' in task


@pytest.mark.parametrize('auth', [
    {'loggedIn': False},
    {'loggedIn': True, 'authMethod': 'api_key', 'apiProvider': 'firstParty'},
    {'loggedIn': True, 'authMethod': 'claude.ai', 'apiProvider': 'thirdParty'},
    {'loggedIn': 1, 'authMethod': 'claude.ai', 'apiProvider': 'firstParty'},
])
def test_operator_refuses_non_subscription_auth_before_inference(operator, monkeypatch, auth):
    calls = install_runner(monkeypatch, auth=auth)
    with pytest.raises(BackendError, match='subscription_auth_required'):
        claude_cli.run_operator(operator, 'Synthetic task.')
    assert len(calls) == 2


@pytest.mark.parametrize('version', [b'2.1.0', b'2.1.283', b'invalid'])
def test_operator_refuses_below_floor_or_unparseable_version_before_auth(operator, monkeypatch, version):
    calls = install_runner(monkeypatch, version=version)
    with pytest.raises(BackendError, match='unsupported_version.*update your CLI') as caught:
        claude_cli.run_operator(operator, 'Synthetic task.')
    assert len(calls) == 1
    assert caught.value.cli_version == ('unknown' if version == b'invalid' else version.decode())


@pytest.mark.parametrize('version', [b'2.2.0', b'2.1.284+custom', b'2.1.284-rc.1'])
def test_operator_accepts_newer_versions_and_suffixes(operator, monkeypatch, version):
    calls = install_runner(monkeypatch, version=version)
    result = claude_cli.run_operator(operator, 'Synthetic task.')
    assert len(calls) == 3
    assert result['cli_version'] == version.decode()


@pytest.mark.parametrize(('envelope', 'failure', 'wanted'), [
    (result_fixture(result='private invalid text'), None, 'invalid_response'),
    (result_fixture(result='{"hypothesis":" ","decision":"KEEP"}'), None, 'invalid_response'),
    (result_fixture(permission_denials=[{'tool_name': 'Read'}]), None, 'scope'),
    (result_fixture(is_error=True, result='private quota limit detail'), None, 'quota'),
    (result_fixture(), 'timeout', 'timeout'),
    ({'usage': {'input_tokens': 10}}, None, 'invalid_response'),
])
def test_operator_failure_retains_usage_without_provider_text(operator, monkeypatch, envelope, failure, wanted):
    install_runner(monkeypatch, result=ProcessResult(0, json.dumps(envelope).encode(), b'private stderr', failure))
    with pytest.raises(BackendError) as caught:
        claude_cli.run_operator(operator, 'Synthetic task.')
    assert caught.value.code == wanted
    assert caught.value.input_tokens == (60 if 'output_tokens' in envelope['usage'] else 10)
    assert caught.value.cli_version == '2.1.284'
    assert 'private' not in str(caught.value)


def test_truncated_timeout_retains_process_failure(operator, monkeypatch):
    install_runner(monkeypatch, result=ProcessResult(-1, b'{', b'private stderr', 'timeout'))
    with pytest.raises(BackendError, match='timeout'):
        claude_cli.run_operator(operator, 'Synthetic task.')


@pytest.mark.parametrize('tokens', [0, -1, 8193, True])
def test_invalid_limits_never_launch(operator, monkeypatch, tokens):
    calls = install_runner(monkeypatch)
    with pytest.raises(BackendError, match='input_limit'):
        claude_cli.run_operator(operator, 'Synthetic task.', max_output_tokens=tokens)
    assert not calls
