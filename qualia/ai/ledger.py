"""The only AI usage/egress coordinator; SQL writes stay in Store."""

import hashlib
import math


def reserve(db, *, backend, model, run_id, segments, config, purpose, reserved_usd=0.0):
    return db.reserve_attempt(backend=backend.name, model=model, run_id=run_id,
                              segment_hashes=[hashlib.sha256(item['text'].encode('utf-8')).hexdigest()
                                              for item in segments], external=backend.external,
                              allow_external=config['allow_external'], daily_calls=config['daily_calls'],
                              run_segments=config['run_segments'], daily_usd=config['jev_daily_usd'],
                              reserved_usd=reserved_usd, purpose=purpose)


def _tokens(value):
    return value if type(value) is int and 0 <= value <= 2**63-1 else 0


def finish(db, reservation_id, *, result=None, error=None, latency_ms=0.0,
           cost_usd=None, reserved_usd=0.0):
    if result is not None:
        usage = result
    else:
        usage = {key: getattr(error, key, None) for key in ('input_tokens', 'output_tokens', 'cli_version')}
    version = usage.get('cli_version')
    if not isinstance(version, str) or not version.strip() or len(version) > 200:
        version = None
    # Unknown actual costs conservatively consume the reservation ceiling.
    amount = cost_usd if cost_usd is not None else reserved_usd
    if not isinstance(amount, (int, float)) or not math.isfinite(amount) or amount < 0:
        amount = reserved_usd
    return db.finish_attempt(reservation_id, input_tokens=_tokens(usage.get('input_tokens')),
                             output_tokens=_tokens(usage.get('output_tokens')), cli_version=version,
                             latency_ms=latency_ms, cost_usd=amount,
                             status='error' if error is not None else 'ok')


def cache_hit(db, *, backend, model, run_id, cli_version, run_segments):
    with db.immediate():
        used = db.one('SELECT coalesce(sum(segments),0) AS count FROM usage_ledger WHERE run_id=?',
                      (run_id,))['count']
        if used + 1 > run_segments:
            raise ValueError('budget reached')
        return db.add('usage_ledger', {'backend': backend, 'model': model, 'run_id': run_id,
                                      'calls': 0, 'segments': 1, 'status': 'cache_hit',
                                      'cli_version': cli_version})
