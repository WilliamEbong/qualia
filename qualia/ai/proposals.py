"""Codebook proposals from AI or offline evidence, stored for a human decision and never applied."""

import hashlib
import time
import uuid

from qualia.ai import ledger
from qualia.ai.router import _select, default_registry, safe_failure
from qualia.ai.schemas import (
    CodeProposalSet,
    ProposalValidationError,
    routing_config,
    validate_proposals,
)
from qualia.core.proposals import code_values, mine
from qualia.store.db import canonical
from qualia.workspace import read_config

# In-code instructions: not under config/, so the improvement loop can never rewrite them.
PROMPTS = {
    'draft': (
        'Read the segments and propose up to 8 new codes that would help a researcher describe what '
        'participants say. Stay close to the data: name concrete experiences, actions or meanings, not '
        'broad topics or single frequent words. Do not repeat or rename existing codes. If a focus is '
        'given, prefer codes relevant to it. For each code give a short name, a one or two sentence '
        'definition, when it applies (include) and when it does not (exclude), one to three positive '
        'examples copied exactly from the segments, and the ids of the segments that support it. Explain '
        'briefly why the code is useful. These are suggestions for the researcher to judge, not themes '
        'or findings.'),
    'refine': (
        'For each code in codes_to_refine, propose one revision that makes it easier to apply '
        'consistently. Use its accepted segments, rejected segments and review notes: sharpen the '
        'definition, add include or exclude guidance for the boundary the rejections reveal, and add '
        'examples copied exactly from the segments. Keep the existing examples unless one contradicts '
        'the evidence, and keep the name unless it is misleading. Return the complete revised fields '
        "with the code's id as target_code_id and the supporting segment ids. Explain the change briefly."),
}
MAX_SEGMENTS = 20
REFINE_CODES = 2
REFINE_EVIDENCE = 4
EDITABLE = ('name', 'definition', 'include', 'exclude', 'examples_pos', 'examples_neg')


def _summary(batch, backend, model):
    return {'batch_id': batch, 'status': 'completed', 'backend': backend, 'model': model,
            'proposal_ids': [], 'errors': []}


def _latest_version(db):
    row = db.one('SELECT id FROM codebook_versions ORDER BY id DESC LIMIT 1')
    return row['id'] if row else None


def propose_from_evidence(db) -> dict:
    """Offline: no AI call, no usage or egress row."""
    result = _summary(uuid.uuid4().hex, 'evidence', 'qualia-evidence-v1')
    version = _latest_version(db)
    rows = [{'batch_id': result['batch_id'], 'mode': 'evidence', 'kind': item['kind'],
             'target_code_id': item['target_code_id'], 'payload_json': canonical(item['payload']),
             'rationale': item['rationale'], 'evidence_json': canonical(item['evidence']),
             'actor_type': 'rule', 'codebook_version_id': version}
            for item in mine(db.code_proposal_evidence())]
    result['proposal_ids'] = db.record_code_proposals(rows) if rows else []
    return result


def _segment_texts(db, ids):
    rows = db.rows('SELECT g.id, substr(s.text,g.start+1,g.end-g.start) AS text FROM segments g '
                   f'JOIN sources s ON s.id=g.source_id WHERE g.id IN ({",".join("?" * len(ids))})', ids)
    found = {row['id']: row['text'] for row in rows}
    for identity in ids:
        if identity not in found:
            raise ValueError(f'segment {identity}: not found')
    return [{'id': str(identity), 'text': found[identity]} for identity in ids]


def _distinct_ids(values, low, high, label):
    if (not isinstance(values, list) or any(type(value) is not int for value in values)
            or len(set(values)) != len(values) or not low <= len(values) <= high):
        raise ValueError(f'choose {low} to {high} distinct {label}')
    return values


