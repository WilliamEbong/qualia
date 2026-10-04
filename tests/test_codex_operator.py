"""Codex proposes strict JSON without project access or advertised action tools."""

import json
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

from qualia.ai.backends import codex_cli
from qualia.ai.backends.process import BackendError, ProcessResult, run_process

PROPOSAL = {'hypothesis': 'Clarify the coding prompt.', 'edits': [
    {'path': 'config/prompts/coding.txt', 'original_sha256': 'a' * 64,
     'content': 'Use only the frozen codebook.\n'}]}
USAGE = {'type': 'turn.completed', 'usage': {'input_tokens': 12, 'output_tokens': 6}}


def install_runner(monkeypatch, *, payload=None, events=None, failure=None,
                   returncode=0, version='0.160.0', auth=b'Logged in using ChatGPT\n',
                   auth_failure=None, auth_returncode=0):
    calls = []
    monkeypatch.setattr(codex_cli, 'resolve_command', lambda: ['installed-codex.exe'])
    monkeypatch.setattr(codex_cli, 'load_catalog', lambda model: {'models': [{'slug': model}]})

    def runner(argv, **options):
        calls.append((argv, options))
        assert list(Path(options['cwd']).iterdir()) == []
        if '--version' in argv:
            return ProcessResult(0, ('codex-cli ' + version).encode(), b'')
        if argv[-2:] == ['login', 'status']:
            assert options['prompt'] == '' and options['timeout_seconds'] == 10
            assert options['max_output_bytes'] == 8192
            return ProcessResult(auth_returncode, b'', auth, auth_failure)
        value = PROPOSAL if payload is None else payload
        options['output_path'].write_text(value if isinstance(value, str) else json.dumps(value),
                                          encoding='utf-8')
        stream = [USAGE] if events is None else events
        return ProcessResult(returncode, '\n'.join(json.dumps(item) for item in stream).encode(),
                             b'private provider stderr', failure)

    monkeypatch.setattr(codex_cli, 'run_process', runner)
    return calls


@pytest.mark.parametrize('model', [None, 'gpt-6-astra', 'gpt-6-luna'])
def test_proposal_dispatch_never_touches_project_or_report(monkeypatch, model):
    class ForbiddenPath:
        def __fspath__(self):
            pytest.fail('proposal transport tried to access project/report')

    calls = install_runner(monkeypatch)
    monkeypatch.setenv('OPENAI_API_KEY', 'never-forward')
    monkeypatch.setenv('NODE_OPTIONS', '--require hostile.js')
    prompt = 'Exact admitted prompt with literal 😀 and $HOME.'
    assert codex_cli.operator_available()
    result = codex_cli.run_operator(ForbiddenPath(), prompt, model=model,
                                    report_path=ForbiddenPath())
    assert result == {**PROPOSAL, 'input_tokens': 12, 'output_tokens': 6,
                      'cli_version': '0.160.0'}
    assert len(calls) == 3
    argv, options = calls[2]
    assert options['prompt'] == prompt
    assert argv[argv.index('-m') + 1] == (model or 'gpt-6-astra')
    assert argv[argv.index('-s') + 1] == 'read-only'
    assert '--ignore-user-config' in argv and '--ephemeral' in argv
    assert options['timeout_seconds'] == 90 and options['max_output_bytes'] == 262144
    assert 'OPENAI_API_KEY' not in options['env'] and 'NODE_OPTIONS' not in options['env']
    assert all(not Path(options['cwd']).exists() for _, options in calls)


