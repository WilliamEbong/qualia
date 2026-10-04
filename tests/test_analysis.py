import copy
import json

import pytest

from qualia.core.analysis_models import AnalysisOptions
from qualia.eval import analysis
from qualia.eval.analysis import analyze


def fixture():
    texts = ['Café café Straße 😀 alpha beta', 'Beta naïve 中文', 'Uncoded words']
    data = {
        'sources': [{'id': i, 'name': f'Source {i}', 'text': text}
                    for i, text in enumerate(texts, 1)],
        'segments': [{'id': i, 'source_id': i, 'start': 0, 'end': len(text),
                      'speaker': None} for i, text in enumerate(texts, 1)],
        'cases': [{'id': i, 'name': f'Case {i}'} for i in range(1, 5)],
        'source_cases': [{'source_id': 1, 'case_id': 1}, {'source_id': 1, 'case_id': 2},
                         {'source_id': 2, 'case_id': 2}, {'source_id': 2, 'case_id': 3},
                         {'source_id': 3, 'case_id': 4}],
        'attributes': [{'case_id': c, 'key': k, 'value': v} for c, k, v in [
            (1, 'group', 'A'), (1, 'group', 'A'), (2, 'group', 'B'),
            (3, 'group', 'A'), (3, 'group', 'B'), (4, 'group', ' '),
            (1, 'x', '1'), (2, 'x', '2'), (3, 'x', '3'),
            (1, 'y', '2'), (2, 'y', '4'), (3, 'y', '6'), (4, 'y', 'bad'),
        ]],
        'codes': [{'id': 1, 'name': 'Current name'}, {'id': 2, 'name': 'Second'},
                  {'id': 3, 'name': 'Only suggested'}],
        'codebook_versions': [{'id': 1, 'hash': 'h1'}, {'id': 2, 'hash': 'h2'}],
        'current_codings': [], 'pipeline_version': 'pipeline',
    }
    # Segment 1 only touches; segment 2 positively overlaps.
    for identity, segment, code, start, end, action, version in [
        (1, 1, 1, 0, 4, 'assign', 1), (2, 1, 1, 1, 3, 'assign', 2),
        (3, 1, 2, 4, 8, 'accept', 1), (4, 2, 1, 0, 5, 'assign', 1),
        (5, 2, 2, 3, 7, 'assign', 2), (6, 3, 3, 0, 3, 'suggest', 1),
        (7, 3, 3, 0, 3, 'reject', 1), (8, 3, 3, 0, 3, 'remove', 1),
    ]:
        data['current_codings'].append(dict(id=identity, segment_id=segment, code_id=code,
            span_start=start, span_end=end, action=action, codebook_version_id=version))
    return data


def test_distinct_presence_denominators_and_complete_provenance():
    data = fixture()
    before = copy.deepcopy(data)
    report = analyze(data, AnalysisOptions(excerpt_limit=1, top_words=1))
    assert data == before
    assert (report.source_count, report.segment_count, report.case_count) == (3, 3, 4)
    assert report.coded_segment_count == 2
    assert report.selected_segment_ids == [1, 2, 3]
    assert report.coding_event_ids == [1, 2, 3, 4, 5]
    assert report.codebook_version_ids == [1, 2]
    assert report.codebook_hashes == {'1': 'h1', '2': 'h2'}
    first = report.frequencies[0]
    assert (first.name, first.segment_count, first.case_count) == ('Current name', 2, 3)
    assert first.segment_percent == pytest.approx(200 / 3)
    assert first.case_percent == 75
    assert first.codebook_version_ids == [1, 2]
    assert report.frequencies[2].segment_count == 0
    assert report.excerpt_total == 3 and len(report.excerpts) == 1
    assert report.excerpts[0].coding_event_ids == [1, 2, 3]
    assert len(report.input_hash) == 64
    json.dumps(report.model_dump(), allow_nan=False)


