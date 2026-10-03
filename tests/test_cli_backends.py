"""Synthetic CLI/process contracts; never contact a subscription service."""

import json
import os
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

from qualia.ai.backends import claude_cli, codex_cli
from qualia.ai.backends.process import (
    BackendError,
    ProcessResult,
    classification_prompt,
    run_process,
    subscription_environment,
)

SEGMENTS = [{'id': '7', 'text': 'I feel hopeful 😀.'}]
PREDICTIONS = [{'segment_id': '7', 'codes': [{'code_id': 1, 'score': 0.8,
                'rationale': 'Explicit hope.', 'span_start': 0, 'span_end': 6}]}]
SCHEMA = {'type': 'object', 'properties': {'predictions': {'type': 'array'}},
          'required': ['predictions'], 'additionalProperties': False}


def fixture_runner(calls, envelope, returncode=0):
    def run(argv, **kwargs):
        if '--version' in argv:
            return ProcessResult(0, b'2.1.284 (Claude Code)', b'')
        calls.append((argv, kwargs, list(Path(kwargs['cwd']).iterdir())))
        return ProcessResult(returncode, json.dumps(envelope).encode(), b'')
    return run


def test_claude_argv_empty_cwd_stdin_subscription_and_usage(monkeypatch):
    monkeypatch.setenv('ANTHROPIC_API_KEY', 'never-forward-this-key')
    monkeypatch.setenv('NODE_OPTIONS', '--require hostile.js')
    monkeypatch.setenv('CLAUDE_CODE_RETRY_WATCHDOG', '1')
    monkeypatch.setattr(claude_cli, 'resolve_command', lambda: ['installed-claude.exe'])
    calls = []
    backend = claude_cli.ClaudeCLIBackend(runner=fixture_runner(calls, {
        'type': 'result', 'is_error': False, 'structured_output': {'predictions': PREDICTIONS},
        'usage': {'input_tokens': 11, 'output_tokens': 8,
                  'cache_read_input_tokens': 4, 'cache_creation_input_tokens': 2},
    }))
    result = backend.classify(SEGMENTS, SCHEMA, {'model': 'haiku', 'codebook': []})
    argv, options, contents = calls[0]
    assert contents == []
    assert not Path(options['cwd']).exists()
    assert argv[argv.index('--tools') + 1] == ''
    assert argv[argv.index('--setting-sources') + 1] == ''
    assert argv[argv.index('--max-turns') + 1] == '2'
    assert '--strict-mcp-config' in argv and '--no-session-persistence' in argv
    assert '--bare' not in argv
    assert 'temperature' not in ' '.join(argv) and 'top_p' not in ' '.join(argv)
    assert SEGMENTS[0]['text'] in options['prompt']
    assert SEGMENTS[0]['text'] not in ' '.join(argv)
    assert options['env']['CLAUDE_CODE_MAX_OUTPUT_TOKENS'] == '8192'
    assert options['env']['CLAUDE_CODE_MAX_RETRIES'] == '0'
    assert options['env']['MAX_STRUCTURED_OUTPUT_RETRIES'] == '1'
    assert 'ANTHROPIC_API_KEY' not in options['env']
    assert 'NODE_OPTIONS' not in options['env']
    assert 'CLAUDE_CODE_RETRY_WATCHDOG' not in options['env']
    assert result == {'predictions': PREDICTIONS, 'input_tokens': 17,
                      'output_tokens': 8, 'cli_version': '2.1.284'}


