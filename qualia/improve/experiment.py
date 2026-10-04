"""Trusted experiment orchestration, measured decisions and recoverable finalization."""

import hashlib
import importlib
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import time
import uuid
from pathlib import Path

from qualia.ai import ledger
from qualia.ai.backends.fake import FakeBackend
from qualia.ai.backends.process import BackendError
from qualia.ai.router import classify_segments
from qualia.ai.schemas import routing_config
from qualia.eval.metrics import tune_thresholds
from qualia.evaluation import evaluate_project
from qualia.improve.policy import decide
from qualia.improve.proposal import BOUNDS, apply_proposal, prepare_proposal
from qualia.store.db import Store, canonical
from qualia.workspace import (
    REPO,
    check_manifest,
    operation_lock,
    pipeline_hash,
    protected_hashes,
    read_config,
    vault_dir,
)

LOCK = '.qualia-operation.lock'
# ponytail: a fixed deterministic dev sample keeps tuning inside default call budgets; raise if noisy.
TUNING_SEGMENTS = 400
DB_FILES = {'project.db', 'project.db-wal', 'project.db-shm'}


def _git(project, *arguments):
    result = subprocess.run(['git', '--no-optional-locks', '-C', str(project),
                             '-c', f'core.hooksPath={REPO / "qualia/templates/.disabled-hooks"}',
                             '-c', 'core.fsmonitor=false', *arguments],
                            capture_output=True, text=True, timeout=60)
    if result.returncode:
        raise ValueError('experiment Git operation failed')
    return result.stdout.strip()


def _status(project):
    return _git(project, 'status', '--porcelain', '--untracked-files=all', '--', '.', f':(exclude){LOCK}')


def _digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def _signature(path):
    return f'{_digest(path)}:{stat.S_IMODE(path.stat().st_mode):o}'


def _tree(project):
    result = {}
    def visit(directory):
        for path in directory.iterdir():
            name = path.relative_to(project).as_posix()
            if name == LOCK:
                continue
            if path.is_symlink() or path.is_junction():
                result[name] = ('link', '')
            elif path.is_dir():
                result[name] = ('dir', '')
                visit(path)
            elif path.is_file():
                result[name] = ('link', '') if path.stat().st_nlink > 1 else ('file', _signature(path))
            else:
                result[name] = ('unsupported', '')
    visit(project)
    return result


def _snapshot(project, directory, tree):
    for name, (kind, _) in tree.items():
        if name in DB_FILES:
            continue
        path = directory/name
        if kind == 'dir':
            path.mkdir(parents=True, exist_ok=True)
        elif kind == 'file':
            path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(project/name, path)
        else:
            raise ValueError('clean experiment baseline cannot contain links or special files')


def _verify_snapshot(directory, tree):
    for name, (kind, digest) in tree.items():
        if name not in DB_FILES and kind == 'file':
            path = directory/name
            if path.is_symlink() or not path.is_file() or _signature(path) != digest:
                raise ValueError('recovery snapshot integrity mismatch')


def _remove(path):
    if path.is_symlink():
        path.unlink()
    elif path.is_junction() or path.is_dir():
        path.rmdir()
    else:
        path.unlink()


def _restore_tree(project, snapshot, before):
    _verify_snapshot(snapshot, before)
    current = _tree(project)
    # Children first, with no recursion through links or junctions.
    for name in sorted(current, key=lambda name: (name.count('/'), name), reverse=True):
        if name in DB_FILES:
            continue
        if name not in before or current[name][0] != before[name][0]:
            _remove(project/name)
    for name, (kind, _) in sorted(before.items(), key=lambda item: (item[0].count('/'), item[0])):
        if name in DB_FILES:
            continue
        path = project/name
        if path.resolve().parent != (project/Path(name).parent).resolve():
            raise ValueError('unsafe recovery path')
        if kind == 'dir':
            path.mkdir(parents=True, exist_ok=True)
        elif current.get(name) != before[name]:
            path.parent.mkdir(parents=True, exist_ok=True)
            if path.exists():
                path.chmod(stat.S_IREAD | stat.S_IWRITE)
            shutil.copy2(snapshot/name, path)


