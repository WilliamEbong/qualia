"""Deterministic descriptive analysis of a visible, current workspace snapshot."""

import hashlib
import json
import math
import re
import statistics
from collections import Counter, defaultdict
from itertools import combinations

from qualia.core.analysis_models import AnalysisOptions, AnalysisReport

_TABLES = ('sources', 'segments', 'cases', 'attributes', 'source_cases', 'codes',
           'codebook_versions', 'current_codings')
_DECIMAL = re.compile(r'[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?')
_MAX_EVENTS = 100000
_MAX_TEXT = 20000000
_MAX_MEMBERSHIPS = 250000
_MAX_VOCABULARY = 100000
_MAX_OVERLAP_COMPARISONS = 2000000
_MAX_ATTRIBUTES = 50000
_MAX_SOURCE_CASES = 100000
_MAX_CASE_MEMBERSHIPS = 250000
_MAX_ATTRIBUTE_CELLS = 250000
_MAX_FREQUENCY_OUTPUT = 250000


def _budget(exceeded, resource):
    if exceeded:
        raise ValueError(f'analysis {resource} budget exceeded; select a smaller source/case scope')


def _canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':'),
                      allow_nan=False)


def _tokens(text):
    """Unicode letters with single internal straight/curly apostrophes, casefolded."""
    text = text.casefold()
    token = []
    for index, char in enumerate(text):
        if char.isalpha() or (char in "'’" and token and index + 1 < len(text)
                              and text[index + 1].isalpha()):
            token.append(char)
        elif token:
            yield ''.join(token)
            token = []
    if token:
        yield ''.join(token)


def _attribute(values):
    present = {value.strip() for value in values if value.strip()}
    if len(present) > 1:
        return 'conflicting', None
    if not present:
        return 'missing', None
    return 'value', next(iter(present))


def _number(value):
    if value is None or not _DECIMAL.fullmatch(value):
        return None
    number = float(value)
    return number if math.isfinite(number) and abs(number) <= 1e150 else None


