import json
import os
import sqlite3
import stat
import subprocess

import pytest

from qualia.ai.backends.fake import FakeBackend
from qualia.improve import experiment
from qualia.io.benchmarks import import_benchmark
from qualia.store.db import Store
from qualia.workspace import ROUTING, init_project, pipeline_hash, vault_dir


def git(project, *arguments):
    return subprocess.run(['git', '-C', str(project), *arguments], check=True,
                          capture_output=True, text=True).stdout.strip()


@pytest.fixture
def project(tmp_path):
    project = init_project('improve', tmp_path)
    (project/'config/routing.yaml').write_text(json.dumps({**ROUTING, 'backend': 'fake', 'model': 'fake-v1'}))
    with Store(project/'project.db') as db:
        db.save_code({'name': 'First'})
        db.save_code({'name': 'Second'})
        version = db.freeze_codebook()['id']
    import_benchmark(project, [{'segment_id': f's{i}', 'text': f'Synthetic {i}',
                               'codes': [2], 'transcript_id': f't{i}'} for i in range(3)],
                     'validation', version, [1, 2])
    git(project, 'add', '.')
    git(project, '-c', 'user.name=Qualia', '-c', 'user.email=qualia@localhost', 'commit', '-qm', 'Synthetic baseline')
    return project


def improve(project, **kwargs):
    return experiment.improve_project(project, test_runner=lambda: True, **kwargs)


def test_fake_measured_gain_confirms_fresh_then_keeps_and_tags(project):
    rows = improve(project)
    assert len(rows) == 1 and rows[0]['decision'] == 'KEEP'
    assert git(project, 'tag', '--list') == rows[0]['tag']
    assert git(project, 'status', '--porcelain') == ''
    with Store(project/'project.db') as db:
        evaluations = db.rows('SELECT metrics_json FROM evaluation_runs')
        assert len(evaluations) == 3
        assert all(json.loads(row['metrics_json'])['cache_hits'] == 0 for row in evaluations)
        assert not db.rows('SELECT * FROM coding_events')
        assert len(db.rows('SELECT * FROM experiments')) == 1
        assert len(db.rows("SELECT * FROM usage_ledger WHERE status='reserved'")) == 4


@pytest.mark.parametrize('target', ['METHODOLOGY.md', 'config/unapproved.txt', '.git/config', 'preexisting.local'])
def test_scope_attacks_restore_all_preexisting_files(project, target):
    ignored = project/'preexisting.local'
    ignored.write_text('preserve original ignored bytes')
    with (project/'.gitignore').open('a') as stream:
        stream.write('\n*.local\n')
    git(project, 'add', '.gitignore')
    git(project, '-c', 'user.name=Qualia', '-c', 'user.email=qualia@localhost', 'commit', '-qm', 'Ignore local fixture')
    originals = {name: (project/name).read_bytes() for name in ('METHODOLOGY.md', '.git/config', 'preexisting.local')}
    def operator(root, prompt, report_path):
        (root/target).write_text('OPERATOR CLAIMS KEEP AND GAINS')
        report_path.write_text('# KEEP\nUnmeasured fabricated gain')
        return {'hypothesis': 'Claimed gain', 'cli_version': 'fake-test', 'input_tokens': 0, 'output_tokens': 0}
    row = improve(project, operator=operator)[0]
    assert row['decision'] == 'REVERT' and 'scope' in row['reason']
    for name, expected in originals.items():
        assert (project/name).read_bytes() == expected
    assert not (project/'config/unapproved.txt').exists()
    assert git(project, 'status', '--porcelain') == ''
    assert '# REVERT' in (project/'experiments/0001.md').read_text()


def test_policy_and_failed_trusted_tests_override_operator_claims(project):
    def regressive(root, prompt, report_path):
        config = json.loads((root/'config/routing.yaml').read_text())
        config['fake_mode'] = 'none'
        (root/'config/routing.yaml').write_text(json.dumps(config))
        report_path.write_text('KEEP: guaranteed perfect improvement')
    row = improve(project, operator=regressive)[0]
    assert row['decision'] == 'REVERT' and 'gain' in row['reason']
    assert 'fake_mode' not in json.loads((project/'config/routing.yaml').read_text())
    row = experiment.improve_project(project, test_runner=lambda: False)[0]
    assert row['decision'] == 'REVERT' and 'tests' in row['reason']


