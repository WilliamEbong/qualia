"""Untrusted proposals never select paths or policy beyond the captured inventory."""

import copy
import hashlib
import json
import os
import stat
from pathlib import Path
from types import SimpleNamespace

import pytest

from qualia.ai.backends.process import BackendError
from qualia.improve import proposal
from qualia.workspace import ROUTING


@pytest.fixture
def project(tmp_path):
    root = tmp_path / 'project'
    (root / 'config/prompts').mkdir(parents=True)
    (root / 'config/routing.yaml').write_text(json.dumps(ROUTING), encoding='utf-8')
    (root / 'config/segmentation.yaml').write_text('{"method":"paragraph"}', encoding='utf-8')
    (root / 'config/prompts/classify.txt').write_text('Original prompt.', encoding='utf-8')
    return root


def result(context, path='config/prompts/classify.txt', content='Improved prompt.'):
    item = next(item for item in json.loads(context.prompt)['files'] if item['path'] == path)
    return {'hypothesis': 'Test a clearer instruction.',
            'edits': [{'path': path, 'original_sha256': item['original_sha256'], 'content': content}],
            'input_tokens': 10, 'output_tokens': 5, 'cli_version': 'synthetic'}


def contents(project):
    return {p.relative_to(project).as_posix(): p.read_bytes()
            for p in project.rglob('*') if p.is_file()}


def test_inventory_only_supplies_permitted_files_and_applies_exact_text(project):
    for name in ['.env', 'project.db', 'IMPROVEMENT.md', 'config/prompts/.env.md',
                 'config/prompts/auth.txt', 'config/prompts/project.db.md',
                 'config/prompts/credentials.md', 'config/prompts/script.py']:
        (project / name).write_text('PRIVATE_SENTINEL', encoding='utf-8')
    context = proposal.prepare_proposal(project, 'Trusted task.')
    assert 'PRIVATE_SENTINEL' not in context.prompt
    assert len(json.loads(context.prompt)['files']) == 3
    original = contents(project)
    response = result(context, content='Unicode replacement \u03b1\n')
    proposal.apply_proposal(project, context, response)
    original['config/prompts/classify.txt'] = 'Unicode replacement \u03b1\n'.encode()
    assert contents(project) == original


def test_protected_names_never_opened_or_supplied(project, monkeypatch):
    names = ['codebook.md', 'codebook.json.md', 'METHODOLOGY.md', 'IMPROVEMENT.md',
             'project.db-wal.txt', 'benchmark.md', 'CLAUDE.md', 'AGENTS.md']
    paths = {project / 'config/prompts' / name for name in names}
    for path in paths:
        path.write_text('PROTECTED_SENTINEL')
    original = Path.open
    def guarded(path, *args, **kwargs):
        assert path not in paths, 'protected input was opened'
        return original(path, *args, **kwargs)
    monkeypatch.setattr(Path, 'open', guarded)
    assert 'PROTECTED_SENTINEL' not in proposal.prepare_proposal(project, 'Task').prompt


@pytest.mark.parametrize('path', ['../outside.txt', '/outside.txt', 'C:/outside.txt',
    r'C:\outside.txt', r'\\host\share\file', 'config/prompts/classify.txt::$DATA',
    'config/prompts/../routing.yaml', 'config//prompts/classify.txt',
    'CONFIG/PROMPTS/CLASSIFY.TXT', 'config/prompts/classify.txt.',
    'config/prompts/classify.txt ', 'config/prompts/new.txt', 'METHODOLOGY.md',
    '.env', 'project.db', 'config/prompts/.env.md'])
def test_exact_inventory_membership_rejects_path_aliases_before_any_write(project, path):
    context = proposal.prepare_proposal(project, 'Task')
    raw = result(context)
    raw['edits'].append({**raw['edits'][0], 'path': path})
    before = contents(project)
    with pytest.raises(BackendError, match='proposal'):
        proposal.apply_proposal(project, context, raw)
    assert contents(project) == before


@pytest.mark.parametrize('attack', ['duplicate', 'hash', 'extra', 'missing_usage', 'too_many',
                                   'large_utf8', 'aggregate', 'invalid_config', 'budget',
                                   'segmentation', 'surrogate'])
