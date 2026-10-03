import pytest

from qualia.store.db import Store
from qualia.workspace import init_project, operation_lock


def test_operation_excludes_existing_and_new_writers_and_restores_backup(tmp_path):
    project = init_project('study', tmp_path / 'home')
    with Store(project / 'project.db') as other:
        other.save_code({'name': 'Original'})
        with operation_lock(project) as identity:
            with pytest.raises(ValueError, match='active or interrupted'):
                Store(project / 'project.db')
            with pytest.raises(ValueError, match='active or interrupted'):
                other.save_code({'name': 'Concurrent'})
            assert not other.connection.in_transaction
            with Store(project / 'project.db', operation_id=identity) as owner:
                before = owner.fingerprint()
                backup = tmp_path / 'trusted-backup.db'
                owner.backup_to(backup)
                owner.save_code({'name': 'Candidate'})
                assert owner.fingerprint() != before
                owner.restore_from(backup)
                assert owner.fingerprint() == before
                assert [row['name'] for row in owner.rows('SELECT * FROM codes')] == ['Original']
        other.save_code({'name': 'After'})
        assert len(other.rows('SELECT * FROM codes')) == 2


def test_nested_operation_and_abandoned_lock_fail_closed(tmp_path):
    project = init_project('study', tmp_path / 'home')
    with operation_lock(project):
        with pytest.raises(ValueError, match='active or interrupted'):
            with operation_lock(project):
                pass
    (project / '.qualia-operation.lock').write_text('abandoned', encoding='utf-8')
    with pytest.raises(ValueError, match='active or interrupted'):
        Store(project / 'project.db')


def test_forged_owner_and_deleted_lock_never_allow_restoration(tmp_path):
    project = init_project('study', tmp_path / 'home')
    with pytest.raises(ValueError, match='lock is missing'):
        Store(project / 'project.db', operation_id='forged')
    with operation_lock(project) as identity:
        with Store(project / 'project.db', operation_id=identity) as db:
            backup = tmp_path / 'backup.db'
            db.backup_to(backup)
            (project / '.qualia-operation.lock').unlink()
            with pytest.raises(ValueError, match='lock is missing'):
                db.restore_from(backup)


def test_pending_recovery_blocks_ordinary_store_even_without_lock(tmp_path):
    project = init_project('study', tmp_path / 'home')
    journal = tmp_path / 'home/recovery/study/pending.json'
    journal.parent.mkdir(parents=True)
    journal.write_text('{}', encoding='utf-8')
    with pytest.raises(ValueError, match='requiring recovery'):
        Store(project / 'project.db')


def test_confirmation_can_bypass_cache_for_an_independent_dispatch(tmp_path):
    from qualia.evaluation import evaluate_project
    from qualia.io.benchmarks import import_benchmark

    project = init_project('study', tmp_path / 'home')
    with Store(project / 'project.db') as db:
        code = db.save_code({'name': 'Example'})
        version = db.freeze_codebook()['id']
        import_benchmark(project, [{'segment_id': 'a', 'text': 'Example.', 'codes': [code],
                                    'transcript_id': 't'}], 'validation', version, [code])
        first = evaluate_project(db, project, backend='fake')
        confirmation = evaluate_project(db, project, backend='fake', use_cache=False)
        assert first['metrics']['calls'] == confirmation['metrics']['calls'] == 1
        assert confirmation['metrics']['cache_hits'] == 0
        assert first['metrics']['identity']['run_id'] != confirmation['metrics']['identity']['run_id']
