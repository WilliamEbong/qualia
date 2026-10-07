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
SUBSCRIPTION_AUTH = {'loggedIn': True, 'authMethod': 'claude.ai', 'apiProvider': 'firstParty'}


def fixture_runner(calls, envelope, returncode=0, version='2.1.284'):
    def run(argv, **kwargs):
        if '--version' in argv:
            return ProcessResult(0, (version + ' (Claude Code)').encode(), b'')
        if argv[-3:] == ['auth', 'status', '--json']:
            return ProcessResult(0, json.dumps(SUBSCRIPTION_AUTH).encode(), b'')
        calls.append((argv, kwargs, list(Path(kwargs['cwd']).iterdir())))
        return ProcessResult(returncode, json.dumps(envelope).encode(), b'')
    return run


@pytest.mark.parametrize('version', ['2.1.284', '2.2.0', '2.10.0', '3.0.0',
                                    '2.1.284-rc.1+custom', '2.2.0+build'])
def test_claude_argv_empty_cwd_stdin_subscription_and_usage(monkeypatch, version):
    monkeypatch.setenv('ANTHROPIC_API_KEY', 'never-forward-this-key')
    monkeypatch.setenv('NODE_OPTIONS', '--require hostile.js')
    monkeypatch.setenv('CLAUDE_CODE_RETRY_WATCHDOG', '1')
    monkeypatch.setattr(claude_cli, 'resolve_command', lambda: ['installed-claude.exe'])
    calls = []
    backend = claude_cli.ClaudeCLIBackend(runner=fixture_runner(calls, {
        'type': 'result', 'is_error': False, 'structured_output': {'predictions': PREDICTIONS},
        'usage': {'input_tokens': 11, 'output_tokens': 8,
                  'cache_read_input_tokens': 4, 'cache_creation_input_tokens': 2},
        'modelUsage': {'claude-haiku-4-5-20251001': {'inputTokens': 11}},
    }, version=version))
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
                      'output_tokens': 8, 'cli_version': version,
                      'model_version': 'claude-haiku-4-5-20251001'}


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


@pytest.mark.parametrize('vendor,class_name', [
    (codex_cli, 'CodexCLIBackend'), (claude_cli, 'ClaudeCLIBackend')])
def test_classification_readiness_uses_command_discovery_only(monkeypatch, vendor, class_name):
    monkeypatch.setattr(vendor, 'resolve_command', lambda: ['installed-official-cli.exe'])
    calls = []
    backend = getattr(vendor, class_name)(runner=lambda *a, **kw: calls.append(a))
    assert backend.available() is True
    assert calls == []
    if vendor is claude_cli:
        assert vendor.operator_available() is True
    assert 'accounting' not in vendor.OPERATOR_UNAVAILABLE_REASON
    monkeypatch.setattr(vendor, 'resolve_command', lambda: None)
    assert backend.available() is False
    with pytest.raises(BackendError, match='unavailable'):
        backend.classify(SEGMENTS, SCHEMA, {})
    assert calls == []


@pytest.mark.parametrize('status', [
    {'loggedIn': False, 'authMethod': 'claude.ai', 'apiProvider': 'firstParty'},
    {'loggedIn': 1, 'authMethod': 'claude.ai', 'apiProvider': 'firstParty'},
    {'loggedIn': True, 'authMethod': 'api_key', 'apiProvider': 'firstParty'},
    {'loggedIn': True, 'authMethod': 'console', 'apiProvider': 'firstParty'},
    {'loggedIn': True, 'authMethod': 'claude.ai', 'apiProvider': 'bedrock'},
    {'loggedIn': True, 'authMethod': 'profile', 'apiProvider': 'firstParty'},
    {'loggedIn': True}, {}, [], 'not-json-private',
])
def test_claude_wrong_auth_mode_never_dispatches(monkeypatch, status):
    monkeypatch.setattr(claude_cli, 'resolve_command', lambda: ['installed-claude.exe'])
    calls = []

    def runner(argv, **options):
        calls.append((argv, options))
        assert options['prompt'] == ''
        assert options['timeout_seconds'] == 10 and options['max_output_bytes'] == 8192
        assert list(Path(options['cwd']).iterdir()) == []
        if '--version' in argv:
            return ProcessResult(0, b'2.1.284', b'')
        assert argv[-3:] == ['auth', 'status', '--json']
        body = status.encode() if isinstance(status, str) else json.dumps(status).encode()
        return ProcessResult(0, body, b'private stderr')

    backend = claude_cli.ClaudeCLIBackend(runner=runner)
    with pytest.raises(BackendError, match='subscription_auth_required') as caught:
        backend.classify(SEGMENTS, SCHEMA, {})
    assert len(calls) == 2
    assert caught.value.cli_version == '2.1.284'
    assert caught.value.input_tokens == caught.value.output_tokens == 0
    assert 'private' not in str(caught.value)
    assert all(not Path(options['cwd']).exists() for _, options in calls)