@pytest.mark.parametrize('envelope,status,code', [
    ({'is_error': True, 'result': 'session limit API_KEY=private',
      'usage': {'input_tokens': 3, 'output_tokens': 1}}, 1, 'quota'),
    ({'is_error': False, 'structured_output': {'wrong': 'secret'},
      'usage': {'input_tokens': 3, 'output_tokens': 1}}, 0, 'invalid_response'),
    ({'is_error': False, 'structured_output': {'predictions': []},
      'usage': {'input_tokens': -4, 'output_tokens': 1}}, 0, 'invalid_response'),
])
def test_claude_errors_sanitized_and_usage_retained(monkeypatch, envelope, status, code):
    monkeypatch.setattr(claude_cli, 'resolve_command', lambda: ['installed-claude.exe'])
    backend = claude_cli.ClaudeCLIBackend(runner=fixture_runner([], envelope, status))
    with pytest.raises(BackendError) as failure:
        backend.classify(SEGMENTS, SCHEMA, {})
    assert failure.value.code == code
    assert failure.value.segment_id == '7'
    assert 'private' not in str(failure.value) and 'secret' not in str(failure.value)
    if envelope['usage']['input_tokens'] >= 0:
        assert failure.value.input_tokens == 3
        assert failure.value.output_tokens == 1


def test_codex_fails_closed_without_launch(monkeypatch):
    monkeypatch.setattr(codex_cli, 'resolve_command', lambda: ['installed-codex.exe'])
    calls = []
    backend = codex_cli.CodexCLIBackend(runner=lambda *a, **kw: calls.append(a))
    assert backend.available() is False
    assert 'token' in backend.unavailable_reason
    with pytest.raises(BackendError, match='unavailable'):
        backend.classify(SEGMENTS, SCHEMA, {})
    assert calls == []


def test_codex_builder_exact_isolation_and_restricted_catalog(tmp_path):
    argv = codex_cli.build_argv(['codex.exe'], 'gpt-6-luna', tmp_path / 'schema.json',
                                tmp_path / 'result.json', tmp_path / 'catalog.json')
    assert argv[1] == 'exec' and argv[-1] == '-'
    assert argv[argv.index('-s') + 1] == 'read-only'
    assert '--ignore-user-config' in argv and '--strict-config' in argv
    assert 'agents.enabled=false' in argv
    assert 'web_search="disabled"' in argv
    assert not any(item.startswith('model_providers.openai.') for item in argv)
    assert 'model_providers.qualia-subscription.requires_openai_auth=true' in argv
    assert 'model_providers.qualia-subscription.request_max_retries=0' in argv
    assert 'model_providers.qualia-subscription.stream_max_retries=0' in argv
    assert not any('base_url' in item or 'env_key' in item for item in argv)
    for feature in codex_cli.DISABLED_FEATURES:
        assert ['--disable', feature] in [argv[i:i+2] for i in range(len(argv)-1)]
    original = {'slug': 'gpt-6-luna', 'base_instructions': 'Original instructions',
                'apply_patch_tool_type': 'freeform', 'tool_mode': 'code_mode_only'}
    catalog = codex_cli.restricted_catalog({'models': [original]}, 'gpt-6-luna')
    record = catalog['models'][0]
    assert record['apply_patch_tool_type'] is None
    assert record['experimental_supported_tools'] == []
    assert record['shell_type'] == 'disabled' and record['tool_mode'] == 'direct'
    assert record['supports_search_tool'] is False
    assert record['base_instructions'] == original['base_instructions']
    assert original['apply_patch_tool_type'] == 'freeform'


def test_process_utf8_and_literal_stdin(tmp_path):
    prompt = 'Research 😀 & $HOME `commands` "quoted"'
    result = run_process([sys.executable, '-c',
                          'import sys; sys.stdout.buffer.write(sys.stdin.buffer.read())'],
                         prompt=prompt, cwd=tmp_path, env=dict(os.environ),
                         timeout_seconds=5, max_output_bytes=1024)
    assert result.failure is None and result.returncode == 0
    assert result.stdout.decode() == prompt


