"""Policy, bounded classification, validated cache reuse and explicit suggestions."""

import hashlib
import importlib
import json
import re
import time
import uuid

from qualia.ai import ledger
from qualia.ai.backends.fake import FakeBackend
from qualia.ai.backends.rules import RulesBackend
from qualia.ai.cache import cache_key, load_cached
from qualia.ai.models import CATALOG, TASK_DEFAULTS, default_model
from qualia.ai.schemas import (
    ResponseValidationError,
    response_schema,
    routing_config,
    validate_result,
)
from qualia.store.db import canonical
from qualia.workspace import pipeline_hash, read_config

RETRYABLE = {'timeout', 'transient', 'process_failed', 'transport_error', 'rate_limit'}
SAFE_FAILURES = RETRYABLE | {'invalid_model', 'unavailable', 'input_limit', 'output_limit',
                            'unsupported_version', 'invalid_input', 'tool_call', 'invalid_response',
                            'subscription_auth_required', 'quota', 'unsupported_flag'}


def safe_failure(exc) -> str:
    """A displayable failure: a known code plus a vetted flag or version, never provider text."""
    code = getattr(exc, 'code', None)
    if not isinstance(code, str) or code not in SAFE_FAILURES:
        return 'provider_error'
    flag = getattr(exc, 'flag', None)
    if code == 'unsupported_flag' and isinstance(flag, str) and re.fullmatch(r'--?[A-Za-z][A-Za-z0-9-]*', flag):
        return f'{code}: the installed CLI no longer accepts {flag}'
    version = getattr(exc, 'cli_version', None)
    if code == 'unsupported_version' and isinstance(version, str) and re.fullmatch(r'[0-9A-Za-z.+-]{1,40}', version):
        return f'{code}: CLI {version} is older than the minimum Qualia supports; update the CLI'
    return code


class UnavailableBackend:
    external = True

    def __init__(self, name, reason):
        self.name = name
        self.unavailable_reason = reason

    def available(self):
        return False


def default_registry():
    result = {'rules': RulesBackend(), 'fake': FakeBackend()}
    for name, class_name in (('claude', 'ClaudeCLIBackend'), ('codex', 'CodexCLIBackend')):
        try:
            module = importlib.import_module(f'qualia.ai.backends.{name}_cli')
            result[name] = getattr(module, class_name)()
        except ImportError:
            result[name] = UnavailableBackend(name, 'Backend is not installed.')
    from qualia.ai.backends.jev import JevBackend

    result['jev'] = JevBackend()
    return result


def availability(project, registry=None):
    config = routing_config(read_config(project))
    backends = []
    for name, backend in (default_registry() if registry is None else registry).items():
        try:
            available = bool(backend.available())
        except Exception:
            available = False
        reason = '' if available else getattr(backend, 'unavailable_reason', 'Backend is unavailable.')
        if backend.external and not config['allow_external']:
            reason = 'External AI is disabled for this project.'
        if not available and not reason:
            reason = 'Backend is unavailable.'
        backends.append({'name': name, 'available': available, 'external': backend.external,
                         'reason': reason, 'models': CATALOG.get(name, [])})
    defaults = {task: {item['name']: _select(config, item['name'], None, task)[1] for item in backends}
                for task in TASK_DEFAULTS}
    return {'allow_external': config['allow_external'], 'backends': backends, 'defaults': defaults}


def _admits(provider, batch, context):
    # Priced adapters validate request bounds in estimate_cost; others accept any configured batch.
    if not hasattr(provider, 'estimate_cost'):
        return True
    try:
        provider.estimate_cost(batch, context)
    except Exception:
        return False
    return True


def _select(config, backend, model, task):
    """Explicit model, then the project's task override, then the built-in task default."""
    override = config['tasks'].get(task)
    # A tier is an alias such as 'cheap' or 'strong'; real backend names always mean the backend
    # (the default routing also has a tier called 'claude', which must not shadow task defaults).
    if backend in config['tiers'] and backend not in CATALOG:
        selected = config['tiers'][backend]
    elif override and backend in (None, override['backend']):
        selected = override
    else:
        name = config['backend'] if backend is None else backend
        # The project's top-level model is its classification choice; other tasks use their own default.
        chosen = (config['model'] if task == 'classification' and name == config['backend']
                  else default_model(task, name))
        selected = {'backend': name, 'model': chosen}
    return selected['backend'], model or selected['model']