@pytest.mark.parametrize('failure,returncode', [('timeout', -1), ('output_limit', -1), (None, 1)])
def test_claude_failed_auth_probe_never_dispatches(monkeypatch, failure, returncode):
    monkeypatch.setattr(claude_cli, 'resolve_command', lambda: ['installed-claude.exe'])
    calls = []

    def runner(argv, **options):
        calls.append(argv)
        if '--version' in argv:
            return ProcessResult(0, b'2.1.284', b'')
        assert argv[-3:] == ['auth', 'status', '--json']
        return ProcessResult(returncode, json.dumps(SUBSCRIPTION_AUTH).encode(), b'', failure)

    with pytest.raises(BackendError, match='subscription_auth_required'):
        claude_cli.ClaudeCLIBackend(runner=runner).classify(SEGMENTS, SCHEMA, {})
    assert len(calls) == 2


def test_claude_subscription_probe_precedes_public_dispatch(monkeypatch):
    monkeypatch.setattr(claude_cli, 'resolve_command', lambda: ['installed-claude.exe'])
    calls = []

    def runner(argv, **options):
        calls.append(argv)
        assert list(Path(options['cwd']).iterdir()) == []
        assert 'ANTHROPIC_API_KEY' not in options['env']
        if '--version' in argv:
            return ProcessResult(0, b'2.1.284', b'')
        if argv[-3:] == ['auth', 'status', '--json']:
            assert options['prompt'] == '' and options['max_output_bytes'] == 8192
            return ProcessResult(0, json.dumps({**SUBSCRIPTION_AUTH, 'subscriptionType': 'max'}).encode(), b'')
        assert '--tools' in argv and len(calls) == 3
        return ProcessResult(0, json.dumps({'structured_output': {'predictions': PREDICTIONS},
                             'usage': {'input_tokens': 1, 'output_tokens': 2}}).encode(), b'')

    result = claude_cli.ClaudeCLIBackend(runner=runner).classify(SEGMENTS, SCHEMA, {})
    assert result['predictions'] == PREDICTIONS and len(calls) == 3


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
@pytest.mark.parametrize('version', ['0.160.0', '0.161.3', '0.1000.0', '1.0.0',
                                    '0.160.0-beta.1+custom', '0.161.3+build'])