@pytest.mark.parametrize('stream', ['stdout', 'stderr'])
def test_process_output_flood_is_bounded(tmp_path, stream):
    result = run_process([sys.executable, '-c',
                          f'import sys; sys.{stream}.buffer.write(b"x"*1000000)'],
                         prompt='', cwd=tmp_path, env=dict(os.environ),
                         timeout_seconds=5, max_output_bytes=2048)
    assert result.failure == 'output_limit'
    assert len(result.stdout) + len(result.stderr) <= 2048


def test_process_timeout_kills_descendant_before_delayed_write(tmp_path):
    marker = tmp_path / 'orphan.txt'
    child = f'import time; time.sleep(1.2); open({str(marker)!r}, "w").write("orphan")'
    parent = ('import subprocess,sys,time; sys.stdin.read(); '
              f'subprocess.Popen([sys.executable,"-c",{child!r}]); time.sleep(20)')
    started = time.monotonic()
    result = run_process([sys.executable, '-c', parent], prompt='start', cwd=tmp_path,
                         env=dict(os.environ), timeout_seconds=.3, max_output_bytes=1024)
    assert result.failure == 'timeout'
    assert time.monotonic() - started < 5
    time.sleep(1.3)
    assert not marker.exists()


def test_process_file_output_limit(tmp_path):
    target = tmp_path / 'result.json'
    result = run_process([sys.executable, '-c',
                          f'open({str(target)!r}, "wb").write(b"x"*5000)'],
                         prompt='', cwd=tmp_path, env=dict(os.environ), timeout_seconds=5,
                         max_output_bytes=1024, output_path=target)
    assert result.failure == 'output_limit'


@pytest.mark.parametrize('model', ['gpt-6-luna', 'gpt-6-astra'])
def test_codex_complete_dispatch_with_synthetic_runner(monkeypatch, model):
    monkeypatch.setattr(codex_cli, 'resolve_command', lambda: ['installed-codex.exe'])
    monkeypatch.setattr(codex_cli, 'load_catalog', lambda model: {'models': [{'slug': model}]})
    seen = []

    def runner(argv, **kwargs):
        if '--version' in argv:
            return ProcessResult(0, b'codex-cli 0.160.0', b'')
        cwd = Path(kwargs['cwd'])
        assert list(cwd.iterdir()) == []
        assert Path(argv[argv.index('--output-schema') + 1]).parent != cwd
        seen.append(cwd)
        kwargs['output_path'].write_text(json.dumps({'predictions': PREDICTIONS}))
        return ProcessResult(0, json.dumps({'type': 'turn.completed',
                             'usage': {'input_tokens': 10, 'output_tokens': 4}}).encode(), b'')

    backend = codex_cli.CodexCLIBackend(model, runner=runner)
    # Patch only this fixture instance. No production constructor/env/context gate bypass exists.
    monkeypatch.setattr(backend, 'available', lambda: True)
    result = backend.classify(SEGMENTS, SCHEMA, {'model': model})
    assert result == {'predictions': PREDICTIONS, 'input_tokens': 10,
                      'output_tokens': 4, 'cli_version': '0.160.0'}
    assert seen and not seen[0].exists()


@pytest.mark.parametrize('violation', ['tool', 'malformed', 'missing_output'])
def test_codex_failure_preserves_completed_usage(monkeypatch, violation):
    monkeypatch.setattr(codex_cli, 'resolve_command', lambda: ['installed-codex.exe'])
    monkeypatch.setattr(codex_cli, 'load_catalog', lambda model: {'models': [{'slug': model}]})

    def runner(argv, **kwargs):
        if '--version' in argv:
            return ProcessResult(0, b'codex-cli 0.160.0', b'')
        data = json.dumps({'type': 'turn.completed',
                           'usage': {'input_tokens': 12, 'output_tokens': 6}})
        if violation == 'tool':
            data += '\n' + json.dumps({'type': 'item.completed',
                                      'item': {'type': 'command_execution',
                                               'command': 'private secret'}})
        if violation == 'malformed':
            kwargs['output_path'].write_text('{not valid; private}')
        return ProcessResult(0, data.encode(), b'private stderr')

    backend = codex_cli.CodexCLIBackend(runner=runner)
    monkeypatch.setattr(backend, 'available', lambda: True)
    with pytest.raises(BackendError) as caught:
        backend.classify(SEGMENTS, SCHEMA, {})
    assert caught.value.input_tokens == 12 and caught.value.output_tokens == 6
    assert 'private' not in str(caught.value)
    assert caught.value.code == ('tool_call' if violation == 'tool' else 'invalid_response')


