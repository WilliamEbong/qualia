"""Double-click entry point: Qualia in its own browser app window; closing the window stops it."""

import os
import shutil
import subprocess
import sys
import threading
import time
import urllib.request
from pathlib import Path

# A windowless (GUI-script) launch has no console, so messages need a dialog instead of stderr.
_CONSOLE = sys.stderr is not None
_PROGRAMS = ('Microsoft/Edge/Application/msedge.exe', 'Google/Chrome/Application/chrome.exe')
_MAC_APPS = ('/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge',
             '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome')
_COMMANDS = ('msedge', 'microsoft-edge', 'google-chrome', 'chromium', 'chromium-browser')


def find_browser():
    """Edge or Chrome, the browsers whose app mode gives Qualia a window without tabs."""
    roots = [os.environ.get(name) for name in ('ProgramFiles(x86)', 'ProgramFiles', 'LOCALAPPDATA')]
    paths = [Path(root, program) for root in roots if root for program in _PROGRAMS]
    for path in [*paths, *map(Path, _MAC_APPS)]:
        if path.is_file():
            return str(path)
    return next((found for name in _COMMANDS if (found := shutil.which(name))), None)


def _probe(port):
    """'qualia' if Qualia already serves the port, 'other' if another program does, None if free."""
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    try:
        with opener.open(f'http://127.0.0.1:{port}/', timeout=2) as response:
            return 'qualia' if b'qualia-token' in response.read(65536) else 'other'
    except urllib.request.HTTPError:
        return 'other'
    except OSError:
        return None


def _notify(message):
    if os.name == 'nt' and not _CONSOLE:
        import ctypes

        ctypes.windll.user32.MessageBoxW(None, message, 'Qualia', 0x40)
    else:
        print(message, file=sys.stderr)


def _window(server, command):
    deadline = time.monotonic() + 60
    while not server.started:
        if server.should_exit or time.monotonic() > deadline:
            return
        time.sleep(0.05)
    try:
        subprocess.Popen(command).wait()
    finally:
        server.should_exit = True


def main(port=None):
    try:
        _run(port)
    except Exception as error:  # a windowless launch must never fail silently
        _notify(f'Qualia could not start: {error}')
        if _CONSOLE:
            raise


def _run(port):
    from qualia.workspace import home_dir, local_setting

    home = home_dir()
    if not _CONSOLE:
        # Keep a log for troubleshooting a windowless launch.
        home.mkdir(parents=True, exist_ok=True)
        sys.stdout = sys.stderr = open(home / 'qualia-app.log', 'a', encoding='utf-8')
    try:
        port = int(port or local_setting('QUALIA_PORT') or 8765)
    except ValueError:
        return _notify('QUALIA_PORT in Qualia\'s .env file must be a number.')
    browser = find_browser()
    if browser is None:
        return _notify('Qualia opens in Microsoft Edge or Google Chrome, but neither was found. '
                       'Install one of them, or run "uv run qualia open" to use your default browser.')
    url = f'http://127.0.0.1:{port}'
    command = [browser, f'--app={url}', f'--user-data-dir={home / ".app-browser"}', '--no-first-run',
               '--no-default-browser-check', '--window-size=1280,860']
    state = _probe(port)
    if state == 'qualia':
        subprocess.Popen(command)
        return
    if state == 'other':
        return _notify(f'Port {port} is used by another program. Close that program, or set '
                       'QUALIA_PORT in Qualia\'s .env file to another number such as 8766.')
    import uvicorn

    from qualia.server.app import create_app

    server = uvicorn.Server(uvicorn.Config(create_app(), host='127.0.0.1', port=port, access_log=False))
    threading.Thread(target=_window, args=(server, command), daemon=True).start()
    server.run()
    if not server.started:
        _notify(f'Qualia could not start on port {port}. See {home / "qualia-app.log"} for details.')