def test_codex_complete_dispatch_with_synthetic_runner(monkeypatch, model, version):
    monkeypatch.setattr(codex_cli, 'resolve_command', lambda: ['installed-codex.exe'])
    monkeypatch.setattr(codex_cli, 'load_catalog', lambda model: {'models': [{'slug': model}]})
    seen = []

    def runner(argv, **kwargs):
        if '--version' in argv:
            return ProcessResult(0, ('codex-cli ' + version).encode(), b'')
        cwd = Path(kwargs['cwd'])
        assert list(cwd.iterdir()) == []
        assert Path(argv[argv.index('--output-schema') + 1]).parent != cwd
        seen.append(cwd)
        kwargs['output_path'].write_text(json.dumps({'predictions': PREDICTIONS}))
        return ProcessResult(0, json.dumps({'type': 'turn.completed',
                             'usage': {'input_tokens': 10, 'output_tokens': 4}}).encode(), b'')

    backend = codex_cli.CodexCLIBackend(model, runner=runner)
    assert backend.available()
    result = backend.classify(SEGMENTS, SCHEMA, {'model': model})
    assert result == {'predictions': PREDICTIONS, 'input_tokens': 10,
                      'output_tokens': 4, 'cli_version': version}
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
    with pytest.raises(BackendError) as caught:
        backend.classify(SEGMENTS, SCHEMA, {})
    assert caught.value.input_tokens == 12 and caught.value.output_tokens == 6
    assert 'private' not in str(caught.value)
    assert caught.value.code == ('tool_call' if violation == 'tool' else 'invalid_response')


@pytest.mark.parametrize('version', ['2.1.0', '2.1.283', '2.0.9999', 'bad output'])
def test_claude_below_floor_or_unparseable_version_never_dispatches(monkeypatch, version):
    monkeypatch.setattr(claude_cli, 'resolve_command', lambda: ['installed-claude.exe'])
    calls = []

    def runner(argv, **kwargs):
        calls.append(argv)
        return ProcessResult(0, version.encode(), b'')

    backend = claude_cli.ClaudeCLIBackend(runner=runner)
    assert backend.available()
    with pytest.raises(BackendError, match='unsupported_version.*update your CLI') as caught:
        backend.classify(SEGMENTS, SCHEMA, {})
    assert len(calls) == 1 and '--version' in calls[0]
    assert caught.value.cli_version == ('unknown' if version == 'bad output' else version)


@pytest.mark.parametrize('version', ['0.150.0', '0.159.0', '0.9.9999', 'bad output'])
def test_codex_below_floor_or_unparseable_version_never_dispatches(monkeypatch, version):
    monkeypatch.setattr(codex_cli, 'resolve_command', lambda: ['installed-codex.exe'])
    monkeypatch.setattr(codex_cli, 'load_catalog', lambda model: {'models': [{'slug': model}]})
    calls = []

    def runner(argv, **options):
        calls.append(argv)
        assert '--version' in argv
        return ProcessResult(0, version.encode(), b'')

    with pytest.raises(BackendError, match='unsupported_version.*update your CLI') as caught:
        codex_cli.CodexCLIBackend(runner=runner).classify(SEGMENTS, SCHEMA, {})
    assert len(calls) == 1
    assert caught.value.cli_version == ('unknown' if version == 'bad output' else version)


@pytest.fixture(params=[claude_cli, codex_cli], ids=['claude', 'codex'])
def versioned_dispatch(request, monkeypatch, tmp_path):
    vendor = request.param
    version = '2.2.0' if vendor is claude_cli else '0.161.3'
    monkeypatch.setattr(vendor, 'resolve_command', lambda: ['installed-cli.exe'])
    if vendor is codex_cli:
        monkeypatch.setattr(vendor, 'load_catalog', lambda model: {'models': [{'slug': model}]})
    (tmp_path / 'config').mkdir()
    (tmp_path / 'experiments').mkdir()
    calls = []

    def dispatch(mode, result):
        def runner(argv, **options):
            calls.append(argv)
            if '--version' in argv:
                return ProcessResult(0, version.encode(), b'')
            if argv[-3:] == ['auth', 'status', '--json']:
                return ProcessResult(0, json.dumps(SUBSCRIPTION_AUTH).encode(), b'')
            if argv[-2:] == ['login', 'status']:
                return ProcessResult(0, b'', b'Logged in using ChatGPT\n')
            if 'output_path' in options:
                options['output_path'].write_text('{"proposals":[]}', encoding='utf-8')
            return result

        monkeypatch.setattr(vendor, 'run_process', runner)
        if mode == 'operator':
            return vendor.run_operator(tmp_path, 'Synthetic task.')
        backend = (vendor.ClaudeCLIBackend() if vendor is claude_cli else vendor.CodexCLIBackend())
        return getattr(backend, mode)(SEGMENTS, SCHEMA, {'prompt': 'Propose codes.'})

    return vendor, version, calls, dispatch