def _mutable(name):
    return name in ('config/routing.yaml', 'config/segmentation.yaml') or name.startswith('config/prompts/')


def _allowed(name, kind, before, report):
    if kind == 'link' or kind == 'unsupported':
        return False
    if _mutable(name):
        return True
    if name == report and name not in before:
        return kind == 'file'
    return (name.startswith('experiments/proposals/') and name not in before and
            (kind == 'dir' or (kind == 'file' and name.endswith('.md'))))


def _run_tests():
    result = subprocess.run([sys.executable, '-m', 'pytest', '-q', 'tests/test_metrics.py',
                             'tests/test_alpha.py', 'tests/test_repo_rules.py'], cwd=REPO,
                            capture_output=True, timeout=120)
    return result.returncode == 0


def _fake_operator(project, prompt, report_path):
    config = read_config(project)
    config.update(backend='fake', model='fake-v1', fake_mode='all')
    (project/'config/routing.yaml').write_text(canonical(config), encoding='utf-8')
    hypothesis = 'Predict all frozen codes; measure the precision/recall tradeoff against the configured baseline.'
    report_path.write_text(hypothesis, encoding='utf-8')
    return {'hypothesis': hypothesis, 'cli_version': 'fake-operator-v1', 'input_tokens': 0, 'output_tokens': 0}


def _threshold_operator(db, project, backend, model):
    """No-AI operator: fit per-code suggestion thresholds on dev; validation decides KEEP/REVERT."""
    from qualia.io.benchmarks import load_benchmark

    records, metadata = load_benchmark(project, split='dev')
    frozen = db.one('SELECT * FROM codebook_versions WHERE id=?', (metadata['codebook_version_id'],))
    if frozen is None:
        raise ValueError('dev benchmark frozen codebook version is missing')
    codebook = json.loads(frozen['snapshot_json'])
    sample = sorted(records, key=lambda row: hashlib.sha256(row['segment_id'].encode()).hexdigest())
    sample = sample[:TUNING_SEGMENTS]
    config = read_config(project)
    result = classify_segments(db, [{'id': row['segment_id'], 'text': row['text']} for row in sample],
                               codebook, config,
                               prompt=(project/'config/prompts/classify.txt').read_text(encoding='utf-8'),
                               codebook_version_id=frozen['id'], pipeline_version=pipeline_hash(project),
                               backend=backend, model=model, with_candidates=True)
    if result['status'] != 'completed':
        raise ValueError('threshold tuning incomplete: ' + '; '.join(result['errors']))
    current = routing_config(config)['code_thresholds']
    code_ids = [code['id'] for code in codebook if code.get('status', 'active') == 'active']
    tuned = tune_thresholds(sample, result['candidates'], code_ids, current)
    names = {str(code['id']): code.get('name') or str(code['id']) for code in codebook}
    changes = [f"{names.get(code, code)} {f'{current[code]:.2f}' if code in current else 'default'} -> {value:.2f}"
               for code, value in sorted(tuned.items(), key=lambda item: int(item[0])) if current.get(code) != value]
    fitted = f'{len(sample)} of {len(records)} dev segments'
    hypothesis = (f'Per-code suggestion thresholds fitted for maximum F1 on {fitted}: ' + '; '.join(changes)
                  if changes else f'{fitted} suggest no threshold change.')

    def invoke(root, prompt, report_path):
        if changes:
            config = read_config(root)
            config['code_thresholds'] = tuned
            (root/'config/routing.yaml').write_text(canonical(config), encoding='utf-8')
        return {'hypothesis': hypothesis[:2000], 'cli_version': 'thresholds-operator-v1',
                'input_tokens': 0, 'output_tokens': 0}

    return invoke