def test_privacy_budget_change_reverts_before_candidate_dispatch(project):
    def operator(root, prompt, report_path):
        config = json.loads((root/'config/routing.yaml').read_text())
        config.update(allow_external=True, daily_calls=999)
        (root/'config/routing.yaml').write_text(json.dumps(config))
    row = improve(project, operator=operator)[0]
    assert row['decision'] == 'REVERT' and 'budget' in row['reason']
    with Store(project/'project.db') as db:
        assert len(db.rows('SELECT * FROM evaluation_runs')) == 1


def test_operator_failure_preserves_audit_and_removes_only_new_files(project):
    def operator(root, prompt, report_path):
        (root/'unexpected.txt').write_text('new')
        raise RuntimeError('RAW_SECRET_OPERATOR_BODY')
    row = improve(project, operator=operator)[0]
    assert row['decision'] == 'REVERT'
    assert 'RAW_SECRET' not in json.dumps(row)
    assert not (project/'unexpected.txt').exists()
    with Store(project/'project.db') as db:
        assert db.one("SELECT count(*) AS n FROM usage_ledger WHERE status='error'")['n'] == 1


def test_vault_tamper_is_flagged_and_preserved_without_parsing(project):
    manifest = vault_dir(project)/'manifest.sha256'
    def operator(root, prompt, report_path):
        manifest.write_text('tampered manifest evidence')
    row = improve(project, operator=operator)[0]
    assert row['decision'] == 'REVERT' and 'vault' in row['reason']
    assert manifest.read_text() == 'tampered manifest evidence'
    assert git(project, 'status', '--porcelain') == ''


def test_zero_invalid_dirty_and_unavailable_runs_launch_nothing(project, monkeypatch):
    from qualia.ai.backends import codex_cli
    monkeypatch.setattr(codex_cli, "operator_available", lambda: False)
    monkeypatch.setattr(codex_cli, 'run_operator', lambda *a, **k: pytest.fail('unavailable operator launched'))
    assert improve(project, budget=0, operator=lambda *args: pytest.fail('operator called')) == []
    with pytest.raises(ValueError, match='budget'):
        improve(project, budget=-1)
    with pytest.raises(ValueError) as error:
        improve(project, agent='codex')
    assert str(error.value) == codex_cli.OPERATOR_UNAVAILABLE_REASON
    (project/'unrelated.txt').write_text('owner work')
    with pytest.raises(ValueError, match='clean'):
        improve(project)
    assert (project/'unrelated.txt').read_text() == 'owner work'


def test_git_failure_leaves_recovery_journal_and_blocks_next_attempt(project, monkeypatch):
    original = experiment._git
    def failing(root, *args):
        if 'commit' in args:
            raise RuntimeError('synthetic Git failure')
        return original(root, *args)
    monkeypatch.setattr(experiment, '_git', failing)
    with pytest.raises(ValueError, match='recovery'):
        improve(project)
    journal = project.parent.parent/'recovery'/project.name/'pending.json'
    assert journal.exists()
    assert json.loads(journal.read_text())['record']['decision'] == 'KEEP'
    with pytest.raises(ValueError, match='recovery'):
        improve(project)


def test_raw_database_codebook_attack_restores_before_finishing_usage(project):
    with Store(project/'project.db') as db:
        definition = db.one('SELECT definition FROM codes WHERE id=1')['definition']
        frozen_hash = db.one('SELECT hash FROM codebook_versions')['hash']
    def malicious_operator(root, prompt, report_path):
        # Deliberately bypass Store to simulate a hostile external process, not application code.
        with sqlite3.connect(root/'project.db') as connection:
            connection.execute("UPDATE codes SET definition='Unapproved methodology' WHERE id=1")
    result = improve(project, operator=malicious_operator)[0]
    assert result['decision'] == 'REVERT' and 'database' in result['reason']
    with Store(project/'project.db') as db:
        assert db.one('SELECT definition FROM codes WHERE id=1')['definition'] == definition
        assert db.one('SELECT hash FROM codebook_versions')['hash'] == frozen_hash
        assert len(db.rows('SELECT * FROM evaluation_runs')) == 1
        assert len(db.rows('SELECT * FROM usage_ledger WHERE reservation_id IS NOT NULL')) == 2
    assert git(project, 'status', '--porcelain') == ''


