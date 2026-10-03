import json

import pytest

from qualia.store.db import Store


def test_hierarchy_cycles_and_immutable_frozen_versions():
    with Store(':memory:') as db:
        parent = db.save_code({'name': 'Parent', 'examples_pos': ['Synthetic example']})
        child = db.save_code({'name': 'Child', 'parent_id': parent})
        grandchild = db.save_code({'name': 'Grandchild', 'parent_id': child})
        for node in (parent, grandchild):
            with pytest.raises(ValueError, match='cycle'):
                db.save_code({'parent_id': node}, parent)
        frozen = db.freeze_codebook()
        assert db.freeze_codebook()['id'] == frozen['id']
        db.save_code({'definition': 'Changed draft', 'status': 'archived'}, child)
        assert db.one('SELECT * FROM codebook_versions WHERE id=?', (frozen['id'],)) == frozen
        assert db.freeze_codebook()['hash'] != frozen['hash']
        assert json.loads(db.one('SELECT examples_pos FROM codes WHERE id=?', (parent,))['examples_pos']) == ['Synthetic example']


@pytest.mark.parametrize('values', [{'name': '  '}, {'name': 'x', 'parent_id': 99},
                                    {'name': 'x', 'examples_neg': 'not a list'}, {'name': 'x', 'id': 8}])
def test_invalid_code_records(values):
    with Store(':memory:') as db:
        with pytest.raises(ValueError):
            db.save_code(values)