def _operator(agent, injected):
    if agent == 'fake':
        return injected or _fake_operator, FakeBackend(), 'fake-operator-v1'
    if agent == 'thresholds':
        if injected is not None:
            raise ValueError('injected operators are supported only by the fake agent')
        return None, FakeBackend(), 'thresholds-operator-v1'
    if agent not in ('claude', 'codex'):
        raise ValueError('unknown improvement agent')
    module = importlib.import_module(f'qualia.ai.backends.{agent}_cli')
    if not getattr(module, 'operator_available', lambda: False)():
        raise ValueError(module.OPERATOR_UNAVAILABLE_REASON)
    if injected is not None:
        raise ValueError('injected operators are supported only by the fake agent')
    operator_model = 'opus' if agent == 'claude' else 'gpt-6-astra'
    provider = getattr(module, 'ClaudeCLIBackend' if agent == 'claude' else 'CodexCLIBackend')()

    def invoke(project, prompt, report_path):
        config = routing_config(read_config(project))
        return module.run_operator(project, prompt, model=operator_model,
                                   max_output_tokens=config['max_output_tokens'],
                                   report_path=report_path.relative_to(project).as_posix())

    return invoke, provider, operator_model


def _journal(path, values):
    temporary = path.with_suffix('.next.json')
    temporary.write_text(canonical(values), encoding='utf-8')
    os.replace(temporary, path)


def _clear_snapshot(directory):
    def writable_retry(function, name, error):
        path = Path(name)
        if (not isinstance(error, PermissionError) or path.is_symlink() or
                directory.resolve() not in path.resolve().parents):
            raise error
        path.chmod(stat.S_IREAD | stat.S_IWRITE)
        function(name)
    shutil.rmtree(directory, onexc=writable_retry)


def _report(number, decision, reason, hypothesis, changed, baseline, candidate, confirmation):
    evidence = {'baseline': baseline, 'candidate': candidate, 'confirmation': confirmation}
    return (f'# {decision} · Experiment {number:04d}\n\nReason: {reason}\n\n'
            f'Hypothesis (operator statement): {json.dumps(hypothesis)}\n\n'
            f'Changed paths: {json.dumps(changed)}\n\n'
            '## Measured evidence\n\n```json\n'+json.dumps(evidence, indent=2)+'\n```\n')