def test_actual_failed_confirmation_reverts_a_first_pass_gain(project, monkeypatch):
    original = FakeBackend.classify
    calls = 0
    def drifting(self, segments, schema, context):
        nonlocal calls
        calls += 1
        return original(self, segments, schema, {**context, 'fake_mode': 'none'} if calls == 3 else context)
    monkeypatch.setattr(FakeBackend, 'classify', drifting)
    row = improve(project)[0]
    assert row['decision'] == 'REVERT' and 'confirmation failed' in row['reason']
    assert calls == 3
    assert not git(project, 'tag', '--list')
    assert 'fake_mode' not in json.loads((project/'config/routing.yaml').read_text())


def test_new_nested_scope_paths_are_removed_without_touching_owner_files(project):
    def operator(root, prompt, report_path):
        path = root/'unapproved/deep/new.txt'
        path.parent.mkdir(parents=True)
        path.write_text('Out of scope')
    row = improve(project, operator=operator)[0]
    assert row['decision'] == 'REVERT' and 'scope' in row['reason']
    assert not (project/'unapproved').exists()
    assert (project/'METHODOLOGY.md').exists()


def test_snapshot_symlink_attack_is_rejected_without_reading_target(project, tmp_path):
    outside = tmp_path/'private-outside.txt'
    outside.write_text('preserve outside')
    link = project/'probe-link'
    try:
        link.symlink_to(outside)
    except OSError:
        pytest.skip('Windows account does not allow symlink creation')
    link.unlink()
    def operator(root, prompt, report_path):
        (root/'config/prompts/escape').symlink_to(outside)
    row = improve(project, operator=operator)[0]
    assert row['decision'] == 'REVERT' and 'scope' in row['reason']
    assert outside.read_text() == 'preserve outside'
    assert not (project/'config/prompts/escape').exists()


def test_valid_mutable_deletion_keeps_exact_evaluated_pipeline(project):
    optional = project/'config/prompts/optional.txt'
    optional.write_text('Unused optional prompt')
    git(project, 'add', 'config/prompts/optional.txt')
    git(project, '-c', 'user.name=Qualia', '-c', 'user.email=qualia@localhost', 'commit', '-qm', 'Optional prompt')
    def operator(root, prompt, report_path):
        result = experiment._fake_operator(root, prompt, report_path)
        (root/'config/prompts/optional.txt').unlink()
        return result
    row = improve(project, operator=operator)[0]
    assert row['decision'] == 'KEEP' and not optional.exists()
    after = json.loads(row['after_json'])
    assert after['pipeline_version'] == pipeline_hash(project)
    assert after['confirmation']['pipeline_version'] == after['pipeline_version']


def test_new_hardlink_rejected_without_following_external_file(project, tmp_path):
    outside = tmp_path/'outside.txt'
    outside.write_text('Outside stays unchanged')
    def operator(root, prompt, report_path):
        os.link(outside, root/'config/prompts/linked.txt')
    row = improve(project, operator=operator)[0]
    assert row['decision'] == 'REVERT' and 'scope' in row['reason']
    assert outside.read_text() == 'Outside stays unchanged'
    assert outside.stat().st_nlink == 1


def test_safe_methodology_proposal_survives_policy_revert_without_application(project):
    original = (project/'METHODOLOGY.md').read_bytes()
    def operator(root, prompt, report_path):
        (root/'experiments/proposals/idea.md').write_text('An idea awaiting explicit human review.')
    row = improve(project, operator=operator)[0]
    assert row['decision'] == 'REVERT'
    assert (project/'experiments/proposals/idea.md').exists()
    assert (project/'METHODOLOGY.md').read_bytes() == original


