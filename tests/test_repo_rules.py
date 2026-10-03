import ast
from pathlib import Path

import pytest

from scripts.check_no_data import forbidden


@pytest.mark.parametrize('path', ['project.db', 'project.db-wal', 'project.db.v1.bak',
                                 'vault/test.jsonl', 'demo/data/sample.csv', '.env',
                                 '.env.production', 'scripts/ntfy-topic.local'])
def test_data_guard_rejects_private_artifacts(path):
    assert forbidden(path)


def test_data_guard_allows_code_and_template():
    assert not forbidden('.env.example')
    assert not forbidden('qualia/store/db.py')


def test_core_and_evaluation_remain_sealed():
    root = Path(__file__).resolve().parents[1]
    forbidden_imports = {'sqlite3', 'subprocess', 'httpx', 'fastapi', 'os'}
    for directory in ('core', 'eval'):
        for path in (root / 'qualia' / directory).rglob('*.py'):
            for node in ast.walk(ast.parse(path.read_text(encoding='utf-8'))):
                if isinstance(node, ast.Import):
                    assert not {n.name.split('.')[0] for n in node.names} & forbidden_imports
                elif isinstance(node, ast.ImportFrom):
                    assert (node.module or '').split('.')[0] not in forbidden_imports