def test_groups_case_links_missing_conflicts_and_no_source_inheritance():
    data = fixture()
    data['attributes'].append({'source_id': 3, 'case_id': None, 'key': 'group', 'value': 'A'})
    report = analyze(data, AnalysisOptions(group_by='group'))
    groups = {(g.status, g.value): g for g in report.groups}
    assert groups['value', 'A'].case_ids == [1]
    assert groups['value', 'B'].case_ids == [2]
    assert groups['value', 'B'].segment_ids == [1, 2]
    assert groups['value', 'B'].frequencies[0].case_percent == 100
    assert groups['value', 'B'].frequencies[0].segment_percent == 100
    assert next(g for g in report.groups if g.status == 'conflicting').case_ids == [3]
    assert next(g for g in report.groups if g.status == 'missing').case_ids == [4]
    assert report.case_rows[1].code_counts == {'1': 2, '2': 2, '3': 0}
    assert any('multiple' in warning.lower() for warning in report.warnings)


def test_filters_intersect_and_only_explicit_case_links_count():
    report = analyze(fixture(), AnalysisOptions(case_id=2, source_id=1, query='STRASSE',
                                               code_ids=[1, 2], code_match='all'))
    assert report.selected_segment_ids == [1]
    assert report.case_count == 1 and report.frequencies[0].case_ids == [2]
    assert report.case_rows[0].case_id == 2
    assert analyze(fixture(), AnalysisOptions(query='.*')).segment_count == 0
    assert analyze(fixture(), AnalysisOptions(code_ids=[1, 3], code_match='any')).segment_count == 2
    assert analyze(fixture(), AnalysisOptions(code_ids=[1, 3], code_match='all')).segment_count == 0


def test_overlap_positive_intersection_and_union_not_span_count():
    same = analyze(fixture(), AnalysisOptions()).pairs[0]
    overlap = analyze(fixture(), AnalysisOptions(cooccurrence='overlap')).pairs[0]
    assert (same.count, same.union_count, same.jaccard) == (2, 2, 1)
    assert (overlap.count, overlap.union_count, overlap.jaccard) == (1, 2, 1)
    assert overlap.segment_ids == [2]


def test_unicode_words_casefold_stopwords_and_exact_segment_slices():
    data = fixture()
    data['sources'][2]['text'] = "prefix 😀 Don't don't l’amour 123 abc_def ²word suffix"
    data['segments'][2].update(start=7, end=len(data['sources'][2]['text']) - 7)
    report = analyze(data, AnalysisOptions(min_word_length=2, stopwords=['BETA'], top_words=100))
    words = {word.word: word for word in report.words}
    assert words['café'].count == 2 and words['café'].segment_ids == [1]
    assert words['strasse'].count == 1 and words['中文'].count == 1
    assert words["don't"].count == 2 and words['l’amour'].count == 1
    assert 'beta' not in words and 'prefix' not in words and 'suffix' not in words
    assert '123' not in words and 'word' in words
    assert words['abc'].count == 1 and words['def'].count == 1


def test_numeric_hand_calculated_missingness_and_pairwise_correlation():
    report = analyze(fixture(), AnalysisOptions(numeric_fields=['x', 'y']))
    x, y = report.numeric
    assert (x.valid, x.missing, x.invalid, x.mean, x.median, x.sample_sd) == (3, 1, 0, 2, 2, 1)
    assert (y.valid, y.missing, y.invalid, y.mean, y.sample_sd) == (3, 0, 1, 4, 2)
    assert (x.minimum, x.maximum) == (1, 3)
    pair = report.correlations[0]
    assert pair.n == 3 and pair.pearson_r == pytest.approx(1)
    assert [point.case_id for point in pair.points] == [1, 2, 3]


@pytest.mark.parametrize('value', ['NaN', 'Infinity', '-inf', '1,000', '1_000', '1e151',
                                  '-1e151', '1e9999', '１２', '.', '0x10'])
def test_numeric_invalid_explicitly_counted(value):
    data = fixture()
    data['attributes'].append({'case_id': 4, 'key': 'x', 'value': value})
    x = analyze(data, AnalysisOptions(numeric_fields=['x'])).numeric[0]
    assert (x.valid, x.missing, x.invalid) == (3, 0, 1)