@pytest.mark.parametrize('payload', [
    'not JSON private', '{"hypothesis":"one","hypothesis":"two","edits":[]}',
    {'hypothesis': 'ok', 'edits': [], 'command': 'private'},
    {'hypothesis': '', 'edits': []}, {'hypothesis': 'x' * 2001, 'edits': []},
    {'hypothesis': 'ok', 'edits': 'private'},
    {'hypothesis': 'ok', 'edits': [PROPOSAL['edits'][0]] * 17},
    {'hypothesis': 'ok', 'edits': [{**PROPOSAL['edits'][0], 'original_sha256': 'bad'}]},
    {'hypothesis': 'ok', 'edits': [{**PROPOSAL['edits'][0], 'command': 'private'}]},
    {'hypothesis': 'ok', 'edits': [{**PROPOSAL['edits'][0], 'content': '😀' * 16385}]},
    {'hypothesis': 'ok', 'edits': [{**PROPOSAL['edits'][0], 'content': 'x' * 50000}] * 3},
    {'hypothesis': 'ok', 'edits': [{**PROPOSAL['edits'][0], 'content': '\ud800'}]},
], ids=['malformed', 'duplicate-property', 'extra', 'empty-hypothesis', 'long-hypothesis',
        'edits-type', 'edit-count', 'hash', 'extra-edit', 'edit-bytes', 'total-bytes', 'unicode'])
def test_proposal_rejects_invalid_output_and_retains_usage(monkeypatch, tmp_path, payload):
    install_runner(monkeypatch, payload=payload)
    with pytest.raises(BackendError) as caught:
        codex_cli.run_operator(tmp_path, 'Synthetic request.')
    assert caught.value.code == 'invalid_response'
    assert caught.value.input_tokens == 12 and caught.value.output_tokens == 6
    assert caught.value.cli_version == '0.160.0' and 'private' not in str(caught.value)
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize('events,failure,status,code', [
    ([], None, 0, 'invalid_response'),
    ([USAGE], 'timeout', -1, 'timeout'),
    ([USAGE], 'output_limit', -1, 'output_limit'),
    ([USAGE], None, 1, 'provider_error'),
    ([USAGE, {'type': 'item.completed', 'item': {'type': 'command_execution'}}],
     None, 0, 'tool_call'),
    ([USAGE, {'type': 'custom_tool_call', 'name': 'apply_patch'}], None, 0, 'tool_call'),
    ([{'type': 'turn.completed', 'usage': {'input_tokens': -1, 'output_tokens': 6}}],
     None, 0, 'invalid_response'),
])
def test_proposal_transport_fails_closed(monkeypatch, tmp_path, events, failure, status, code):
    calls = install_runner(monkeypatch, events=events, failure=failure, returncode=status)
    with pytest.raises(BackendError) as caught:
        codex_cli.run_operator(tmp_path, 'Synthetic request.')
    assert caught.value.code == code and len(calls) == 3
    if USAGE in events:
        assert caught.value.input_tokens == 12 and caught.value.output_tokens == 6


@pytest.mark.parametrize('prompt,limit', [('', 8192), ('x' * 131073, 8192),
                                         ('😀' * 32769, 8192), ('\ud800', 8192),
                                         ('ok', 0), ('ok', 8193), ('ok', True)],
                         ids=['empty', 'long', 'long-utf8', 'unicode', 'zero', 'large', 'bool'])
def test_proposal_input_bounds_before_launch(monkeypatch, tmp_path, prompt, limit):
    calls = install_runner(monkeypatch)
    with pytest.raises(BackendError, match='input_limit'):
        codex_cli.run_operator(tmp_path, prompt, max_output_tokens=limit)
    assert calls == []


def test_proposal_output_token_threshold_rejects_after_dispatch_with_usage(monkeypatch, tmp_path):
    calls = install_runner(monkeypatch)
    with pytest.raises(BackendError, match='output_limit') as caught:
        codex_cli.run_operator(tmp_path, 'Synthetic request.', max_output_tokens=5)
    assert len(calls) == 3
    assert caught.value.input_tokens == 12 and caught.value.output_tokens == 6
    assert caught.value.cli_version == '0.160.0'
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize('version', ['0.159.0', '0.161.0', '0.160.0-beta.1', 'invalid'])
def test_proposal_unknown_version_never_dispatches(monkeypatch, tmp_path, version):
    calls = install_runner(monkeypatch, version=version)
    with pytest.raises(BackendError):
        codex_cli.run_operator(tmp_path, 'Synthetic request.')
    assert len(calls) == 1 and '--version' in calls[0][0]


