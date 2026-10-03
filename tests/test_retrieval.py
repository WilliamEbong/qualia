from test_coding import seed_coding

from qualia.store.db import Store


def test_matrix_counts_distinct_segments_and_matches_filtered_retrieval():
    with Store(':memory:') as db:
        source, _, event = seed_coding(db)
        first = db.save_case({'name': 'first'})
        second = db.save_case({'name': 'second'})
        db.link_case(source, first)
        db.link_case(source, second)
        db.assign(event)
        db.assign({**event, 'span_start': 0, 'span_end': 2})
        assert len(db.retrieve()) == 2
        assert db.matrix() == [{'code_id': event['code_id'], 'case_id': first, 'count': 1},
                               {'code_id': event['code_id'], 'case_id': second, 'count': 1}]
        for cell in db.matrix():
            rows = db.retrieve(cell['code_id'], cell['case_id'])
            assert len({r['segment_id'] for r in rows}) == cell['count']
        assert db.retrieve(code_id=999) == []
        assert db.retrieve(case_id=999) == []