def test_numeric_blank_conflict_and_valid_scientific_syntax():
    data = fixture()
    data['attributes'] = [{'case_id': c, 'key': 'x', 'value': v} for c, v in [
        (1, ' +1.5e2 '), (1, '+1.5e2'), (2, ''), (2, '  '), (3, '2'), (3, '3'), (4, '.5')]]
    x = analyze(data, AnalysisOptions(numeric_fields=['x'])).numeric[0]
    assert (x.valid, x.missing, x.invalid, x.mean) == (2, 1, 1, 75.25)


@pytest.mark.parametrize('values', [['1', '1', '1'], ['1', '2', 'bad']])
def test_constant_or_under_three_pairs_return_null(values):
    data = fixture()
    for attribute in data['attributes']:
        if attribute['key'] == 'x':
            attribute['value'] = values[attribute['case_id'] - 1]
    report = analyze(data, AnalysisOptions(numeric_fields=['x', 'y']))
    assert report.correlations[0].pearson_r is None


def test_large_magnitude_finite_and_tiny_correlation_stable():
    data = fixture()
    for attribute in data['attributes']:
        if attribute['key'] in ('x', 'y') and attribute['case_id'] < 4:
            attribute['value'] = str((attribute['case_id'] - 2) *
                                     (1e150 if attribute['key'] == 'x' else 1e-150))
    report = analyze(data, AnalysisOptions(numeric_fields=['x', 'y']))
    assert report.correlations[0].pearson_r == pytest.approx(1)
    json.dumps(report.model_dump(), allow_nan=False)


@pytest.mark.parametrize('option', [dict(source_id=999), dict(case_id=999), dict(code_ids=[999]),
                                    dict(group_by='absent'), dict(numeric_fields=['absent'])])
def test_unknown_selections_rejected(option):
    with pytest.raises(ValueError, match='unknown'):
        analyze(fixture(), AnalysisOptions(**option))


@pytest.mark.parametrize(('table', 'limit'), [('segments', 20000), ('cases', 5000), ('codes', 200)])
def test_input_caps_before_computation(table, limit):
    data = fixture()
    data[table] = [data[table][0]] * (limit + 1)
    with pytest.raises(ValueError, match='smaller'):
        analyze(data, AnalysisOptions())


def test_empty_input_and_hash_ignores_unrelated_workspace_state_and_order():
    report = analyze({}, AnalysisOptions())
    assert report.segment_count == report.case_count == 0
    assert report.excerpts == report.numeric == report.pairs == []
    data = fixture()
    first = analyze(data, AnalysisOptions()).input_hash
    data['routing'] = {'unrelated': True}
    data['segments'].reverse()
    assert analyze(data, AnalysisOptions()).input_hash == first
    data['current_codings'][0]['span_end'] = 3
    assert analyze(data, AnalysisOptions()).input_hash != first


@pytest.mark.parametrize(('constant', 'limit', 'options', 'resource'), [
    ('_MAX_EVENTS', 7, {}, 'current coding events'),
    ('_MAX_TEXT', 3, {'query': 'not present'}, 'candidate segment text'),
    ('_MAX_MEMBERSHIPS', 1, {}, 'pair segment memberships'),
    ('_MAX_VOCABULARY', 1, {}, 'word vocabulary'),
    ('_MAX_OVERLAP_COMPARISONS', 1, {'cooccurrence': 'overlap'}, 'overlapping span'),
])
def test_resource_caps_fail_explicitly_before_results(monkeypatch, constant, limit, options, resource):
    monkeypatch.setattr(analysis, constant, limit)
    with pytest.raises(ValueError, match=resource):
        analyze(fixture(), AnalysisOptions(**options))