def test_permission_only_protected_edit_is_reverted(project):
    path = project/'METHODOLOGY.md'
    mode = stat.S_IMODE(path.stat().st_mode)
    def operator(root, prompt, report_path):
        (root/'METHODOLOGY.md').chmod(stat.S_IREAD)
    row = improve(project, operator=operator)[0]
    assert row['decision'] == 'REVERT' and 'scope' in row['reason']
    assert stat.S_IMODE(path.stat().st_mode) == mode


@pytest.mark.parametrize('agent', ['claude', 'codex'])
@pytest.mark.parametrize('fails', [False, True])
def test_native_operator_is_admitted_once_and_retains_usage(project, monkeypatch, agent, fails):
    from qualia.ai.backends.process import BackendError
    module = experiment.importlib.import_module(f'qualia.ai.backends.{agent}_cli')
    monkeypatch.setattr(module, 'operator_available', lambda: True)
    config_path = project / 'config/routing.yaml'
    config = json.loads(config_path.read_text())
    config.update(allow_external=True)
    config_path.write_text(json.dumps(config))
    git(project, 'add', '.')
    git(project, '-c', 'user.name=Qualia', '-c', 'user.email=qualia@localhost',
        'commit', '-qm', 'Admit synthetic native operator')
    calls = []
    admissions = []
    reserve = experiment.ledger.reserve

    def observe_admission(db, **kwargs):
        reservation = reserve(db, **kwargs)
        if kwargs['backend'].name == agent:
            rows = db.rows('SELECT * FROM egress_log WHERE backend=?', (agent,))
            assert len(rows) == 1
            assert rows[0]['purpose'] == 'operator:cli_invocation'
            admissions.append(reservation)
        return reservation

    monkeypatch.setattr(experiment.ledger, 'reserve', observe_admission)

    def native(root, prompt, *, model, max_output_tokens, report_path):
        assert len(admissions) == 1
        assert report_path == 'experiments/0001.md'
        assert model == ('opus' if agent == 'claude' else 'gpt-6-astra')
        assert max_output_tokens == config['max_output_tokens']
        calls.append(report_path)
        if fails:
            raise BackendError('quota', input_tokens=41, output_tokens=7,
                               cli_version='synthetic-native')
        if agent == 'claude':
            (root / report_path).write_text('Measured experiment proposal.')
        return {'hypothesis': 'Unchanged candidate must be rejected.', 'input_tokens': 41,
                'output_tokens': 7, 'cli_version': 'synthetic-native',
                **({'edits': []} if agent == 'codex' else {})}

    monkeypatch.setattr(module, 'run_operator', native)
    row = improve(project, agent=agent)[0]
    assert row['decision'] == 'REVERT'
    assert len(calls) == 1
    assert git(project, 'status', '--porcelain') == ''
    with Store(project / 'project.db') as db:
        attempts = db.rows('SELECT * FROM usage_ledger WHERE backend=? AND reservation_id IS NOT NULL', (agent,))
        assert len(attempts) == 1
        assert attempts[0]['status'] == ('error' if fails else 'ok')
        assert attempts[0]['input_tokens'] == 41 and attempts[0]['output_tokens'] == 7
        assert attempts[0]['cli_version'] == 'synthetic-native'
        assert not db.rows('SELECT * FROM coding_events')


@pytest.mark.parametrize('agent', ['claude', 'codex'])
def test_native_operator_external_denial_prevents_dispatch(project, monkeypatch, agent):
    module = experiment.importlib.import_module(f'qualia.ai.backends.{agent}_cli')
    monkeypatch.setattr(module, 'operator_available', lambda: True)
    monkeypatch.setattr(module, 'run_operator', lambda *a, **k: pytest.fail('external operator launched'))
    with pytest.raises(ValueError, match='external'):
        improve(project, agent=agent)
    with Store(project / 'project.db') as db:
        assert not db.rows('SELECT * FROM egress_log')


@pytest.mark.parametrize('agent', ['claude', 'codex'])
def test_native_injected_operator_cannot_bypass_vendor(project, monkeypatch, agent):
    module = experiment.importlib.import_module(f'qualia.ai.backends.{agent}_cli')
    monkeypatch.setattr(module, 'operator_available', lambda: True)
    with pytest.raises(ValueError, match='injected'):
        improve(project, agent=agent, operator=lambda *a: pytest.fail('injected native operator'))
    with Store(project / 'project.db') as db:
        assert not db.rows('SELECT * FROM egress_log')