def test_newer_version_proposal_dispatch_retains_version(versioned_dispatch):
    vendor, version, calls, dispatch = versioned_dispatch
    body = ({'structured_output': {'proposals': []}} if vendor is claude_cli
            else {'type': 'turn.completed'})
    body['usage'] = {'input_tokens': 2, 'output_tokens': 1}
    result = dispatch('propose', ProcessResult(0, json.dumps(body).encode(), b''))
    expected = {'proposals': [], 'input_tokens': 2, 'output_tokens': 1, 'cli_version': version}
    assert result == ({**expected, 'model_version': None} if vendor is claude_cli else expected)
    assert len(calls) == (3 if vendor is claude_cli else 2)


@pytest.mark.parametrize('mode', ['classify', 'propose', 'operator'])
@pytest.mark.parametrize('stream', ['stdout', 'stderr'])
@pytest.mark.parametrize('message', ['unknown option', 'unexpected argument', 'unrecognized arguments'])
def test_dispatch_unsupported_flag_is_safe(versioned_dispatch, mode, stream, message):
    vendor, version, calls, dispatch = versioned_dispatch
    flag = ('--permission-mode' if mode == 'operator' else '--json-schema') if vendor is claude_cli else '--output-schema'
    data = f"error: {message} '{flag}' PRIVATE_PROVIDER_TEXT".encode()
    result = ProcessResult(1, data if stream == 'stdout' else b'', data if stream == 'stderr' else b'')
    with pytest.raises(BackendError, match='unsupported_flag') as caught:
        dispatch(mode, result)
    error = caught.value
    assert error.flag == flag and flag in calls[-1] and flag in str(error)
    assert error.cli_version == version
    assert error.segment_id == (None if mode == 'operator' else '7')
    assert 'PRIVATE_PROVIDER_TEXT' not in str(error) and 'PRIVATE_PROVIDER_TEXT' not in repr(vars(error))


@pytest.mark.parametrize('case', ['unpassed', 'flag_prefix', 'no_diagnostic', 'success', 'timeout', 'tool'])
def test_flag_mapping_preserves_other_failures(versioned_dispatch, case):
    vendor, version, _, dispatch = versioned_dispatch
    flag = '--json-schema' if vendor is claude_cli else '--output-schema'
    mentioned = {'unpassed': '--private-flag', 'flag_prefix': flag + '-private'}.get(case, flag)
    message = f"unknown option '{mentioned}'" if case != 'no_diagnostic' else f"failed to use '{flag}'"
    if vendor is claude_cli:
        body = {'usage': {'input_tokens': 2, 'output_tokens': 1}}
        if case == 'tool':
            body['permission_denials'] = [{'tool_name': 'Read'}]
        stdout = json.dumps(body).encode()
    else:
        stdout = b'{"type":"turn.completed","usage":{"input_tokens":2,"output_tokens":1}}'
        if case == 'tool':
            stdout += b'\n{"type":"tool_call"}'
    result = ProcessResult(0 if case == 'success' else 1, stdout, message.encode(),
                           'timeout' if case == 'timeout' else None)
    with pytest.raises(BackendError) as caught:
        dispatch('classify', result)
    assert caught.value.code == {'tool': 'tool_call', 'timeout': 'timeout',
                                 'success': 'invalid_response'}.get(case, 'provider_error')
    assert caught.value.cli_version == version
    assert not hasattr(caught.value, 'flag')


