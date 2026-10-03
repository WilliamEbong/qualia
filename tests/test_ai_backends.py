from qualia.ai.backends.fake import FakeBackend
from qualia.ai.backends.rules import RulesBackend
from qualia.ai.schemas import response_schema, validate_result


def test_fake_modes_do_not_need_gold_labels():
    segments = [{'id': 's1', 'text': 'Synthetic text'}]
    codes = [{'id': 1, 'name': 'One', 'status': 'active'},
             {'id': 2, 'name': 'Two', 'status': 'active'}]
    for mode, expected in [('first', [1]), ('all', [1, 2]), ('none', [])]:
        result = FakeBackend().classify(segments, response_schema(), {'codebook': codes, 'fake_mode': mode})
        validated = validate_result(result, segments, codes)
        assert [item['code_id'] for item in validated['predictions'][0]['codes']] == expected
        assert not FakeBackend.external


def test_rules_match_declared_keywords_and_remain_offline():
    segments = [{'id': 's1', 'text': 'A hopeful possibility.'}, {'id': 's2', 'text': 'Unrelated.'}]
    codes = [{'id': 1, 'name': 'Hope', 'include': 'hopeful, possibility', 'status': 'active'},
             {'id': 2, 'name': 'Unrelated', 'status': 'archived'}]
    result = validate_result(RulesBackend().classify(segments, response_schema(), {'codebook': codes}), segments, codes)
    assert result['predictions'][0]['codes'][0]['code_id'] == 1
    assert result['predictions'][1]['codes'] == []
    assert RulesBackend().available() and not RulesBackend.external