def propose_with_ai(db, project, mode, backend=None, model=None, segment_ids=None, code_ids=None,
                    focus='', registry=None) -> dict:
    """Draft new codes from chosen segments, or refine chosen codes from their review evidence."""
    if mode not in PROMPTS:
        raise ValueError('mode must be draft or refine')
    if not isinstance(focus, str) or len(focus) > 500:
        raise ValueError('focus must be text of at most 500 characters')
    config = routing_config(read_config(project))
    name, selected = _select(config, backend, model, 'proposal')
    result = _summary(uuid.uuid4().hex, name, selected)
    codes = db.rows('SELECT * FROM codes ORDER BY id')
    active = {code['id']: code for code in codes if code['status'] == 'active'}
    refine, targets = [], set()
    if mode == 'draft':
        segments = _segment_texts(db, _distinct_ids(segment_ids or [], 1, MAX_SEGMENTS, 'segments'))
    else:
        wanted = []
        for code_id in _distinct_ids(code_ids or [], 1, REFINE_CODES, 'codes'):
            if code_id not in active:
                raise ValueError(f'code {code_id} is not an active draft code')
            accepted = [row['segment_id'] for row in db.rows(
                'SELECT DISTINCT segment_id FROM current_codings WHERE code_id=? '
                'ORDER BY segment_id DESC LIMIT ?', (code_id, REFINE_EVIDENCE))]
            rejected, notes = [], []
            for row in db.rows("SELECT e.segment_id, f.note FROM feedback_events f JOIN coding_events e "
                               "ON e.id=f.coding_event_id WHERE f.decision='reject' AND e.code_id=? "
                               'ORDER BY f.id DESC', (code_id,)):
                if row['segment_id'] not in rejected and len(rejected) < REFINE_EVIDENCE:
                    rejected.append(row['segment_id'])
                if row['note'].strip() and len(notes) < 3:
                    notes.append(row['note'].strip())
            if not accepted and not rejected:
                raise ValueError(f'code {code_id} has no coded or reviewed passages to learn from')
            refine.append({**code_values(active[code_id]), 'id': code_id,
                           'accepted_segment_ids': [str(value) for value in accepted],
                           'rejected_segment_ids': [str(value) for value in rejected],
                           'review_notes': notes})
            targets.add(code_id)
            wanted += [value for value in accepted + rejected if value not in wanted]
        segments = _segment_texts(db, wanted)
    for segment in segments:
        if len(segment['text']) > config['max_segment_chars']:
            raise ValueError(f"segment {segment['id']}: exceeds max_segment_chars")

    def stop(status, message):
        result.update(status=status, errors=[message])
        return result

    provider = (default_registry() if registry is None else registry).get(name)
    if provider is None:
        return stop('unavailable', f'backend {name} is unavailable')
    if provider.external and not config['allow_external']:
        return stop('blocked', 'external AI disabled for this project')
    try:
        ready = provider.available()
    except Exception:
        ready = False
    if not ready:
        return stop('unavailable', f'backend {name} is unavailable')
    if not hasattr(provider, 'propose'):
        return stop('unavailable', f'backend {name} cannot propose codes; choose claude, codex or fake')
    context = {'prompt': PROMPTS[mode], 'focus': focus.strip(), 'refine': refine, 'model': selected,
               'max_output_tokens': config['max_output_tokens'],
               'codebook': [{key: code[key] for key in ('id', 'name', 'definition', 'include', 'exclude')}
                            for code in active.values()]}
    try:
        reservation = ledger.reserve(db, backend=provider, model=selected, run_id=result['batch_id'],
                                     segments=segments, config=config, purpose='codebook_proposal')
    except ValueError as exc:
        return stop('budget_reached' if 'budget reached' in str(exc) else 'blocked', str(exc))
    started = time.monotonic()
    raw = None
    try:
        raw = provider.propose(segments, CodeProposalSet.model_json_schema(), context)
        validated = validate_proposals(raw, mode, segments, codes, targets)
        if validated['output_tokens'] > config['max_output_tokens']:
            raise ProposalValidationError('output token limit exceeded')
    except Exception as exc:
        ledger.finish(db, reservation, result=raw if isinstance(raw, dict) else None, error=exc,
                      latency_ms=(time.monotonic() - started) * 1000)
        if isinstance(exc, ProposalValidationError):
            return stop('error', f'proposals rejected: {exc}')
        return stop('error', f'codebook proposal failed ({safe_failure(exc)})')
    ledger.finish(db, reservation, result=validated, latency_ms=(time.monotonic() - started) * 1000)
    version = _latest_version(db)
    prompt_hash = hashlib.sha256(PROMPTS[mode].encode('utf-8')).hexdigest()
    rows = []
    for item in validated['proposals']:
        target = item['target_code_id']
        base = code_values(active[target]) if target is not None else {'status': 'active', 'parent_id': None}
        rows.append({'batch_id': result['batch_id'], 'mode': mode, 'kind': item['kind'],
                     'target_code_id': target,
                     'payload_json': canonical({**base, **{key: item[key] for key in EDITABLE}}),
                     'rationale': item['rationale'],
                     'evidence_json': canonical({'segment_ids': [int(value) for value in
                                                                 item['evidence_segment_ids']],
                                                 'focus': focus.strip()}),
                     'actor_type': 'model', 'backend': name, 'model': selected,
                     'cli_version': validated['cli_version'], 'prompt_hash': prompt_hash,
                     'codebook_version_id': version})
    result['proposal_ids'] = db.record_code_proposals(rows) if rows else []
    return result
