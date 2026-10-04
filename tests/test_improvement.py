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


def test_zero_invalid_dirty_and_unavailable_runs_launch_nothing(project):
    assert improve(project, budget=0, operator=lambda *args: pytest.fail('operator called')) == []
    with pytest.raises(ValueError, match='budget'):
        improve(project, budget=-1)
    with pytest.raises(ValueError, match='unavailable'):
        improve(project, agent='codex')
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
