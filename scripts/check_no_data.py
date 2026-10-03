"""Fail on tracked research data, local configuration, or secret environment files."""

import subprocess
import sys


def forbidden(path: str) -> bool:
    lower = path.lower().replace('\\', '/')
    parts = lower.split('/')
    return (lower.endswith(('.db', '.sqlite', '.sqlite3', '.local'))
            or any(suffix in parts[-1] for suffix in
                   ('.db-', '.db.', '.sqlite-', '.sqlite.', '.sqlite3-', '.sqlite3.'))
            or 'vault' in parts or lower.startswith('demo/data/')
            or (parts[-1].startswith('.env') and parts[-1] != '.env.example')
            or parts[-1] in ('owner-needed.md', 'owner-answers.md'))


if __name__ == '__main__':
    files = subprocess.check_output(['git', 'ls-files', '-z']).decode().split('\0')
    bad = [path for path in files if forbidden(path)]
    if bad:
        print('Tracked local/research data forbidden: ' + ', '.join(bad))
        sys.exit(1)
    print('No tracked research data or local secret files.')
