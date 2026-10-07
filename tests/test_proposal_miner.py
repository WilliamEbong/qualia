import json

from qualia.core.proposals import mine


def code(code_id, name, status='active', negatives=()):
    return {'id': code_id, 'name': name, 'parent_id': None, 'status': status, 'definition': '',
            'include': '', 'exclude': '', 'examples_pos': '[]', 'examples_neg': json.dumps(list(negatives))}


def evidence(codes, presence=(), rejections=(), pending=()):
    return {'codes': codes, 'presence': [{'code_id': c, 'segment_id': s} for c, s in presence],
            'rejections': list(rejections), 'pending': [json.dumps(item) for item in pending]}


def rejection(event, code_id, excerpt, note=''):
    return {'coding_event_id': event, 'code_id': code_id, 'segment_id': event, 'excerpt': excerpt, 'note': note}


def test_rejections_become_new_negative_examples_with_notes():
    rows = [rejection(1, 1, 'already listed'), rejection(2, 1, 'fresh passage', 'about cost'),
            rejection(3, 1, 'fresh passage', 'about cost'), rejection(4, 2, 'single')]
    [proposal] = mine(evidence([code(1, 'Support', negatives=['already listed']), code(2, 'Other')],
                               rejections=rows))
    assert proposal['target_code_id'] == 1
    assert proposal['payload']['examples_neg'] == ['already listed', 'fresh passage']
    assert proposal['evidence']['signal'] == 'rejections' and proposal['evidence']['notes'] == ['about cost']
    assert '“about cost”' in proposal['rationale']


def test_unused_codes_need_enough_coding_and_skip_archived():
    presence = [(1, segment) for segment in range(20)]
    codes = [code(1, 'Used'), code(2, 'Unused'), code(3, 'Old', status='archived')]
    [proposal] = mine(evidence(codes, presence))
    assert proposal['target_code_id'] == 2 and proposal['payload']['status'] == 'archived'
    assert mine(evidence(codes, presence[:19])) == []


def test_overlap_targets_less_frequent_code_and_respects_thresholds():
    presence = [(1, s) for s in range(6)] + [(2, s) for s in range(5)]
    [proposal] = mine(evidence([code(1, 'Worry'), code(2, 'Fear')], presence))
    assert proposal['target_code_id'] == 2
    assert 'Not when “Worry”' in proposal['payload']['exclude']
    assert proposal['evidence'] == {'signal': 'overlap', 'code_ids': [1, 2], 'segment_ids': [0, 1, 2, 3, 4],
                                    'jaccard': 0.833}
    loose = [(1, s) for s in range(10)] + [(2, s) for s in range(5)]
    assert mine(evidence([code(1, 'Worry'), code(2, 'Fear')], loose)) == []


def test_pending_signals_are_not_proposed_again():
    presence = [(1, s) for s in range(5)] + [(2, s) for s in range(5)]
    codes = [code(1, 'Worry'), code(2, 'Fear')]
    assert mine(evidence(codes, presence, pending=[{'signal': 'overlap', 'code_ids': [1, 2]}])) == []
