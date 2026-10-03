"""Offline operator contracts and installed native file-tool sentinel probes."""

import json
import os
import subprocess
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

from qualia.ai.backends import claude_cli, codex_cli
from qualia.ai.backends.process import (
    BackendError,
    ProcessResult,
    run_process,
    subscription_environment,
)


@pytest.fixture
def project(tmp_path):
    project = tmp_path / 'project'
    (project / 'config/prompts').mkdir(parents=True)
    (project / 'experiments').mkdir()
    for name, text in {'IMPROVEMENT.md': 'Improve implementation only.',
                       'METHODOLOGY.md': 'SECRET_METHOD_SENTINEL',
                       'project.db': 'SECRET_DB_SENTINEL', '.env': 'SECRET_ENV_SENTINEL',
                       'codebook.json': 'SECRET_CODES_SENTINEL',
                       'CLAUDE.md': 'SECRET_CLAUDE_SENTINEL', 'AGENTS.md': 'SECRET_AGENTS_SENTINEL',
                       'improvement.yaml': 'SECRET_POLICY_SENTINEL',
                       'config/routing.yaml': 'before', 'config/segmentation.yaml': '{}',
                       'experiments/0001.md': 'SECRET_OLD_REPORT_SENTINEL'}.items():
        (project / name).write_text(text, encoding='utf-8')
    (project / '.git').mkdir()
    (project / '.git/config').write_text('SECRET_GIT_SENTINEL')
    return project


@pytest.mark.parametrize('vendor', [claude_cli, codex_cli])
def test_operator_readiness_gate_never_launches(vendor, project, monkeypatch):
    monkeypatch.setattr(vendor, 'resolve_command', lambda: pytest.fail('operator launched'))
    assert not vendor.operator_available() and vendor.OPERATOR_UNAVAILABLE_REASON
    with pytest.raises(BackendError, match='operator_unavailable'):
        vendor.run_operator(project, 'Synthetic task.', report_path='experiments/0002.md')


def test_operator_exact_argv_scope_and_output_fixture(project, monkeypatch):
    monkeypatch.setattr(claude_cli, 'resolve_command', lambda: ['installed-claude.exe'])
    calls = []

    def runner(argv, **kwargs):
        if '--version' in argv:
            return ProcessResult(0, b'2.1.284', b'')
        settings_path = Path(argv[argv.index('--settings') + 1])
        settings = json.loads(settings_path.read_text())
        assert settings_path.parent != project
        assert 'Edit(./config/prompts/**)' in settings['permissions']['allow']
        assert 'Read(./codebook.json)' in settings['permissions']['deny']
        assert 'Read(./.env)' in settings['permissions']['deny']
        assert 'Edit(./experiments/0001.md)' in settings['permissions']['deny']
        assert kwargs['cwd'] == project
        assert argv[argv.index('--tools') + 1] == 'Read,Edit,Write'
        assert '--restricted' in argv and '--bare' not in argv
        assert argv[argv.index('--permission-mode') + 1] == 'dontAsk'
        assert argv[argv.index('--setting-sources') + 1] == ''
        assert kwargs['env']['CLAUDE_CODE_MAX_RETRIES'] == '0'
        calls.append(settings_path)
        return ProcessResult(0, json.dumps({'result': '{"hypothesis":"Clearer instructions."}',
            'usage': {'input_tokens': 10, 'output_tokens': 5}}).encode(), b'')

    result = claude_cli._run_operator(project, 'Trusted IMPROVEMENT prompt.', runner=runner,
                                      report_path='experiments/0002.md')
    assert result == {'hypothesis': 'Clearer instructions.', 'cli_version': '2.1.284',
                      'input_tokens': 10, 'output_tokens': 5}
    assert not calls[0].exists()


@pytest.mark.parametrize('path', ['experiments/0001.md', '../outside.md', 'experiments/old.md'])
def test_existing_or_escaping_report_rejected(project, path):
    with pytest.raises(BackendError):
        claude_cli.operator_settings(project, path)