@pytest.mark.parametrize('auth,failure,status', [
    (b'Not logged in', None, 1), (b'Logged in using an API key - private', None, 0),
    (b'Logged in using workload identity', None, 0), (b'', None, 0),
    (b'Logged in using ChatGPT\nprivate', None, 0),
    (b'Logged in using ChatGPT\n', 'timeout', -1),
    (b'Logged in using ChatGPT\n', None, 1),
])
def test_proposal_requires_verified_subscription_before_dispatch(monkeypatch, tmp_path,
                                                                 auth, failure, status):
    calls = install_runner(monkeypatch, auth=auth, auth_failure=failure, auth_returncode=status)
    with pytest.raises(BackendError, match='subscription_auth_required') as caught:
        codex_cli.run_operator(tmp_path, 'Synthetic request.')
    assert len(calls) == 2 and calls[-1][0][-2:] == ['login', 'status']
    assert caught.value.input_tokens == caught.value.output_tokens == 0
    assert caught.value.cli_version == '0.160.0' and 'private' not in str(caught.value)


def test_direct_file_gate_preserves_recorded_runtime_failure():
    evidence = json.loads((Path(__file__).parent / 'fixtures/codex-operator-isolation.json').read_text())
    assert evidence['verified_cli_version'] == codex_cli.VERIFIED_VERSION
    assert evidence['status'] == 'blocked'
    assert evidence['model_service_requests'] == 0
    assert evidence['authorization_header_present'] is False
    reason = codex_cli.DIRECT_FILE_OPERATOR_UNAVAILABLE_REASON.lower()
    assert 'outside the project' in reason and 'loopback' in reason