@pytest.mark.parametrize('payload', [b'not json private key', b'[]', b'{"usage":NaN}'])
def test_claude_malformed_json_is_safe_and_record_specific(monkeypatch, payload):
    monkeypatch.setattr(claude_cli, 'resolve_command', lambda: ['installed-claude.exe'])

    def runner(argv, **kwargs):
        if argv[-3:] == ['auth', 'status', '--json']:
            return ProcessResult(0, json.dumps(SUBSCRIPTION_AUTH).encode(), b'')
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
        if argv[-3:] == ['auth', 'status', '--json']:
            return ProcessResult(0, json.dumps(SUBSCRIPTION_AUTH).encode(), b'')
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
            if status == 'guard':
                messages = [entry for path, entry in requests if path.startswith('/v1/messages')]
                block = ({'type': 'tool_use', 'id': 'synthetic_guard', 'name': 'Bash', 'input': {
                    'command': 'node -e "console.log(\'docs/02-qualia-build.md\')"',
                    'description': 'Harmless print-only guard activation probe', 'timeout': 1000}}
                    if len(messages) == 1 else {'type': 'text', 'text': 'Synthetic guard audit complete.'})
                self.send_response(200)
                self.send_header('Content-Type', 'text/event-stream')
                self.end_headers()
                events = [
                    {'type': 'message_start', 'message': {'id': 'synthetic', 'type': 'message',
                     'role': 'assistant', 'content': [], 'model': 'claude-haiku-4-5',
                     'stop_reason': None, 'stop_sequence': None,
                     'usage': {'input_tokens': 10, 'output_tokens': 1}}},
                    {'type': 'content_block_start', 'index': 0, 'content_block':
                     {**block, 'input': {}} if block['type'] == 'tool_use'
                     else {'type': 'text', 'text': ''}},
                    {'type': 'content_block_delta', 'index': 0, 'delta':
                     {'type': 'input_json_delta', 'partial_json': json.dumps(block['input'])}
                     if block['type'] == 'tool_use' else
                     {'type': 'text_delta', 'text': block['text']}},
                    {'type': 'content_block_stop', 'index': 0},
                    {'type': 'message_delta', 'delta': {'stop_reason':
                     'tool_use' if len(messages) == 1 else 'end_turn',
                     'stop_sequence': None}, 'usage': {'output_tokens': 20}},
                    {'type': 'message_stop'},
                ]
                for event in events:
                    self.wfile.write(('event: ' + event['type'] + '\ndata: '
                                      + json.dumps(event) + '\n\n').encode())
                return
            if status in ('truncated_text', 'plain_text', 'pause_turn'):
                reason = {'truncated_text': 'max_tokens', 'plain_text': 'end_turn',
                          'pause_turn': 'pause_turn'}[status]
                events = [
                    {'type': 'message_start', 'message': {'id': 'synthetic', 'type': 'message',
                     'role': 'assistant', 'content': [], 'model': 'claude-haiku-4-5',
                     'stop_reason': None, 'stop_sequence': None,
                     'usage': {'input_tokens': 10, 'output_tokens': 1}}},
                    {'type': 'content_block_start', 'index': 0,
                     'content_block': {'type': 'text', 'text': ''}},
                    {'type': 'content_block_delta', 'index': 0,
                     'delta': {'type': 'text_delta', 'text': 'Synthetic incomplete result.'}},
                    {'type': 'content_block_stop', 'index': 0},
                    {'type': 'message_delta', 'delta': {'stop_reason': reason,
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
    # Owner-approved byte/time limits are local bounds, not a provider token cap.
    assert 'max_output_tokens' not in body


@pytest.mark.parametrize('local_recorder', [400, 500, 'structured', 'invalid_structured',
                                          'truncated_text', 'plain_text', 'pause_turn'], indirect=True)
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
    scenario = request.node.callspec.params['local_recorder']
    expected_requests = {'truncated_text': 4, 'plain_text': 2, 'pause_turn': 2}.get(scenario, 1)
    assert len(messages) == expected_requests
    if expected_requests > 1:
        assert claude_cli.ClaudeCLIBackend().available()
        assert not json.loads(result.stdout).get('structured_output')
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


@pytest.mark.parametrize('local_recorder', ['guard'], indirect=True)
def test_installed_claude_project_guard_loads_at_fresh_session(tmp_path, local_recorder):
    command = claude_cli.resolve_command()
    if command is None:
        pytest.skip('installed Claude required for offline native hook activation probe')
    endpoint, requests = local_recorder
    home = tmp_path/'home'
    home.mkdir()
    root = Path(__file__).resolve().parents[1]
    protected = [root/'docs/02-qualia-build.md', root/'.claude/settings.json',
                 root/'.claude/hooks/guard.cjs', root/'.claude/hooks/guard-config.json']
    before = [path.read_bytes() for path in protected]
    env = subscription_environment()
    env.update(ANTHROPIC_BASE_URL=endpoint, ANTHROPIC_API_KEY='synthetic-local-only',
               CLAUDE_CONFIG_DIR=str(home), CLAUDE_CODE_MAX_RETRIES='0',
               CLAUDE_CODE_MAX_OUTPUT_TOKENS='128',
               CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC='1')
    argv = [*command, '-p', '--output-format', 'json', '--model', 'haiku',
            '--max-turns', '2', '--no-session-persistence', '--tools', 'Bash',
            '--allowedTools', 'Bash', '--strict-mcp-config', '--setting-sources', 'project',
            '--disable-slash-commands', '--no-chrome', '--permission-mode', 'dontAsk',
            '--permission-prompts', 'none']
    result = run_process(argv, prompt='Synthetic localhost-only harmless guard activation probe.',
                         cwd=root, env=env, timeout_seconds=30, max_output_bytes=65536)
    assert before == [path.read_bytes() for path in protected]
    assert not result.failure
    messages = [body for path, body in requests if path.startswith('/v1/messages')]
    assert len(messages) >= 2
    assert 'Shell mutation references a protected path' in json.dumps(messages[-1]['messages'])


def test_both_native_backends_propose_through_the_same_isolated_transport(monkeypatch):
    proposals = [{'kind': 'new_code', 'name': 'Hope'}]
    context = {'model': 'haiku', 'prompt': 'Propose codes.', 'codebook': [], 'refine': []}
    monkeypatch.setattr(claude_cli, 'resolve_command', lambda: ['installed-claude.exe'])
    calls = []
    claude = claude_cli.ClaudeCLIBackend(runner=fixture_runner(calls, {
        'is_error': False, 'structured_output': {'proposals': proposals},
        'usage': {'input_tokens': 2, 'output_tokens': 3}}))
    assert claude.propose(SEGMENTS, SCHEMA, context)['proposals'] == proposals
    argv, options, contents = calls[0]
    assert contents == [] and argv[argv.index('--tools') + 1] == ''
    assert 'Propose qualitative codebook entries' in options['prompt']
    with pytest.raises(BackendError, match='invalid_response'):
        claude_cli.ClaudeCLIBackend(runner=fixture_runner([], {
            'is_error': False, 'structured_output': {'predictions': []},
            'usage': {'input_tokens': 1, 'output_tokens': 1}})).propose(SEGMENTS, SCHEMA, context)

    monkeypatch.setattr(codex_cli, 'resolve_command', lambda: ['installed-codex.exe'])
    monkeypatch.setattr(codex_cli, 'load_catalog', lambda model: {'models': [{'slug': model}]})

    def runner(argv, **kwargs):
        if '--version' in argv:
            return ProcessResult(0, b'codex-cli 0.160.0', b'')
        assert list(Path(kwargs['cwd']).iterdir()) == []
        assert 'Propose qualitative codebook entries' in kwargs['prompt']
        kwargs['output_path'].write_text(json.dumps({'proposals': proposals}))
        return ProcessResult(0, json.dumps({'type': 'turn.completed',
                             'usage': {'input_tokens': 4, 'output_tokens': 5}}).encode(), b'')

    result = codex_cli.CodexCLIBackend(runner=runner).propose(SEGMENTS, SCHEMA, {**context, 'model': 'gpt-6-luna'})
    assert result == {'proposals': proposals, 'input_tokens': 4, 'output_tokens': 5, 'cli_version': '0.160.0'}