def test_entire_proposal_validates_before_first_write(project, attack):
    if attack == 'aggregate':
        for index in range(3):
            (project / f'config/prompts/p{index}.txt').write_text('Small')
    context = proposal.prepare_proposal(project, 'Task')
    raw = result(context)
    if attack == 'duplicate':
        raw['edits'] *= 2
    elif attack == 'hash':
        raw['edits'][0]['original_sha256'] = '0' * 64
    elif attack == 'extra':
        raw['command'] = 'do not run'
    elif attack == 'missing_usage':
        del raw['input_tokens']
    elif attack == 'too_many':
        raw['edits'] *= 17
    elif attack == 'large_utf8':
        raw['edits'][0]['content'] = '\u03b1' * 40000
    elif attack == 'aggregate':
        raw['edits'] = [result(context, f'config/prompts/p{i}.txt', 'x' * 50000)['edits'][0]
                        for i in range(3)]
    elif attack == 'surrogate':
        raw['edits'][0]['content'] = '\ud800'
    else:
        path = 'config/segmentation.yaml' if attack == 'segmentation' else 'config/routing.yaml'
        text = {'invalid_config': '{', 'budget': json.dumps({**ROUTING, 'daily_calls': 9999}),
                'segmentation': '{"method":"execute"}'}[attack]
        raw['edits'] += result(context, path, text)['edits']
    before = contents(project)
    with pytest.raises(BackendError, match='proposal'):
        proposal.apply_proposal(project, context, raw)
    assert contents(project) == before


@pytest.mark.parametrize('mutation', ['content', 'replace', 'hardlink', 'other_input'])
def test_stale_file_identity_or_any_changed_input_rejects(project, tmp_path, mutation):
    context = proposal.prepare_proposal(project, 'Task')
    path = project / 'config/prompts/classify.txt'
    if mutation == 'content':
        path.write_text('Different', encoding='utf-8')
    elif mutation == 'replace':
        replacement = path.with_suffix('.next')
        replacement.write_bytes(path.read_bytes())
        os.replace(replacement, path)
    elif mutation == 'hardlink':
        os.link(path, tmp_path / 'outside.txt')
    else:
        (project / 'config/segmentation.yaml').write_text('{"method":"sentence"}')
    before = contents(project)
    with pytest.raises(BackendError, match='proposal'):
        proposal.apply_proposal(project, context, result(context))
    assert contents(project) == before


def test_hardlinked_input_rejected_before_read(project, tmp_path, monkeypatch):
    path = project / 'config/prompts/classify.txt'
    path.unlink()
    outside = tmp_path / 'outside.txt'
    outside.write_text('DO_NOT_READ')
    os.link(outside, path)
    original = Path.open
    def guarded(candidate, *args, **kwargs):
        assert candidate != path, 'hardlink was opened'
        return original(candidate, *args, **kwargs)
    monkeypatch.setattr(Path, 'open', guarded)
    with pytest.raises(BackendError, match='proposal'):
        proposal.prepare_proposal(project, 'Task')
    assert outside.read_text() == 'DO_NOT_READ'


def test_reparse_directory_rejected_without_enumeration(project, monkeypatch):
    target = project / 'config/prompts'
    original_stat, original_iter = Path.lstat, Path.iterdir
    def lstat(path, *args, **kwargs):
        if path == target:
            return SimpleNamespace(st_mode=stat.S_IFDIR, st_file_attributes=stat.FILE_ATTRIBUTE_REPARSE_POINT)
        return original_stat(path, *args, **kwargs)
    def iterdir(path):
        assert path != target, 'reparse directory enumerated'
        return original_iter(path)
    monkeypatch.setattr(Path, 'lstat', lstat)
    monkeypatch.setattr(Path, 'iterdir', iterdir)
    with pytest.raises(BackendError, match='proposal'):
        proposal.prepare_proposal(project, 'Task')


@pytest.mark.parametrize('attack', ['file', 'count', 'total', 'task', 'binary'])
def test_input_limits_fail_closed(project, attack):
    directory = project / 'config/prompts'
    if attack == 'file':
        (directory / 'classify.txt').write_text('x' * 65537)
    elif attack == 'count':
        for index in range(65):
            (directory / f'p{index}.txt').write_text('small')
    elif attack == 'total':
        for index in range(3):
            (directory / f'p{index}.txt').write_text('x' * 50000)
    elif attack == 'binary':
        (directory / 'classify.txt').write_bytes(b'\xff')
    with pytest.raises(BackendError, match='proposal'):
        proposal.prepare_proposal(project, 'x' * 140000 if attack == 'task' else 'Task')


def test_payload_hash_covers_exact_original_content(project):
    context = proposal.prepare_proposal(project, 'Task')
    item = json.loads(context.prompt)['files'][0]
    assert item['original_sha256'] == hashlib.sha256((project / item['path']).read_bytes()).hexdigest()
    raw = result(context)
    copy_raw = copy.deepcopy(raw)
    proposal.apply_proposal(project, context, raw)
    assert raw == copy_raw