def analyze(data: dict, options: AnalysisOptions) -> AnalysisReport:
    """Analyze current assign/accept events; never mutate inputs or access resources."""
    for table, maximum in (('segments', 20000), ('cases', 5000), ('codes', 200)):
        if len(data.get(table, [])) > maximum:
            raise ValueError(f'analysis supports at most {maximum} {table}; import a smaller project')
    _budget(len(data.get('current_codings', [])) > _MAX_EVENTS, 'current coding events')
    _budget(len(data.get('attributes', [])) > _MAX_ATTRIBUTES, 'input attributes')
    _budget(len(data.get('source_cases', [])) > _MAX_SOURCE_CASES, 'input source-case links')
    tables = {name: list(data.get(name, [])) for name in _TABLES}
    identity = {name: sorted(rows, key=_canonical) for name, rows in tables.items()}
    identity['pipeline_version'] = data.get('pipeline_version', '')
    input_hash = hashlib.sha256(_canonical(identity).encode('utf-8')).hexdigest()
    sources = {row['id']: row for row in tables['sources']}
    cases = {row['id']: row for row in tables['cases']}
    codes = {row['id']: row for row in tables['codes']}
    segments = {row['id']: row for row in tables['segments']}
    versions = {row['id']: row for row in tables['codebook_versions']}
    for table, index in (('sources', sources), ('cases', cases), ('codes', codes),
                         ('segments', segments), ('codebook_versions', versions)):
        if len(index) != len(tables[table]):
            raise ValueError(f'duplicate {table} IDs')
    for value, index, label in ((options.source_id, sources, 'source'),
                                (options.case_id, cases, 'case')):
        if value is not None and value not in index:
            raise ValueError(f'unknown {label} ID')
    if any(code not in codes for code in options.code_ids):
        raise ValueError('unknown code ID')
    attribute_values = defaultdict(list)
    attribute_names = set()
    for row in tables['attributes']:
        if row.get('case_id') in cases:
            attribute_names.add(row['key'])
            attribute_values[row['case_id'], row['key']].append(row['value'])
    fields = set(options.numeric_fields) | ({options.group_by} if options.group_by else set())
    if fields - attribute_names:
        raise ValueError('unknown case attribute selection')
    links = defaultdict(set)
    for link in tables['source_cases']:
        if link['source_id'] not in sources or link['case_id'] not in cases:
            raise ValueError('unknown source/case link')
        if options.case_id is None or link['case_id'] == options.case_id:
            links[link['source_id']].add(link['case_id'])
    events = defaultdict(list)
    for event in tables['current_codings']:
        if event['action'] not in ('assign', 'accept'):
            continue
        if (event['segment_id'] not in segments or event['code_id'] not in codes
                or event['codebook_version_id'] not in versions):
            raise ValueError('unknown current coding reference')
        events[event['segment_id']].append(event)
    texts, selected, text_size = {}, set(), 0
    requested = set(options.code_ids)
    for sid, segment in segments.items():
        if segment['source_id'] not in sources:
            raise ValueError('unknown segment source')
        source = sources[segment['source_id']]
        present = {event['code_id'] for event in events[sid]}
        if options.source_id is not None and source['id'] != options.source_id:
            continue
        if options.case_id is not None and options.case_id not in links[source['id']]:
            continue
        if requested and not (requested <= present if options.code_match == 'all'
                              else requested & present):
            continue
        # Bound text work before slicing/casefolding and before a literal query narrows it.
        text_size += segment['end'] - segment['start']
        _budget(text_size > _MAX_TEXT, 'candidate segment text')
        text = source['text'][segment['start']:segment['end']]
        if options.query.casefold() not in text.casefold():
            continue
        selected.add(sid)
        texts[sid] = text
    eligible_cases = set()
    case_segments = defaultdict(set)
    presence = defaultdict(set)
    code_versions = defaultdict(set)
    selected_events = []
    case_memberships = 0
    for sid in sorted(selected):
        for cid in links[segments[sid]['source_id']]:
            case_memberships += 1
            _budget(case_memberships > _MAX_CASE_MEMBERSHIPS, 'case-segment memberships')
            eligible_cases.add(cid)
            case_segments[cid].add(sid)
        for event in events[sid]:
            presence[event['code_id']].add(sid)
            code_versions[event['code_id'], sid].add(event['codebook_version_id'])
            selected_events.append(event)
    warnings = []
    if any(len(links[segments[sid]['source_id']]) > 1 for sid in selected):
        warnings.append('Sources linked to multiple cases contribute to each linked case/group; '
                        'groups are not independent observations.')

    frequency_output = 0

    def frequencies(segment_ids, case_ids):
        nonlocal frequency_output
        rows = []
        for code_id in sorted(codes):
            carrying = presence[code_id] & segment_ids
            carrying_cases = {cid for cid in case_ids if case_segments[cid] & carrying}
            frozen = set().union(*(code_versions[code_id, sid] for sid in carrying))
            # Include the row itself: thousands of all-zero groups must also be bounded.
            frequency_output += 1 + len(carrying) + len(carrying_cases) + len(frozen)
            _budget(frequency_output > _MAX_FREQUENCY_OUTPUT, 'frequency output rows/contributor IDs')
            rows.append(dict(code_id=code_id, name=codes[code_id]['name'],
                segment_count=len(carrying), case_count=len(carrying_cases),
                segment_percent=100 * len(carrying) / len(segment_ids) if segment_ids else 0,
                case_percent=100 * len(carrying_cases) / len(case_ids) if case_ids else 0,
                segment_ids=sorted(carrying), case_ids=sorted(carrying_cases),
                codebook_version_ids=sorted(frozen)))
        return rows

    _budget(len(eligible_cases) * len(attribute_names) > _MAX_ATTRIBUTE_CELLS,
            'case attribute cells')
    resolved = {(cid, field): _attribute(attribute_values[cid, field])
                for cid in eligible_cases for field in attribute_names}
    group_cases = defaultdict(set)
    if options.group_by:
        for cid in eligible_cases:
            status, value = resolved[cid, options.group_by]
            group_cases[status, value].add(cid)
    groups = []
    for (status, value), ids in sorted(group_cases.items(), key=lambda item: (
            item[0][0], item[0][1] or '')):
        sids = set().union(*(case_segments[cid] for cid in ids))
        groups.append(dict(value=value if status == 'value' else status.title(), status=status,
                           case_ids=sorted(ids), segment_ids=sorted(sids),
                           frequencies=frequencies(sids, ids)))
    pairs, pair_memberships, overlap_comparisons = [], 0, 0
    spans = defaultdict(list)
    for event in selected_events:
        spans[event['segment_id'], event['code_id']].append(
            (event['span_start'], event['span_end']))
    for left, right in combinations(sorted(codes), 2):
        intersection = presence[left] & presence[right]
        union = presence[left] | presence[right]
        contributing = intersection
        if options.cooccurrence == 'overlap':
            contributing = set()
            for sid in sorted(intersection):
                found = False
                for a in spans[sid, left]:
                    for b in spans[sid, right]:
                        overlap_comparisons += 1
                        _budget(overlap_comparisons > _MAX_OVERLAP_COMPARISONS,
                                'overlapping span comparisons')
                        if max(a[0], b[0]) < min(a[1], b[1]):
                            contributing.add(sid)
                            found = True
                            break
                    if found:
                        break
        pair_memberships += len(contributing)
        _budget(pair_memberships > _MAX_MEMBERSHIPS, 'pair segment memberships')
        pairs.append(dict(left_code_id=left, right_code_id=right, count=len(contributing),
                          union_count=len(union), jaccard=len(intersection) / len(union) if union else None,
                          segment_ids=sorted(contributing)))
    counts, word_segments, word_memberships = Counter(), defaultdict(set), 0
    stopwords = {word.casefold() for word in options.stopwords}
    for sid in sorted(selected):
        for word in _tokens(texts[sid]):
            if len(word) >= options.min_word_length and word not in stopwords:
                _budget(word not in counts and len(counts) >= _MAX_VOCABULARY, 'word vocabulary')
                if sid not in word_segments[word]:
                    word_memberships += 1
                    _budget(word_memberships > _MAX_MEMBERSHIPS, 'word segment memberships')
                counts[word] += 1
                word_segments[word].add(sid)
    words = [dict(word=word, count=count, segment_count=len(word_segments[word]),
                  segment_ids=sorted(word_segments[word])) for word, count in
             sorted(counts.items(), key=lambda item: (-item[1], item[0]))[:options.top_words]]

    def finite_stat(label, operation):
        try:
            result = float(operation())
            if math.isfinite(result):
                return result
        except (ValueError, OverflowError, ZeroDivisionError):
            pass
        warnings.append(f'{label}: result unavailable because finite arithmetic could not be established.')
        return None

    numeric, numeric_values = [], {}
    for field in options.numeric_fields:
        values, missing, invalid = {}, 0, 0
        for cid in sorted(eligible_cases):
            status, raw = resolved[cid, field]
            value = _number(raw) if status == 'value' else None
            if status == 'missing':
                missing += 1
            elif value is None:
                invalid += 1
            else:
                values[cid] = value
        sequence = list(values.values())
        numeric_values[field] = values
        if invalid:
            warnings.append(f'{field}: {invalid} invalid/conflicting case values excluded from numeric summaries.')
        numeric.append(dict(field=field, valid=len(values), missing=missing, invalid=invalid,
            mean=finite_stat(f'{field} mean', lambda: statistics.mean(sequence)) if sequence else None,
            median=finite_stat(f'{field} median', lambda: statistics.median(sequence)) if sequence else None,
            sample_sd=finite_stat(f'{field} sample SD', lambda: statistics.stdev(sequence)) if len(sequence) > 1 else None,
            minimum=min(sequence) if sequence else None, maximum=max(sequence) if sequence else None,
            values=[dict(case_id=cid, value=value) for cid, value in values.items()]))
    correlations = []
    for x_field, y_field in combinations(options.numeric_fields, 2):
        x, y = numeric_values[x_field], numeric_values[y_field]
        ids = sorted(x.keys() & y.keys())
        points = [dict(case_id=cid, x=x[cid], y=y[cid]) for cid in ids]
        r = None
        if len(ids) >= 3 and len({x[cid] for cid in ids}) > 1 and len({y[cid] for cid in ids}) > 1:
            x_scale, y_scale = max(abs(x[cid]) for cid in ids), max(abs(y[cid]) for cid in ids)
            r = finite_stat(f'{x_field}/{y_field} Pearson r', lambda: statistics.correlation(
                [x[cid] / x_scale for cid in ids], [y[cid] / y_scale for cid in ids]))
        correlations.append(dict(x_field=x_field, y_field=y_field, n=len(ids), pearson_r=r,
                                 points=points))
    frozen_ids = sorted({event['codebook_version_id'] for event in selected_events})
    return AnalysisReport(
        options=options, input_hash=input_hash, selected_segment_ids=sorted(selected),
        methods=[
            'Filters intersect. Text matching is literal and case-insensitive using Unicode casefold.',
            'Current assign/accept coding only. Code names are current display names, not historical names. '
            'Event IDs and frozen codebook versions/hashes retain the computation provenance.',
            'Frequency is distinct segment/case presence, not spans. Overall percentages use selected '
            'segment_count/case_count; group percentages use group segment_ids/case_ids lengths. Empty denominators yield 0%.',
            'Co-occurrence counts each segment once per unordered pair. Overlap requires a positive-length '
            'intersection; touching boundaries do not overlap. Jaccard always uses same-segment presence '
            'intersection/union, regardless of overlap mode. Association is not causation.',
            'Words are casefolded Unicode alphabetic characters with single internal straight/curly '
            'apostrophes; other characters delimit tokens. No Unicode normalization, stemming or hidden '
            'stopwords. Minimum length counts code points including apostrophes; explicit stopwords are '
            'casefolded exact matches. Ties sort lexically. Each selected segment is tokenized once.',
            'Attributes are case-only: trim whitespace, collapse equal values, ignore blanks; distinct '
            'nonblank values conflict. Source attributes are not inherited.',
            'Numeric fields are explicitly selected, not inferred as measurements. ASCII decimal/scientific '
            'syntax only, finite absolute values <=1e150. Missing and invalid/conflicting counts are separate. '
            'Sample SD uses n-1 (n<2: null). Pearson uses pairwise-complete cases, with each coordinate '
            'rescaled by its maximum magnitude; fewer than three pairs or constant coordinates yield null. '
            'No significance or causal inference.',
            'Only displayed excerpts/top words are capped; selected IDs, frequency/pair/word contributors '
            'and event/version identities remain complete for the corresponding result.',
            'Resource limits fail explicitly without truncated counts: 20,000 input segments, 5,000 '
            'cases, 200 codes, 100,000 current coding rows; 20 million candidate text code points '
            'after source/case/code filters but before text query; 250,000 pair segment memberships '
            'and word segment memberships, 100,000 distinct words, two million span comparisons.',
            'Additional allocation limits: 50,000 input attributes, 100,000 input source-case links; '
            '250,000 eligible case-segment memberships, 250,000 resolved case-by-attribute cells, '
            'and 250,000 aggregate frequency rows plus segment/case/version contributor IDs across '
            'all groups and the overall frequency table. Exceeding a limit rejects the report.',
        ], warnings=warnings, source_count=len({segments[sid]['source_id'] for sid in selected}),
        segment_count=len(selected), case_count=len(eligible_cases),
        coded_segment_count=sum(bool(events[sid]) for sid in selected),
        coding_event_ids=sorted({event['id'] for event in selected_events}),
        codebook_version_ids=frozen_ids, codebook_hashes={str(v): versions[v]['hash'] for v in frozen_ids},
        pipeline_version=data.get('pipeline_version', ''),
        frequencies=frequencies(selected, eligible_cases), groups=groups, pairs=pairs, words=words,
        numeric=numeric, correlations=correlations, excerpt_total=len(selected),
        excerpts=[dict(segment_id=sid, source_id=segments[sid]['source_id'],
                       source_name=sources[segments[sid]['source_id']]['name'],
                       speaker=segments[sid].get('speaker'), text=texts[sid],
                       coding_event_ids=sorted({e['id'] for e in events[sid]}))
                  for sid in sorted(selected)[:options.excerpt_limit]],
        case_rows=[dict(case_id=cid, name=cases[cid]['name'],
                        attributes={field: resolved[cid, field][1] for field in sorted(attribute_names)},
                        attribute_status={field: resolved[cid, field][0] for field in sorted(attribute_names)},
                        code_counts={str(code): len(case_segments[cid] & presence[code]) for code in sorted(codes)})
                   for cid in sorted(eligible_cases)],
    )