def _summary(run_id, backend, model):
    return {'run_id': run_id, 'backend': backend, 'model': model, 'segments': 0, 'calls': 0,
            'cache_hits': 0, 'escalated_segments': 0, 'suggestion_ids': [], 'predictions': [],
            'status': 'completed', 'errors': []}


def classify_segments(db, segments, codebook, config, *, prompt, codebook_version_id,
                      pipeline_version, backend=None, model=None, task='classification',
                      run_id=None, persist=False, registry=None, use_cache=True, cache_results=True,
                      with_candidates=False):
    config = routing_config(config)
    name, selected_model = _select(config, backend, model, task)
    run_id = run_id or uuid.uuid4().hex
    result = _summary(run_id, name, selected_model)
    if not isinstance(run_id, str) or not run_id.strip():
        raise ValueError('run identity is required')
    expected = {}
    for segment in segments:
        identity = segment.get('id')
        text = segment.get('text')
        if (not isinstance(identity, str) or not identity or identity in expected
                or not isinstance(text, str) or not text):
            result.update(status='error', errors=['invalid or duplicate segment record'])
            return result
        if len(text) > config['max_segment_chars']:
            result.update(status='error', errors=[f'segment {identity}: exceeds max_segment_chars'])
            return result
        expected[identity] = text
    used = db.one('SELECT coalesce(sum(segments),0) AS count FROM usage_ledger WHERE run_id=?',
                  (run_id,))['count']
    if used + len(segments) > config['run_segments']:
        result.update(status='budget_reached', errors=['budget reached: run segment limit'])
        return result
    if not segments:
        return result
    if not codebook or not any(code.get('status', 'active') == 'active' for code in codebook):
        result.update(status='error', errors=['freeze an active codebook before classification'])
        return result
    registry = default_registry() if registry is None else registry
    prompt_hash = hashlib.sha256(prompt.encode('utf-8')).hexdigest()
    outcomes = {}
    failures = []
    disagreed = set()

    def classify_batch_inputs(inputs, backend_name, model_name):
        provider = registry.get(backend_name)
        if provider is None:
            failures.append(('unavailable', f'backend {backend_name} is unavailable'))
            return {}
        collected = {}
        default = getattr(provider, 'default_threshold', None) or 0

        def assign(prediction):
            # Thresholds act on raw (cached) scores, so changing them never needs a new call.
            return {**prediction, 'codes': [code for code in prediction['codes'] if code['score'] >=
                    config['code_thresholds'].get(str(code['code_id']), default)]}

        context = {'codebook': codebook, 'model': model_name, 'prompt': prompt,
                   'max_output_tokens': config['max_output_tokens'], 'fake_mode': config['fake_mode'],
                   'task': task}
        # Owner-approved native accounting is per invocation, not per internal HTTP request.
        native = backend_name in ('claude', 'codex')
        batch_size = min(config['segments_per_call'], 5) if native else config['segments_per_call']
        retries = 0 if native else config['max_retries']
        offset = 0
        while offset < len(inputs):
            size = min(batch_size, len(inputs) - offset)
            # Shrink a batch the provider cannot admit (e.g. Jev's request-size bound) rather than fail it.
            while size > 1 and not _admits(provider, inputs[offset:offset + size], context):
                size -= 1
            batch = inputs[offset:offset + size]
            offset += size
            context_hash = hashlib.sha256(canonical({'batch': batch, 'context': context}).encode()).hexdigest()
            keys = {segment['id']: cache_key(segment=segment, prompt_hash=prompt_hash,
                    codebook_version_id=codebook_version_id, backend=backend_name,
                    model=model_name, pipeline_version=pipeline_version, task=task,
                    context_hash=context_hash) for segment in batch}
            cached_batch = [load_cached(db, keys[segment['id']], segment, codebook) if use_cache else None
                            for segment in batch]
            # Co-batch text is provider context: reuse all entries or dispatch the identical whole batch.
            if all(cached is not None for cached in cached_batch):
                for segment, cached in zip(batch, cached_batch, strict=True):
                    try:
                        ledger.cache_hit(db, backend=backend_name, model=model_name, run_id=run_id,
                                         cli_version=cached['cli_version'], run_segments=config['run_segments'])
                    except ValueError:
                        failures.append(('budget_reached', 'budget reached'))
                        return collected
                    result['cache_hits'] += 1
                    raw = cached['predictions'][0]
                    collected[segment['id']] = (assign(raw), backend_name, model_name,
                                                cached['cli_version'], raw, cached.get('model_version'))
                continue
            if provider.external and not config['allow_external']:
                failures.append(('blocked', 'external AI disabled for this project'))
                return collected
            if backend_name == 'jev' and not config['jev_enabled']:
                failures.append(('blocked', 'Jev is disabled for this project'))
                return collected
            try:
                ready = provider.available()
            except Exception:
                ready = False
            if not ready:
                failures.append(('unavailable', f'backend {backend_name} is unavailable'))
                return collected
            for attempt in range(retries + 1):
                # Optional backend cost hooks let a priced adapter reserve a conservative ceiling.
                try:
                    reserved_usd = provider.estimate_cost(batch, context) if hasattr(provider, 'estimate_cost') else 0.0
                except Exception:
                    failures.append(('error', f"segment {batch[0]['id']}: cost estimate unavailable"))
                    return collected
                try:
                    reservation = ledger.reserve(db, backend=provider, model=model_name, run_id=run_id,
                                                 segments=batch, config=config, purpose=task,
                                                 reserved_usd=reserved_usd)
                except ValueError as exc:
                    status = 'budget_reached' if 'budget reached' in str(exc) else 'blocked'
                    failures.append((status, str(exc)))
                    return collected
                result['calls'] += 1
                started = time.monotonic()
                raw = None
                try:
                    raw = provider.classify(batch, response_schema(), context)
                    validated = validate_result(raw, batch, codebook)
                    if validated['output_tokens'] > config['max_output_tokens']:
                        raise ResponseValidationError(batch[0]['id'], 'output token limit exceeded')
                    cost = provider.actual_cost(validated, context) if hasattr(provider, 'actual_cost') else None
                except Exception as exc:
                    ledger.finish(db, reservation, result=raw if isinstance(raw, dict) else None,
                                  error=exc, latency_ms=(time.monotonic()-started)*1000,
                                  reserved_usd=reserved_usd)
                    retryable = getattr(exc, 'code', None) in RETRYABLE
                    if retryable and attempt < retries:
                        continue
                    identity = (exc.segment_id if isinstance(exc, ResponseValidationError) and
                                exc.segment_id in {segment['id'] for segment in batch} else batch[0]['id'])
                    # Never display arbitrary provider exception text, even for a typed adapter failure.
                    failure = 'invalid_response' if isinstance(exc, ResponseValidationError) else safe_failure(exc)
                    failures.append(('error', f"segment {identity}: classification failed ({failure})"))
                    break
                ledger.finish(db, reservation, result=validated, cost_usd=cost,
                              latency_ms=(time.monotonic()-started)*1000, reserved_usd=reserved_usd)
                for prediction in validated['predictions']:
                    identity = prediction['segment_id']
                    single = {'predictions': [prediction], 'input_tokens': 0, 'output_tokens': 0,
                              'cli_version': validated['cli_version'],
                              'model_version': validated['model_version']}
                    if cache_results:
                        db.cache_put(keys[identity], single)
                    collected[identity] = (assign(prediction), backend_name, model_name,
                                           validated['cli_version'], prediction, validated['model_version'])
                break
        return collected

    outcomes.update(classify_batch_inputs(segments, name, selected_model))
    threshold = config['escalate_below']
    strong = config['tiers'].get('strong')
    if threshold is not None and strong and (strong['backend'], strong['model']) != (name, selected_model):
        uncertain = [segment for segment in segments if segment['id'] in outcomes and
                     min((code['score'] for code in outcomes[segment['id']][0]['codes']), default=0.0) < threshold]
        if uncertain:
            additional = classify_batch_inputs(uncertain, strong['backend'], strong['model'])
            result['escalated_segments'] = len(additional)
            for identity, outcome in additional.items():
                previous = {(code['code_id'], code['span_start'], code['span_end'])
                            for code in outcomes[identity][0]['codes']}
                current = {(code['code_id'], code['span_start'], code['span_end'])
                           for code in outcome[0]['codes']}
                if current != previous:
                    disagreed.add(identity)
                outcomes[identity] = outcome
    result['predictions'] = [outcomes[segment['id']][0] for segment in segments if segment['id'] in outcomes]
    if with_candidates:
        result['candidates'] = [outcomes[segment['id']][4] for segment in segments if segment['id'] in outcomes]
    result['segments'] = len(result['predictions'])
    chosen = {(outcome[1], outcome[2]) for outcome in outcomes.values()}
    if len(chosen) == 1:
        result['backend'], result['model'] = next(iter(chosen))
    elif len(chosen) > 1:
        result['backend'] = result['model'] = 'mixed'
    if failures:
        result['errors'] = [message for _, message in failures]
        result['status'] = 'partial' if outcomes else failures[-1][0]
    if persist and outcomes:
        events = []
        for segment in segments:
            identity = segment['id']
            if identity not in outcomes:
                continue
            prediction, actual_backend, actual_model, cli_version, _, model_version = outcomes[identity]
            sampled = int(hashlib.sha256(f'{run_id}:{identity}'.encode()).hexdigest(), 16) / 2**256 < config['qc_sample_rate']
            for code in prediction['codes']:
                triggers = []
                if code['score'] < config['human_review_below']:
                    triggers.append('below_threshold')
                if identity in disagreed:
                    triggers.append('disagreement')
                if sampled:
                    triggers.append('qc_sample')
                events.append({**code, 'segment_id': int(identity), 'actor_type': 'model',
                               'actor': actual_backend, 'backend': actual_backend, 'model': actual_model,
                               'cli_version': cli_version, 'model_version': model_version,
                               'action': 'suggest', 'review_status': 'pending',
                               'review_trigger': canonical(triggers), 'codebook_version_id': codebook_version_id,
                               'pipeline_version': pipeline_version, 'prompt_hash': prompt_hash})
        result['suggestion_ids'] = db.record_suggestions(events)
    return result