@pytest.fixture
def native_proposal_wire(tmp_path, monkeypatch, request):
    """Actual public transport with a synthetic home and local Responses endpoint."""
    model, scenario = request.param
    if codex_cli.resolve_command() is None:
        pytest.skip('installed Codex required for offline native proposal capture')
    try:
        catalog = codex_cli.load_catalog(model)
    except BackendError:
        pytest.skip('current nonsecret model metadata unavailable')
    home, project = tmp_path / 'home', tmp_path / 'project'
    home.mkdir()
    project.mkdir()
    sentinel = project / 'sentinel.txt'
    sentinel.write_text('SYNTHETIC_PROTECTED_SENTINEL', encoding='utf-8')
    (project / 'AGENTS.md').write_text('SYNTHETIC_PROJECT_INSTRUCTIONS', encoding='utf-8')
    integration_marker = tmp_path / 'inherited-integration-ran'
    arguments = ['-c', f'open({str(integration_marker)!r}, "w").write("ran")']
    (home / 'config.toml').write_text(
        '[features]\nshell_tool=true\n'
        '[mcp_servers.inherited]\ncommand=' + json.dumps(sys.executable) + '\nargs='
        + json.dumps(arguments) + '\n', encoding='utf-8')
    (home / 'models_cache.json').write_text(json.dumps(catalog), encoding='utf-8')
    monkeypatch.setenv('CODEX_HOME', str(home))
    requests, authorization = [], []

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_POST(self):
            authorization.append('Authorization' in self.headers)
            requests.append(json.loads(self.rfile.read(int(self.headers['Content-Length']))))
            turn = len(requests)
            if scenario == 'patch' and turn == 1:
                item = {'type': 'custom_tool_call', 'id': 'ct1', 'call_id': 'call1',
                        'name': 'apply_patch', 'input': '*** Begin Patch\n*** Delete File: '
                        + str(sentinel) + '\n*** End Patch'}
            elif scenario == 'shell' and turn == 1:
                item = {'type': 'function_call', 'id': 'fc1', 'call_id': 'call1',
                        'name': 'exec_command', 'arguments': json.dumps(
                            {'cmd': "Remove-Item -LiteralPath '"
                             + str(sentinel).replace("'", "''") + "'"})}
            else:
                item = {'type': 'message', 'id': 'msg', 'role': 'assistant', 'status': 'completed',
                        'content': [{'type': 'output_text', 'text': json.dumps(PROPOSAL),
                                     'annotations': []}]}
            events = [
                {'type': 'response.created', 'response': {'id': f'resp{turn}',
                 'object': 'response', 'status': 'in_progress', 'output': []}},
                {'type': 'response.output_item.done', 'output_index': 0, 'item': item},
                {'type': 'response.completed', 'response': {'id': f'resp{turn}',
                 'status': 'completed', 'output': [item], 'usage': {'input_tokens': 10,
                 'output_tokens': 5, 'total_tokens': 15, 'input_tokens_details': {'cached_tokens': 0},
                 'output_tokens_details': {'reasoning_tokens': 0}}}},
            ]
            self.send_response(200)
            self.send_header('Content-Type', 'text/event-stream')
            self.end_headers()
            for event in events:
                self.wfile.write(('event: ' + event['type'] + '\ndata: '
                                  + json.dumps(event) + '\n\n').encode())

    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    original_builder = codex_cli.build_argv

    def local_argv(*args):
        argv = original_builder(*args)
        settings = {'model_providers.qualia-subscription.base_url':
                    f'http://127.0.0.1:{server.server_port}/v1',
                    'features.enable_request_compression': False}
        if scenario != 'missing_auth':
            settings['model_providers.qualia-subscription.requires_openai_auth'] = False
        argv[-1:-1] = [item for key, value in settings.items()
                       for item in ('-c', key + '=' + json.dumps(value))]
        return argv

    monkeypatch.setattr(codex_cli, 'build_argv', local_argv)
    if scenario != 'missing_auth':
        def native_runner(argv, **options):
            # This fixture has no subscription credentials. Only status is synthetic;
            # the audited native exec, catalog, cwd, argv and output parsing are real.
            if argv[-2:] == ['login', 'status']:
                return ProcessResult(0, b'', b'Logged in using ChatGPT\n')
            return run_process(argv, **options)
        monkeypatch.setattr(codex_cli, 'run_process', native_runner)
    try:
        yield model, scenario, project, requests
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
        assert sentinel.read_text(encoding='utf-8') == 'SYNTHETIC_PROTECTED_SENTINEL'
        assert not (project / 'experiments').exists()
        assert not integration_marker.exists()
        assert not any(authorization)
        assert len(requests) <= 2
        for body in requests:
            assert body['model'] == model and not body.get('tools')
            additional = [item for item in body['input'] if item.get('type') == 'additional_tools']
            assert additional and all(not item['tools'] for item in additional)
            assert 'SYNTHETIC_PROTECTED_SENTINEL' not in json.dumps(body)
            assert 'SYNTHETIC_PROJECT_INSTRUCTIONS' not in json.dumps(body)


@pytest.mark.parametrize('native_proposal_wire', [
    ('gpt-6-luna', 'proposal'), ('gpt-6-astra', 'proposal'),
    ('gpt-6-astra', 'patch'), ('gpt-6-astra', 'shell'),
], indirect=True)
def test_installed_operator_no_tools_success_and_hostile_calls(native_proposal_wire):
    model, scenario, project, requests = native_proposal_wire
    try:
        result = codex_cli.run_operator(project, 'Synthetic localhost-only proposal.', model=model)
    except BackendError as error:
        assert scenario in ('patch', 'shell') and error.code in ('tool_call', 'provider_error')
    else:
        assert result['hypothesis'] == PROPOSAL['hypothesis'] and result['edits'] == PROPOSAL['edits']
        assert result['input_tokens'] > 0 and result['output_tokens'] > 0
    assert requests


@pytest.mark.parametrize('native_proposal_wire', [('gpt-6-astra', 'missing_auth')], indirect=True)
def test_installed_operator_missing_auth_never_contacts_provider(native_proposal_wire):
    model, _, project, requests = native_proposal_wire
    with pytest.raises(BackendError):
        codex_cli.run_operator(project, 'Synthetic auth-isolation probe.', model=model)
    assert requests == []