def improve_project(project, agent='fake', budget=1, *, operator=None, backend=None, model=None,
                    test_runner=None):
    if type(budget) is not int or budget < 0:
        raise ValueError('experiment budget must be a finite nonnegative integer')
    if budget == 0:
        return []
    project = Path(project).resolve()
    recovery = project.parent.parent/'recovery'/project.name
    journal = recovery/'pending.json'
    if journal.exists():
        raise ValueError('pending experiment recovery requires explicit resolution')
    invoke, provider, operator_model = _operator(agent, operator)
    if _status(project):
        raise ValueError('experiment requires a clean Git baseline')
    if recovery.is_symlink() or recovery.resolve().parent != (project.parent.parent/'recovery').resolve():
        raise ValueError('recovery path escapes workspace')
    recovery.mkdir(parents=True, exist_ok=True)
    results = []
    with operation_lock(project) as operation_id, Store(project/'project.db', operation_id=operation_id) as db:
        for _ in range(budget):
            if _status(project):
                raise ValueError('experiment requires a clean Git baseline')
            tree = _tree(project)
            if any(kind in ('link', 'unsupported') for kind, _ in tree.values()):
                raise ValueError('experiment baseline cannot contain links or special files')
            if not check_manifest(project):
                raise ValueError('protected manifest mismatch before experiment')
            policy = json.loads((project/'improvement.yaml').read_text(encoding='utf-8'))
            if any(policy.get(key) for key in ('challenge', 'challenges', 'challenge_benchmark')):
                raise ValueError('configured challenge benchmark requires a supported trusted evaluator')
            config = routing_config(read_config(project))
            number = db.one('SELECT coalesce(max(id),0)+1 AS n FROM experiments')['n']
            relative_report = f'experiments/{number:04d}.md'
            report_path = project/relative_report
            if report_path.exists():
                raise ValueError('experiment report already exists; recovery is required')
            baseline = evaluate_project(db, project, backend=backend, model=model, use_cache=False)
            coding_count = db.one('SELECT count(*) AS n FROM coding_events')['n']
            prompt = (project/'IMPROVEMENT.md').read_text(encoding='utf-8')
            proposal_context = prepare_proposal(project, prompt) if agent == 'codex' else None
            if agent == 'thresholds':
                # Fitting data is read and recorded before the database pin below.
                invoke = _threshold_operator(db, project, backend, model)
            if proposal_context is not None:
                prompt = proposal_context.prompt
            reservation = ledger.reserve(db, backend=provider, model=operator_model,
                run_id=f'operator-{uuid.uuid4().hex}', segments=[{'text': prompt}], config=config, purpose='operator')
            snapshot_root = Path(tempfile.mkdtemp(prefix=f'exp-{number:04d}-', dir=recovery))
            snapshot = snapshot_root/'project'
            snapshot.mkdir()
            backup = snapshot_root/'database.backup'
            db.backup_to(backup)
            backup_hash = _digest(backup)
            pinned_database = db.fingerprint()
            pinned_protected = protected_hashes(project)
            manifest_hash = _digest(vault_dir(project)/'manifest.sha256')
            tree = _tree(project)
            _snapshot(project, snapshot, tree)
            state = {'project': str(project), 'snapshot': str(snapshot_root), 'number': number,
                     'stage': 'operator', 'database_hash': backup_hash, 'database_fingerprint': pinned_database,
                     'tree': tree, 'baseline': baseline}
            _journal(journal, state)
            try:
                started = time.monotonic()
                raw, operator_error = None, None
                try:
                    raw = invoke(project, prompt, report_path)
                    if proposal_context is not None:
                        apply_proposal(project, proposal_context, raw)
                except BackendError as error:
                    operator_error = error
                except Exception:
                    operator_error = ValueError('operator failed')
                reasons = ['operator failed'] if operator_error else []
                after_tree = _tree(project)
                changed = sorted(name for name in tree.keys() | after_tree.keys() if tree.get(name) != after_tree.get(name))
                if any(not _allowed(name, after_tree.get(name, ('file', ''))[0], tree, relative_report) for name in changed):
                    reasons.append('scope violation')
                try:
                    database_changed = db.fingerprint() != pinned_database
                except Exception:
                    database_changed = True
                if database_changed or any(name in DB_FILES for name in changed):
                    reasons.append('scope violation: database changed')
                    if _digest(backup) != backup_hash:
                        raise ValueError('recovery database backup integrity mismatch')
                    db.restore_from(backup)
                    if db.fingerprint() != pinned_database:
                        raise ValueError('recovery database fingerprint mismatch')
                try:
                    vault_changed = (_digest(vault_dir(project)/'manifest.sha256') != manifest_hash or
                                     protected_hashes(project) != pinned_protected or not check_manifest(project))
                except (OSError, ValueError):
                    vault_changed = True
                if vault_changed:
                    reasons.append('protected methodology or vault tamper flag; vault evidence preserved')
                try:
                    candidate_config = routing_config(read_config(project))
                    if any(candidate_config[key] != config[key] for key in BOUNDS):
                        reasons.append('privacy or budget bounds changed')
                    segmentation = read_config(project, 'segmentation.yaml')
                    if set(segmentation) != {'method'} or segmentation['method'] not in ('paragraph', 'utterance', 'sentence'):
                        reasons.append('invalid segmentation configuration')
                except ValueError:
                    reasons.append('invalid candidate configuration')
                ledger.finish(db, reservation, result=raw if isinstance(raw, dict) else None,
                              error=operator_error, latency_ms=(time.monotonic()-started)*1000)
                hypothesis = raw.get('hypothesis', 'Operator supplied no hypothesis.') if isinstance(raw, dict) else 'Operator supplied no hypothesis.'
                hypothesis = hypothesis[:2000] if isinstance(hypothesis, str) else 'Invalid operator hypothesis.'
                approved = {name: (project/name).read_bytes() for name in changed
                            if after_tree.get(name, ('', ''))[0] == 'file' and
                            (_mutable(name) or (name.startswith('experiments/proposals/') and name not in tree))}
                approved.update({name: None for name in changed if _mutable(name) and
                                 name not in after_tree and tree[name][0] == 'file'})
                scope_passed = not reasons
                candidate = confirmation = None
                decision = 'REVERT'
                if not reasons:
                    try:
                        tests_passed = (test_runner or _run_tests)() is True
                        candidate = evaluate_project(db, project, backend=backend, model=model, use_cache=False)
                        eligibility = decide(baseline['metrics'], candidate['metrics'], policy, tests_passed=tests_passed)
                        if eligibility['keep']:
                            confirmation = evaluate_project(db, project, backend=backend, model=model, use_cache=False)
                            confirmed = decide(baseline['metrics'], confirmation['metrics'], policy, tests_passed=tests_passed)
                            if confirmed['keep']:
                                decision = 'KEEP'
                                reasons = confirmed['reasons']
                            else:
                                reasons = ['confirmation failed', *confirmed['reasons']]
                        else:
                            reasons = eligibility['reasons']
                    except Exception:
                        reasons = ['trusted tests or validation evaluation failed']
                if db.one('SELECT count(*) AS n FROM coding_events')['n'] != coding_count:
                    raise ValueError('coding events changed during trusted evaluation; recovery required')
                _restore_tree(project, snapshot, tree)
                for name, content in approved.items():
                    if decision == 'KEEP' or (scope_passed and name.startswith('experiments/proposals/')):
                        destination = project/name
                        if content is None:
                            destination.unlink()
                        else:
                            destination.parent.mkdir(parents=True, exist_ok=True)
                            destination.write_bytes(content)
                if decision == 'KEEP' and pipeline_hash(project) != candidate['pipeline_version']:
                    raise ValueError('kept pipeline differs from measured candidate; recovery required')
                reason = '; '.join(dict.fromkeys(reasons))
                report_path.write_text(_report(number, decision, reason, hypothesis, changed,
                                              baseline, candidate, confirmation), encoding='utf-8')
                slug = 'measured-gain' if decision == 'KEEP' else 'rejected'
                tag = f'exp-{number:04d}-{slug}' if decision == 'KEEP' else None
                if tag and _git(project, 'tag', '--list', tag):
                    raise ValueError('experiment tag already exists; recovery required')
                record = {'slug': slug, 'agent': agent, 'decision': decision,
                    'reason': reason, 'hypothesis': hypothesis, 'before_json': canonical(baseline),
                    'after_json': canonical({**(candidate or {}), 'confirmation': confirmation}),
                    'changed_files_json': canonical(changed), 'commit_hash': None, 'tag': tag}
                state.update(stage='git', decision=decision, tag=tag, record=record)
                _journal(journal, state)
                _git(project, 'add', '--', '.', f':(exclude){LOCK}')
                _git(project, '-c', 'user.name=Qualia', '-c', 'user.email=qualia@localhost',
                     'commit', '-m', f'experiment: {decision} {number:04d} {slug}')
                commit = _git(project, 'rev-parse', 'HEAD')
                if tag:
                    _git(project, 'tag', tag)
                record['commit_hash'] = commit
                state.update(stage='database', commit=commit)
                _journal(journal, state)
                row_id = db.add('experiments', record)
                if _status(project):
                    raise ValueError('experiment Git status is not clean; recovery required')
                results.append(db.one('SELECT * FROM experiments WHERE id=?', (row_id,)))
                state.update(stage='complete', experiment_id=row_id)
                _journal(journal, state)
                if snapshot_root.resolve().parent != recovery.resolve():
                    raise ValueError('recovery snapshot escaped workspace')
                _clear_snapshot(snapshot_root)
                journal.unlink()
            except Exception:
                raise ValueError('experiment stopped; pending recovery journal preserves the snapshot and finalization state') from None
    return results