def classify_project(db, project, backend=None, model=None, segment_ids=None, task='classification',
                     run_id=None, persist=True, registry=None):
    config = read_config(project)
    frozen = db.one('SELECT * FROM codebook_versions ORDER BY id DESC LIMIT 1')
    if frozen is None:
        raise ValueError('freeze a codebook before classification')
    rows = db.rows('SELECT g.id, substr(s.text,g.start+1,g.end-g.start) AS text '
                   'FROM segments g JOIN sources s ON s.id=g.source_id ORDER BY g.id')
    if segment_ids is not None:
        if (not isinstance(segment_ids, list) or any(type(value) is not int for value in segment_ids)
                or len(set(segment_ids)) != len(segment_ids)):
            raise ValueError('segment IDs must be distinct integers')
        found = {row['id'] for row in rows}
        if any(value not in found for value in segment_ids):
            missing = next(value for value in segment_ids if value not in found)
            raise ValueError(f'segment {missing}: not found')
        selected = set(segment_ids)
        rows = [row for row in rows if row['id'] in selected]
    prompt = (project / 'config/prompts/classify.txt').read_text(encoding='utf-8')
    return classify_segments(db, [{'id': str(row['id']), 'text': row['text']} for row in rows],
                             json.loads(frozen['snapshot_json']), config, prompt=prompt,
                             codebook_version_id=frozen['id'], pipeline_version=pipeline_hash(project),
                             backend=backend, model=model, task=task, run_id=run_id,
                             persist=persist, registry=registry)