@pytest.mark.parametrize('version', ['2.1.283', '2.1.285', 'bad output'])
def test_claude_unknown_version_never_dispatches(monkeypatch, version):
    monkeypatch.setattr(claude_cli, 'resolve_command', lambda: ['installed-claude.exe'])
    calls = []

    def runner(argv, **kwargs):
        calls.append(argv)
        return ProcessResult(0, version.encode(), b'')

    backend = claude_cli.ClaudeCLIBackend(runner=runner)
    assert not backend.available()
    with pytest.raises(BackendError):
        backend.classify(SEGMENTS, SCHEMA, {})
    assert all('--version' in argv for argv in calls)


@pytest.mark.parametrize('payload', [b'not json private key', b'[]', b'{"usage":NaN}'])
def test_claude_malformed_json_is_safe_and_record_specific(monkeypatch, payload):
    monkeypatch.setattr(claude_cli, 'resolve_command', lambda: ['installed-claude.exe'])

    def runner(argv, **kwargs):
        return ProcessResult(0, b'2.1.284' if '--version' in argv else payload, b'')

    with pytest.raises(BackendError, match='segment 7') as failure:
        claude_cli.ClaudeCLIBackend(runner=runner).classify(SEGMENTS, SCHEMA, {})
    assert 'private' not in str(failure.value)


@pytest.mark.parametrize('duplicate', ['"segment_id":"7","segment_id":"other"',
                                     '"codes":[{"code_id":1,"code_id":2}]'])
def test_transport_rejects_nested_duplicate_properties(monkeypatch, duplicate):
    monkeypatch.setattr(claude_cli, 'resolve_command', lambda: ['installed-claude.exe'])
    payload = ('{"usage":{"input_tokens":1,"output_tokens":1},'
               '"structured_output":{"predictions":[{' + duplicate + '}]}}').encode()

    def runner(argv, **kwargs):
        return ProcessResult(0, b'2.1.284' if '--version' in argv else payload, b'')

    with pytest.raises(BackendError, match='invalid_response'):
        claude_cli.ClaudeCLIBackend(runner=runner).classify(SEGMENTS, SCHEMA, {})


def test_blocked_stdin_obeys_deadline(tmp_path):
    started = time.monotonic()
    result = run_process([sys.executable, '-c', 'import time; time.sleep(20)'],
                         prompt='x' * 1_000_000, cwd=tmp_path, env=dict(os.environ),
                         timeout_seconds=.3, max_output_bytes=1024)
    assert result.failure == 'timeout' and time.monotonic() - started < 5


@pytest.mark.parametrize('vendor', [claude_cli, codex_cli])
def test_missing_cli_has_no_shell_fallback(monkeypatch, vendor):
    monkeypatch.setattr(vendor.shutil, 'which', lambda name: None)
    assert vendor.resolve_command() is None


@pytest.mark.skipif(os.name != 'nt', reason='Windows npm shim resolution')
def test_windows_npm_shims_resolve_direct_executables(tmp_path, monkeypatch):
    shim = tmp_path / 'claude.cmd'
    native = tmp_path / 'node_modules/@anthropic-ai/claude-code/bin/claude.exe'
    native.parent.mkdir(parents=True)
    native.touch()
    monkeypatch.setattr(claude_cli.shutil, 'which', lambda name: str(shim))
    assert claude_cli.resolve_command() == [str(native)]
    codex_wrapper = tmp_path / 'node_modules/@openai/codex/bin/codex.js'
    codex_wrapper.parent.mkdir(parents=True)
    codex_wrapper.touch()
    node = tmp_path / 'node.exe'
    monkeypatch.setattr(codex_cli.shutil, 'which', lambda name: str(
        node if name == 'node' else tmp_path / 'codex.ps1'))
    assert codex_cli.resolve_command() == [str(node), str(codex_wrapper)]


