"""Double-click launcher: app window lifecycle, port reuse and plain-language failures."""

import http.server
import socket
import threading
import urllib.request

import pytest

from qualia import launcher


def free_port():
    with socket.socket() as probe:
        probe.bind(('127.0.0.1', 0))
        return probe.getsockname()[1]


@pytest.fixture
def quiet(monkeypatch, tmp_path):
    monkeypatch.setenv('QUALIA_HOME', str(tmp_path / 'home'))
    monkeypatch.setattr(launcher, 'find_browser', lambda: 'edge.exe')
    messages = []
    monkeypatch.setattr(launcher, '_notify', messages.append)
    return messages


def serve(body):
    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args):
            pass

    server = http.server.HTTPServer(('127.0.0.1', 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server


def test_closing_the_app_window_stops_the_server(quiet, monkeypatch, tmp_path):
    port, seen = free_port(), {}

    class Browser:
        def __init__(self, command):
            seen['command'] = command

        def wait(self):
            # While the "window" is open, the real local server answers with its launch token.
            with urllib.request.urlopen(f'http://127.0.0.1:{port}/', timeout=5) as response:
                seen['page'] = response.read()

    monkeypatch.setattr(launcher.subprocess, 'Popen', Browser)
    runner = threading.Thread(target=launcher.main, args=(port,))
    runner.start()
    runner.join(timeout=60)
    assert not runner.is_alive(), 'server kept running after the window closed'
    assert b'qualia-token' in seen['page'] and quiet == []
    command = seen['command']
    assert command[0] == 'edge.exe' and f'--app=http://127.0.0.1:{port}' in command
    assert f'--user-data-dir={tmp_path / "home" / ".app-browser"}' in command
    assert '--no-first-run' in command


def test_second_launch_only_opens_another_window(quiet, monkeypatch):
    running = serve(b'<html><head><meta name="qualia-token" content="x"></head></html>')
    opened = []
    monkeypatch.setattr(launcher.subprocess, 'Popen', opened.append)
    try:
        launcher.main(running.server_port)
    finally:
        running.shutdown()
    assert len(opened) == 1 and quiet == []


def test_foreign_program_on_the_port_is_explained(quiet, monkeypatch):
    other = serve(b'<html>someone else</html>')
    monkeypatch.setattr(launcher.subprocess, 'Popen', lambda command: pytest.fail('opened a window'))
    try:
        launcher.main(other.server_port)
    finally:
        other.shutdown()
    assert len(quiet) == 1 and 'used by another program' in quiet[0]


def test_missing_browser_is_explained(quiet, monkeypatch):
    monkeypatch.setattr(launcher, 'find_browser', lambda: None)
    launcher.main(free_port())
    assert len(quiet) == 1 and 'Microsoft Edge or Google Chrome' in quiet[0]


def test_find_browser_prefers_installed_edge(monkeypatch, tmp_path):
    edge = tmp_path / 'Microsoft/Edge/Application/msedge.exe'
    edge.parent.mkdir(parents=True)
    edge.write_text('')
    monkeypatch.setenv('ProgramFiles(x86)', str(tmp_path))
    assert launcher.find_browser() == str(edge)