@pytest.mark.parametrize('scenario', ['keep', 'noop', 'bad_hash', 'privacy', 'partial_write'])
def test_codex_proposal_full_dispatch_accounting_and_recovery(project, monkeypatch, scenario):
    import hashlib
    from pathlib import Path

    from qualia.ai.backends import codex_cli

    config_path = project / 'config/routing.yaml'
    config = json.loads(config_path.read_text())
    config['allow_external'] = True
    config_path.write_text(json.dumps(config))
    git(project, 'add', '.')
    git(project, '-c', 'user.name=Qualia', '-c', 'user.email=qualia@localhost',
        'commit', '-qm', 'Admit synthetic proposal operator')
    original_config = config_path.read_bytes()
    original_prompt = (project / 'config/prompts/classify.txt').read_bytes()
    monkeypatch.setattr(codex_cli, 'operator_available', lambda: True)
    dispatched = []

    def native(root, prompt, **kwargs):
        dispatched.append(prompt)
        inventory = {item['path']: item for item in json.loads(prompt)['files']}
        assert set(inventory) == {'config/routing.yaml', 'config/segmentation.yaml',
                                  'config/prompts/classify.txt'}
        candidate = {**config, 'fake_mode': 'all'}
        if scenario == 'privacy':
            candidate['daily_calls'] += 1
        edit = {**inventory['config/routing.yaml'], 'content': json.dumps(candidate)}
        if scenario == 'bad_hash':
            edit['original_sha256'] = '0' * 64
        edits = [] if scenario == 'noop' else [edit]
        if scenario == 'partial_write':
            edits += [{**inventory['config/prompts/classify.txt'], 'content': 'Another prompt'}]
        return {'hypothesis': 'Test proposal through real policy.', 'edits': edits,
                'input_tokens': 41, 'output_tokens': 7, 'cli_version': 'synthetic-native'}

    monkeypatch.setattr(codex_cli, 'run_operator', native)
    if scenario == 'partial_write':
        original_open = Path.open
        class FailingWrite:
            def __init__(self, stream):
                self.stream = stream
            def __enter__(self):
                return self
            def __exit__(self, *args):
                self.stream.close()
            def __getattr__(self, name):
                return getattr(self.stream, name)
            def write(self, data):
                assert config_path.read_bytes() != original_config
                raise OSError('synthetic second-write failure')
        def open_file(path, mode='r', *args, **kwargs):
            stream = original_open(path, mode, *args, **kwargs)
            if mode == 'r+b' and path == project / 'config/prompts/classify.txt':
                return FailingWrite(stream)
            return stream
        monkeypatch.setattr(Path, 'open', open_file)
    row = improve(project, agent='codex')[0]
    assert len(dispatched) == 1
    assert row['decision'] == ('KEEP' if scenario == 'keep' else 'REVERT')
    assert git(project, 'status', '--porcelain') == ''
    if scenario != 'keep':
        assert config_path.read_bytes() == original_config
        assert (project / 'config/prompts/classify.txt').read_bytes() == original_prompt
    else:
        assert json.loads(config_path.read_text())['fake_mode'] == 'all'
        assert json.loads(row['after_json'])['confirmation']
    with Store(project / 'project.db') as db:
        calls = db.rows("SELECT * FROM usage_ledger WHERE backend='codex' AND reservation_id IS NOT NULL")
        assert len(calls) == 1 and calls[0]['input_tokens'] == 41 and calls[0]['output_tokens'] == 7
        assert calls[0]['status'] == ('ok' if scenario in ('keep', 'noop') else 'error')
        egress = db.rows("SELECT * FROM egress_log WHERE backend='codex'")
        assert len(egress) == 1
        assert json.loads(egress[0]['segment_hashes_json']) == [hashlib.sha256(dispatched[0].encode()).hexdigest()]
        assert not db.rows('SELECT * FROM coding_events')