def test_mutable_hardlink_refused_before_launch(project, tmp_path):
    outside = tmp_path / 'outside-secret'
    outside.write_text('protected')
    os.link(outside, project / 'config/prompts/linked')
    with pytest.raises(BackendError, match='scope'):
        claude_cli.operator_settings(project, 'experiments/0002.md')
    assert outside.read_text() == 'protected'


def test_symlink_refused_before_launch(project, tmp_path):
    outside = tmp_path / 'outside-secret'
    outside.write_text('protected')
    try:
        (project / 'config/prompts/link').symlink_to(outside)
    except OSError:
        pytest.skip('host does not permit unprivileged symlink creation')
    with pytest.raises(BackendError, match='scope'):
        claude_cli.operator_settings(project, 'experiments/0002.md')


@pytest.mark.skipif(os.name != 'nt', reason='native Windows junction')
def test_windows_junction_refused_before_launch(project, tmp_path):
    outside = tmp_path / 'outside-directory'
    outside.mkdir()
    (outside / 'secret').write_text('SECRET_LINK_SENTINEL')
    junction = project / 'config/prompts/junction'
    result = subprocess.run(['cmd.exe', '/c', 'mklink', '/J', str(junction), str(outside)],
                            capture_output=True, timeout=5, creationflags=subprocess.CREATE_NO_WINDOW)
    assert result.returncode == 0 and junction.is_junction()
    with pytest.raises(BackendError, match='scope'):
        claude_cli.operator_settings(project, 'experiments/0002.md')
    assert (outside / 'secret').read_text() == 'SECRET_LINK_SENTINEL'


