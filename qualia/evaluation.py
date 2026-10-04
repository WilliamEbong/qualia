"""Explicit benchmark orchestration. Pure metric modules never perform I/O."""

import hashlib
import json
import time
import uuid
from pathlib import Path

from qualia.ai.router import classify_segments
from qualia.eval.metrics import evaluate_metrics
from qualia.store.db import canonical
from qualia.workspace import (
    extend_manifest,
    manifest_snapshot,
    pipeline_hash,
    protected_artifact_path,
    read_config,
)


def evaluate_project(db, project, *, split='validation', protected=False,
                     backend=None, model=None, registry=None, use_cache=True):
    from qualia.io.benchmarks import load_benchmark

    if split not in ('dev', 'validation', 'protected') or (split == 'protected') != protected:
        raise ValueError('protected evaluation requires the explicit --protected option')
    expected_manifest = manifest_snapshot(project) if protected else None
    records, metadata = load_benchmark(project, split=split, protected=protected)
    frozen = db.one('SELECT * FROM codebook_versions WHERE id=?', (metadata['codebook_version_id'],))
    if frozen is None:
        raise ValueError('benchmark frozen codebook version is missing')
    codebook = json.loads(frozen['snapshot_json'])
    code_ids = [code['id'] for code in codebook if code.get('status', 'active') == 'active']
    # Check reference labels before dispatch, then send only identities and text to the router.
    allowed = set(code_ids)
    if any(not set(record['codes']) <= allowed or
           any(coder is not None and not set(coder) <= allowed for coder in record.get('coders', []))
           for record in records):
        raise ValueError('benchmark labels do not match its frozen codebook')
    prompt = (project / 'config/prompts/classify.txt').read_text(encoding='utf-8')
    pipeline = pipeline_hash(project)
    started = time.monotonic()
    result = classify_segments(db, [{'id': row['segment_id'], 'text': row['text']} for row in records],
                               codebook, read_config(project), prompt=prompt,
                               codebook_version_id=frozen['id'], pipeline_version=pipeline,
                               backend=backend, model=model, persist=False, registry=registry,
                               use_cache=use_cache and not protected, cache_results=not protected)
    elapsed = (time.monotonic() - started) * 1000
    if result['status'] != 'completed':
        raise ValueError('evaluation incomplete: ' + '; '.join(result['errors']))
    metrics = evaluate_metrics(records, result['predictions'], code_ids, calls=result['calls'],
                               latency_ms=elapsed, escalated_segments=result['escalated_segments'])
    versions = db.rows('SELECT DISTINCT cli_version FROM usage_ledger WHERE run_id=? '
                       'AND cli_version IS NOT NULL', (result['run_id'],))
    metrics['identity'] = {'prompt_hash': hashlib.sha256(prompt.encode()).hexdigest(),
                           'benchmark_hash': metadata['sha256'], 'run_id': result['run_id'],
                           'cli_versions': sorted(row['cli_version'] for row in versions),
                           'codebook_hash': frozen['hash']}
    metrics['cache_hits'] = result['cache_hits']
    metrics['definitions']['escalation_rate'] = (
        'Distinct segments with a successful strong-tier result divided by evaluated segments.')
    predictions = result['predictions']
    if protected:
        if manifest_snapshot(project) != expected_manifest:
            raise ValueError('protected manifest changed during evaluation')
        relative = 'evaluations/' + uuid.uuid4().hex + '.json'
        artifact = protected_artifact_path(project, relative)
        artifact.parent.mkdir(parents=True, exist_ok=True)
        artifact_bytes = canonical({'identity': metrics['identity'], 'predictions': predictions}).encode('utf-8')
        with artifact.open('xb') as stream:
            stream.write(artifact_bytes)
        extend_manifest(project, expected_manifest, {
            'vault/' + relative: hashlib.sha256(artifact_bytes).hexdigest(),
        })
        metrics['identity']['predictions_location'] = 'protected vault'
        predictions = []
    row_id = db.add('evaluation_runs', dict(split=split, backend=result['backend'], model=result['model'],
                    codebook_version_id=frozen['id'], pipeline_version=pipeline,
                    metrics_json=canonical(metrics), predictions_json=canonical(predictions)))
    row = db.one('SELECT created_at FROM evaluation_runs WHERE id=?', (row_id,))
    return dict(id=row_id, split=split, backend=result['backend'], model=result['model'],
                codebook_version_id=frozen['id'], pipeline_version=pipeline, metrics=metrics,
                created_at=row['created_at'])


def report_markdown(result):
    def display(value):
        if isinstance(value, list):
            return '[' + ', '.join(display(item) for item in value) + ']'
        return 'n/a' if value is None else f'{value:.6f}' if isinstance(value, float) else str(value)

    metrics = result['metrics']
    lines = [f"# Evaluation {result['id']}", '',
             f"Split: {result['split']} · Backend/model: {result['backend']}/{result['model']}",
             f"Frozen codebook: {result['codebook_version_id']} · Created: {result['created_at']}",
             f"Pipeline: `{result['pipeline_version']}`", '', '| Metric | Value |', '|---|---:|']
    for name in ('segment_count', 'macro_f1', 'micro_f1', 'exact_match', 'partial_match', 'kappa',
                 'alpha', 'ece', 'review_share', 'review_cutoff', 'escalation_rate', 'calls_per_1000',
                 'latency_ms', 'cache_hits'):
        lines.append(f'| {name} | {display(metrics[name])} |')
    lines += ['', '| Code ID | Precision | Precision 95% CI | Recall | Recall 95% CI | F1 | Support |',
              '|---|---:|---:|---:|---:|---:|---:|']
    lines += ['| ' + ' | '.join(display(row[key]) for key in (
        'code_id', 'precision', 'precision_ci95', 'recall', 'recall_ci95', 'f1', 'support'))
              + ' |' for row in metrics['per_code']]
    lines += ['', f"Alpha basis: {metrics['alpha_basis']}.", '', '## Definitions', '']
    lines += [f'- **{name}**: {value}' for name, value in metrics['definitions'].items()]
    lines += ['', '## Reproduction identity', '', '```json',
              json.dumps(metrics['identity'], ensure_ascii=False, indent=2), '```', '']
    return '\n'.join(lines)


def write_reports(result, directory: Path):
    directory.mkdir(parents=True, exist_ok=True)
    stem = f"evaluation-{result['id']:04d}-{result['split']}"
    json_path, md_path = directory / (stem + '.json'), directory / (stem + '.md')
    json_path.write_text(canonical(result) + '\n', encoding='utf-8')
    md_path.write_text(report_markdown(result), encoding='utf-8')
    return json_path, md_path
