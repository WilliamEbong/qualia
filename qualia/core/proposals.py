"""Offline evidence for codebook revisions: pure, deterministic and never applied automatically."""

import json
from collections import defaultdict
from itertools import combinations

MIN_REJECTIONS = 2
MAX_NEW_NEGATIVES = 5
UNUSED_AFTER = 20
OVERLAP_JACCARD = 0.8
OVERLAP_MIN = 5


def code_values(code: dict) -> dict:
    """A draft code row as the editable values a proposal carries."""
    return {'name': code['name'], 'parent_id': code['parent_id'], 'status': code['status'],
            'definition': code['definition'], 'include': code['include'], 'exclude': code['exclude'],
            'examples_pos': json.loads(code['examples_pos']),
            'examples_neg': json.loads(code['examples_neg'])}


def mine(evidence: dict) -> list[dict]:
    """Propose revisions from rejected suggestions, unused codes and overlapping pairs."""
    codes = {code['id']: code for code in evidence['codes']}
    active = sorted(code_id for code_id, code in codes.items() if code['status'] == 'active')
    presence = defaultdict(set)
    for row in evidence['presence']:
        presence[row['code_id']].add(row['segment_id'])
    coded = set().union(*presence.values())
    pending = {(item.get('signal'), tuple(item.get('code_ids', [])))
               for item in map(json.loads, evidence['pending'])}
    proposals = []

    def propose(signal, code_ids, target, changes, rationale, details):
        if (signal, tuple(code_ids)) not in pending:
            proposals.append({'kind': 'revise_code', 'target_code_id': target,
                              'payload': {**code_values(codes[target]), **changes},
                              'rationale': rationale,
                              'evidence': {'signal': signal, 'code_ids': list(code_ids), **details}})

    rejected = defaultdict(list)
    for row in evidence['rejections']:
        rejected[row['code_id']].append(row)
    for code_id in active:
        rows = rejected[code_id]
        if len(rows) < MIN_REJECTIONS:
            continue
        negatives = json.loads(codes[code_id]['examples_neg'])
        new = []
        for row in rows:
            text = (row['excerpt'] or '').strip()
            if text and text not in negatives and text not in new and len(new) < MAX_NEW_NEGATIVES:
                new.append(text)
        if not new:
            continue
        notes = list(dict.fromkeys(row['note'].strip() for row in rows if row['note'].strip()))[:3]
        rationale = (f'Reviewers rejected {len(rows)} AI suggestions of “{codes[code_id]["name"]}”. '
                     'Adding the rejected passages as negative examples shows where the code does not '
                     'apply; remove any that were rejected for another reason, such as a wrong span.')
        if notes:
            rationale += ' Review notes: ' + '; '.join(f'“{note}”' for note in notes) + '.'
        propose('rejections', [code_id], code_id, {'examples_neg': negatives + new}, rationale,
                {'segment_ids': sorted({row['segment_id'] for row in rows}),
                 'coding_event_ids': [row['coding_event_id'] for row in rows],
                 'excerpts': new, 'notes': notes})

    if len(coded) >= UNUSED_AFTER:
        for code_id in active:
            if not presence[code_id]:
                propose('unused', [code_id], code_id, {'status': 'archived'},
                        f'“{codes[code_id]["name"]}” has no current coding across {len(coded)} coded '
                        'segments. Archive it, or keep it if it is a deliberate category you still '
                        'expect to apply.', {'coded_segments': len(coded)})

    for left, right in combinations(active, 2):
        both = presence[left] & presence[right]
        union = presence[left] | presence[right]
        if len(both) < OVERLAP_MIN or len(both) / len(union) < OVERLAP_JACCARD:
            continue
        # Revise the less frequent code; on a tie, the later one.
        target, other = sorted((left, right), key=lambda code_id: (len(presence[code_id]), -code_id))
        boundary = (f'Not when “{codes[other]["name"]}” describes the passage better '
                    '(draft boundary: reword before freezing).')
        jaccard = len(both) / len(union)
        propose('overlap', [left, right], target,
                {'exclude': (codes[target]['exclude'].rstrip() + '\n' + boundary).strip()},
                f'“{codes[left]["name"]}” and “{codes[right]["name"]}” are both applied on {len(both)} '
                f'of the {len(union)} segments carrying either (Jaccard {jaccard:.2f}). Clarify the '
                'boundary, merge them, or keep both if the overlap is intended.',
                {'segment_ids': sorted(both)[:20], 'jaccard': round(jaccard, 3)})
    return proposals