def test_input_bounds_before_provider_dispatch(monkeypatch):
    monkeypatch.setattr(claude_cli, 'resolve_command', lambda: ['installed-claude.exe'])
    calls = []
    backend = claude_cli.ClaudeCLIBackend(runner=lambda *args, **kw: calls.append(args))
    with pytest.raises(BackendError, match='segment oversized'):
        backend.classify([{'id': 'oversized', 'text': 'x' * 10000}], SCHEMA, {})
    assert calls == []
    with pytest.raises(BackendError):
        classification_prompt(SEGMENTS, SCHEMA, {'prompt': 'x' * 1_048_576})


def test_process_parent_exit_also_kills_descendants(tmp_path):
    marker = tmp_path / 'orphan-success.txt'
    child = f'import time; time.sleep(1.2); open({str(marker)!r}, "w").write("orphan")'
    parent = ('import subprocess,sys; sys.stdin.read(); '
              f'subprocess.Popen([sys.executable,"-c",{child!r}]); print("complete")')
    result = run_process([sys.executable, '-c', parent], prompt='start', cwd=tmp_path,
                         env=dict(os.environ), timeout_seconds=3, max_output_bytes=1024)
    assert result.failure is None and result.returncode == 0
    time.sleep(1.3)
    assert not marker.exists()


@pytest.fixture
def local_recorder(request):
    """Capture synthetic request bodies only; never retain headers or credentials."""
    requests = []

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_POST(self):
            body = self.rfile.read(int(self.headers['Content-Length']))
            requests.append((self.path, json.loads(body)))
            status = getattr(request, 'param', 400)
            if status in ('structured', 'invalid_structured'):
                prediction = {'predictions': PREDICTIONS if status == 'structured' else 'invalid'}
                events = [
                    {'type': 'message_start', 'message': {'id': 'synthetic', 'type': 'message',
                     'role': 'assistant', 'content': [], 'model': 'claude-haiku-4-5',
                     'stop_reason': None, 'stop_sequence': None,
                     'usage': {'input_tokens': 10, 'output_tokens': 1}}},
                    {'type': 'content_block_start', 'index': 0, 'content_block': {
                     'type': 'tool_use', 'id': 'tool_synthetic', 'name': 'StructuredOutput',
                     'input': {}}},
                    {'type': 'content_block_delta', 'index': 0, 'delta': {
                     'type': 'input_json_delta', 'partial_json': json.dumps(prediction)}},
                    {'type': 'content_block_stop', 'index': 0},
                    {'type': 'message_delta', 'delta': {'stop_reason': 'tool_use',
                     'stop_sequence': None}, 'usage': {'output_tokens': 20}},
                    {'type': 'message_stop'},
                ]
                self.send_response(200)
                self.send_header('Content-Type', 'text/event-stream')
                self.end_headers()
                for event in events:
                    self.wfile.write(('event: ' + event['type'] + '\ndata: '
                                      + json.dumps(event) + '\n\n').encode())
                return
            self.send_response(status)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(b'{"type":"error","error":{"type":"invalid_request_error",'
                             b'"message":"intentional synthetic audit stop"}}')

    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f'http://127.0.0.1:{server.server_port}', requests
    server.shutdown()
    server.server_close()
    thread.join(timeout=2)