def test_native_claude_file_tool_confinement(project, tmp_path):
    command = claude_cli.resolve_command()
    if command is None:
        pytest.skip('installed Claude required for offline native permission probe')
    outside = tmp_path / 'outside.txt'
    outside.write_text('SECRET_OUTSIDE_SENTINEL')
    vault = tmp_path / 'vault'
    vault.mkdir()
    (vault / 'gold.json').write_text('SECRET_VAULT_SENTINEL')
    home = tmp_path / 'synthetic-home'
    home.mkdir()
    settings = tmp_path / 'settings.json'
    settings.write_text(json.dumps(claude_cli.operator_settings(project, 'experiments/0002.md')))
    requests = []
    reads = ['config/routing.yaml', 'project.db', 'codebook.json', '.env', '.git/config',
             'METHODOLOGY.md', 'experiments/0001.md', 'CLAUDE.md', 'AGENTS.md', 'improvement.yaml',
             str(outside), '../outside.txt', str(vault / 'gold.json')]
    if os.name == 'nt':
        reads.extend(['PROJECT.DB', 'codebook.json::$DATA'])
    writes = [('Edit', {'file_path': str(project / 'config/routing.yaml'),
                       'old_string': 'before', 'new_string': 'after'}),
              ('Write', {'file_path': str(project / 'config/prompts/new.txt'), 'content': 'candidate'}),
              ('Write', {'file_path': str(project / 'experiments/0002.md'), 'content': 'Hypothesis'}),
              ('Write', {'file_path': str(project / 'experiments/proposals/0002/idea.md'), 'content': 'Proposal'}),
              ('Write', {'file_path': str(project / 'METHODOLOGY.md'), 'content': 'FORBIDDEN'}),
              ('Write', {'file_path': str(project / 'project.db'), 'content': 'FORBIDDEN'}),
              ('Write', {'file_path': str(outside), 'content': 'FORBIDDEN'})]
    writes.extend(('Write', {'file_path': str(project / path), 'content': 'FORBIDDEN'})
                  for path in ('codebook.json', '.env', '.git/config', 'experiments/0001.md',
                               'CLAUDE.md', 'AGENTS.md', 'improvement.yaml', '../outside.txt'))

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_POST(self):
            body = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
            if not self.path.startswith('/v1/messages'):
                self.send_response(400)
                self.end_headers()
                return
            requests.append(body)
            turn = len(requests)
            actions = ([('Read', {'file_path': str(project / path) if not Path(path).is_absolute() else path})
                        for path in reads] if turn == 1 else writes if turn == 2 else [])
            events = [{'type': 'message_start', 'message': {'id': f'synthetic-{turn}',
                       'type': 'message', 'role': 'assistant', 'content': [], 'model': 'claude-sonnet-4-6',
                       'stop_reason': None, 'stop_sequence': None,
                       'usage': {'input_tokens': 10, 'output_tokens': 1}}}]
            for index, (name, arguments) in enumerate(actions):
                events.extend([
                    {'type': 'content_block_start', 'index': index, 'content_block': {
                     'type': 'tool_use', 'id': f'action_{turn}_{index}', 'name': name, 'input': {}}},
                    {'type': 'content_block_delta', 'index': index, 'delta': {
                     'type': 'input_json_delta', 'partial_json': json.dumps(arguments)}},
                    {'type': 'content_block_stop', 'index': index}])
            if not actions:
                events.extend([
                    {'type': 'content_block_start', 'index': 0, 'content_block': {'type': 'text', 'text': ''}},
                    {'type': 'content_block_delta', 'index': 0, 'delta': {
                     'type': 'text_delta', 'text': '{"hypothesis":"Synthetic confinement probe."}'}},
                    {'type': 'content_block_stop', 'index': 0}])
            events.extend([{'type': 'message_delta', 'delta': {
                'stop_reason': 'tool_use' if actions else 'end_turn', 'stop_sequence': None},
                'usage': {'output_tokens': 20}}, {'type': 'message_stop'}])
            self.send_response(200)
            self.send_header('Content-Type', 'text/event-stream')
            self.end_headers()
            for event in events:
                self.wfile.write(('event: ' + event['type'] + '\ndata: ' + json.dumps(event) + '\n\n').encode())

    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    env = subscription_environment()
    env.update(ANTHROPIC_BASE_URL=f'http://127.0.0.1:{server.server_port}',
               ANTHROPIC_API_KEY='synthetic-local-only', CLAUDE_CONFIG_DIR=str(home),
               CLAUDE_CODE_MAX_RETRIES='0', CLAUDE_CODE_MAX_OUTPUT_TOKENS='1024',
               CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC='1')
    try:
        result = run_process(claude_cli.build_operator_argv(command, 'sonnet', settings),
            prompt='Synthetic permission enforcement probe. Execute only offered synthetic actions.',
            cwd=project, env=env, timeout_seconds=30, max_output_bytes=65536)
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
    assert result.failure is None
    assert len(requests) == 3, result.stderr.decode(errors='replace')[-1000:]
    assert {tool['name'] for tool in requests[0]['tools']} == {'Read', 'Edit', 'Write'}
    assert (project / 'config/routing.yaml').read_text() == 'after'
    assert (project / 'config/prompts/new.txt').read_text() == 'candidate'
    assert (project / 'experiments/0002.md').read_text() == 'Hypothesis'
    assert (project / 'experiments/proposals/0002/idea.md').read_text() == 'Proposal'
    assert (project / 'METHODOLOGY.md').read_text() == 'SECRET_METHOD_SENTINEL'
    assert (project / 'project.db').read_text() == 'SECRET_DB_SENTINEL'
    for path, original in [('codebook.json', 'SECRET_CODES_SENTINEL'), ('.env', 'SECRET_ENV_SENTINEL'),
                           ('.git/config', 'SECRET_GIT_SENTINEL'),
                           ('CLAUDE.md', 'SECRET_CLAUDE_SENTINEL'),
                           ('AGENTS.md', 'SECRET_AGENTS_SENTINEL'),
                           ('improvement.yaml', 'SECRET_POLICY_SENTINEL'),
                           ('experiments/0001.md', 'SECRET_OLD_REPORT_SENTINEL')]:
        assert (project / path).read_text() == original
    assert outside.read_text() == 'SECRET_OUTSIDE_SENTINEL'
    assert 'SECRET_' not in json.dumps(requests) + result.stdout.decode(errors='replace')