def test_word_membership_budget_counts_each_segment_once(monkeypatch):
    data = fixture()
    data['current_codings'] = []
    monkeypatch.setattr(analysis, '_MAX_MEMBERSHIPS', 1)
    data['sources'][0]['text'] = 'alpha alpha alpha'
    data['segments'][0]['end'] = len(data['sources'][0]['text'])
    report = analyze(data, AnalysisOptions(source_id=1))
    assert report.words[0].count == 3
    with pytest.raises(ValueError, match='word segment memberships'):
        analyze(data, AnalysisOptions())


def test_numeric_attribute_status_preserves_conflict_and_missing():
    report = analyze(fixture(), AnalysisOptions(group_by='group'))
    assert report.case_rows[2].attribute_status['group'] == 'conflicting'
    assert report.case_rows[2].attributes['group'] is None
    assert report.case_rows[3].attribute_status['group'] == 'missing'
    assert report.case_rows[3].attributes['group'] is None


def test_actual_dense_pair_result_limit_rejects_without_truncating():
    data = fixture()
    data['segments'] = [{'id': i, 'source_id': 1, 'start': 0, 'end': 10}
                        for i in range(1, 15)]
    data['codes'] = [{'id': i, 'name': str(i)} for i in range(1, 201)]
    data['current_codings'] = [
        dict(id=sid * 200 + code, segment_id=sid, code_id=code, span_start=0, span_end=2,
             action='assign', codebook_version_id=1)
        for sid in range(1, 15) for code in range(1, 201)]
    # 19,900 unordered pairs * 14 contributing segments = 278,600 memberships.
    with pytest.raises(ValueError, match='pair segment memberships'):
        analyze(data, AnalysisOptions())


def test_one_case_numeric_sd_and_correlation_unavailable():
    report = analyze(fixture(), AnalysisOptions(case_id=1, numeric_fields=['x', 'y']))
    assert report.numeric[0].valid == 1
    assert report.numeric[0].sample_sd is None
    assert report.correlations[0].n == 1
    assert report.correlations[0].pearson_r is None


@pytest.mark.parametrize(('constant', 'limit', 'options', 'resource'), [
    ('_MAX_ATTRIBUTES', 1, {}, 'input attributes'),
    ('_MAX_SOURCE_CASES', 1, {}, 'input source-case links'),
    ('_MAX_CASE_MEMBERSHIPS', 4, {}, 'case-segment memberships'),
    ('_MAX_ATTRIBUTE_CELLS', 11, {}, 'case attribute cells'),
    ('_MAX_FREQUENCY_OUTPUT', 20, {'group_by': 'group'}, 'frequency output'),
])
def test_link_attribute_and_frequency_budgets(monkeypatch, constant, limit, options, resource):
    monkeypatch.setattr(analysis, constant, limit)
    with pytest.raises(ValueError, match=resource):
        analyze(fixture(), AnalysisOptions(**options))


def test_actual_multilink_budget_and_smaller_case_scope_recovery():
    data = fixture()
    data['cases'] = [{'id': cid, 'name': str(cid)} for cid in range(1, 501)]
    data['source_cases'] = [{'source_id': 1, 'case_id': cid} for cid in range(1, 501)]
    data['segments'] = [{'id': sid, 'source_id': 1, 'start': 0, 'end': 4}
                        for sid in range(1, 502)]
    data['attributes'] = []
    data['current_codings'] = []
    # Just 500 links expand into 500 * 501 = 250,500 case-segment memberships.
    with pytest.raises(ValueError, match='case-segment memberships'):
        analyze(data, AnalysisOptions())
    report = analyze(data, AnalysisOptions(case_id=1))
    assert report.segment_count == 501 and report.case_count == 1
    assert report.selected_segment_ids == list(range(1, 502))


def test_frequency_budget_includes_zero_rows_not_only_positive_ids(monkeypatch):
    data = fixture()
    data['current_codings'] = []
    monkeypatch.setattr(analysis, '_MAX_FREQUENCY_OUTPUT', 6)
    assert len(analyze(data, AnalysisOptions()).frequencies) == 3
    with pytest.raises(ValueError, match='frequency output'):
        analyze(data, AnalysisOptions(group_by='group'))