@pytest.mark.parametrize('model', ['gpt-6-luna', 'gpt-6-astra'])
@pytest.mark.parametrize('local_recorder', [400, 500], indirect=True)
def test_installed_codex_advertises_no_tools_to_localhost(tmp_path, local_recorder, model):
    command = codex_cli.resolve_command()
    if command is None:
        pytest.skip('installed Codex required only for offline local wire-format probe')
    try:
        catalog = codex_cli.load_catalog(model)
    except BackendError:
        pytest.skip('current nonsecret model metadata unavailable')
    endpoint, requests = local_recorder
    cwd = tmp_path / 'cwd'
    home = tmp_path / 'home'
    cwd.mkdir()
    home.mkdir()
    catalog_path = tmp_path / 'catalog.json'
    schema_path = tmp_path / 'schema.json'
    catalog_path.write_text(json.dumps(catalog), encoding='utf-8')
    schema_path.write_text(json.dumps(SCHEMA), encoding='utf-8')
    argv = codex_cli.build_argv(command, model, schema_path, tmp_path / 'result.json', catalog_path)
    additions = {'model_providers.qualia-subscription.base_url': endpoint + '/v1',
                 'model_providers.qualia-subscription.requires_openai_auth': False,
                 'features.enable_request_compression': False}
    extra = [item for key, value in additions.items() for item in ('-c', key+'='+json.dumps(value))]
    argv[-1:-1] = extra
    env = subscription_environment()
    env['CODEX_HOME'] = str(home)  # Synthetic probe only: no real login or external model route.
    result = run_process(argv, prompt='Synthetic local tools audit.', cwd=cwd, env=env,
                         timeout_seconds=20, max_output_bytes=65536)
    assert not result.failure
    assert len(requests) == 1, result.stderr.decode('utf-8', errors='replace')[-2000:]
    path, body = requests[0]
    assert path == '/v1/responses' and body['model'] == model
    assert not body.get('tools')
    additional = [item for item in body['input'] if item.get('type') == 'additional_tools']
    assert additional and all(not item['tools'] for item in additional)
    assert 'max_output_tokens' not in body  # Explicit reason the production gate stays closed.


@pytest.mark.parametrize('local_recorder', [400, 500, 'structured', 'invalid_structured'], indirect=True)
def test_installed_claude_advertises_only_schema_transport_to_localhost(
        tmp_path, local_recorder, request):
    command = claude_cli.resolve_command()
    if command is None:
        pytest.skip('installed Claude required only for offline local wire-format probe')
    endpoint, requests = local_recorder
    cwd, home = tmp_path / 'cwd', tmp_path / 'home'
    cwd.mkdir()
    home.mkdir()
    env = subscription_environment()
    env.update(ANTHROPIC_BASE_URL=endpoint, ANTHROPIC_API_KEY='synthetic-local-only',
               CLAUDE_CONFIG_DIR=str(home), CLAUDE_CODE_MAX_RETRIES='0',
               CLAUDE_CODE_MAX_OUTPUT_TOKENS='128', MAX_STRUCTURED_OUTPUT_RETRIES='1',
               CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC='1')
    result = run_process(claude_cli.build_argv(command, 'haiku', SCHEMA),
                         prompt='Synthetic local tools audit.', cwd=cwd, env=env,
                         timeout_seconds=20, max_output_bytes=65536)
    assert not result.failure
    messages = [body for path, body in requests if path.startswith('/v1/messages')]
    assert len(messages) == 1
    # --json-schema uses a pure serializer, not an action capability.
    advertised = messages[0]['tools']
    assert len(advertised) == 1 and advertised[0]['name'] == 'StructuredOutput'
    assert advertised[0]['input_schema'] == SCHEMA
    assert messages[0]['max_tokens'] == 128
    if request.node.callspec.params['local_recorder'] == 'structured':
        assert result.returncode == 0
        assert json.loads(result.stdout)['structured_output'] == {'predictions': PREDICTIONS}
    if request.node.callspec.params['local_recorder'] == 'invalid_structured':
        assert result.returncode != 0
        assert not json.loads(result.stdout).get('structured_output')
