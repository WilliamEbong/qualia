"""Read-only analysis snapshots and explicit, inert research exports."""

import csv
import hashlib
import io
import json
from pathlib import Path

from qualia.core.analysis_models import AnalysisOptions, AnalysisReport
from qualia.io.exporters import _csv_cell
from qualia.workspace import pipeline_hash

TABLES = ('sources', 'segments', 'cases', 'attributes', 'source_cases', 'codes',
          'codebook_versions', 'current_codings')


def read_analysis(db, project, options: AnalysisOptions) -> AnalysisReport:
    from qualia.eval.analysis import analyze

    project = Path(project).resolve()
    config = project/'config'
    if config.is_symlink() or config.is_junction():
        raise ValueError('analysis configuration must not contain links')
    for file in config.rglob('*'):
        if (file.is_symlink() or file.is_junction()
                or (file.is_file() and file.stat().st_nlink != 1)):
            raise ValueError('analysis configuration must not contain links')
    with db.reading():
        before = pipeline_hash(project)
        data = {table: db.rows(f'SELECT * FROM {table} ORDER BY '
                              + ('source_id,case_id' if table == 'source_cases' else 'id'))
                for table in TABLES}
        data['pipeline_version'] = before
        if pipeline_hash(project) != before:
            raise ValueError('configuration changed during analysis; retry')
    return analyze(data, options)


def _json(value):
    return json.dumps(value, ensure_ascii=False, allow_nan=False, sort_keys=True, indent=2)+'\n'


def _dictionary(report):
    columns = {
        'case_id': {'kind': 'case_id'},
        'case_name': {'kind': 'case_name', 'escaped_column': 'case_name_escaped'},
        'case_name_escaped': {'kind': 'escape_flag', 'for': 'case_name'},
    }
    for frequency in sorted(report.frequencies, key=lambda row: row.code_id):
        columns[f'code_{frequency.code_id}'] = {
            'kind': 'code_count', 'code_id': frequency.code_id, 'name': frequency.name,
            'unit': 'distinct selected segments linked to this case',
        }
    fields = {key for row in report.case_rows for key in row.attributes}
    fields.update(key for row in report.case_rows for key in row.attribute_status)
    fields.update(report.options.numeric_fields)
    if report.options.group_by:
        fields.add(report.options.group_by)
    for field in sorted(fields):
        column = 'attr_'+hashlib.sha256(field.encode('utf-8')).hexdigest()
        columns[column] = {'kind': 'attribute', 'field': field,
                           'status_column': column+'_status', 'escaped_column': column+'_escaped'}
        columns[column+'_status'] = {'kind': 'attribute_status', 'for': column,
                                    'values': ['value', 'missing', 'conflicting']}
        columns[column+'_escaped'] = {'kind': 'escape_flag', 'for': column}
    return columns


def _metadata(report, columns):
    return {
        'format_version': 1, 'text_excluded': True, 'attribute_values_included': True,
        'privacy_note': 'Case names, attributes and query criteria may be sensitive. '
                        'No-text export is not anonymization.',
        'options': report.options.model_dump(), 'input_hash': report.input_hash,
        'pipeline_version': report.pipeline_version,
        'column_dictionary': columns,
        'csv_escaping': 'A flag of 1 means exactly one leading apostrophe was added for '
                        'spreadsheet safety. Remove it only when that flag is 1.',
        'numeric_method': 'Explicit finite ASCII decimal/scientific values with abs <= 1e150; '
                          'sample SD uses n-1; pairwise Pearson requires n>=3 and nonconstant data.',
    }


def _escaped(value):
    text = '' if value is None else str(value)
    safe = _csv_cell(text)
    return safe, int(safe != text)


def _csv(report, columns):
    stream = io.StringIO(newline='')
    writer = csv.DictWriter(stream, fieldnames=list(columns), lineterminator='\n')
    writer.writeheader()
    attributes = [(column, info) for column, info in columns.items() if info['kind'] == 'attribute']
    for case in sorted(report.case_rows, key=lambda row: row.case_id):
        name, name_escaped = _escaped(case.name)
        row = {'case_id': case.case_id, 'case_name': name, 'case_name_escaped': name_escaped}
        for frequency in report.frequencies:
            row[f'code_{frequency.code_id}'] = case.code_counts.get(str(frequency.code_id), 0)
        for column, info in attributes:
            value, escaped = _escaped(case.attributes.get(info['field']))
            row[column] = value
            row[info['escaped_column']] = escaped
            row[info['status_column']] = case.attribute_status.get(info['field'], 'missing')
        writer.writerow(row)
    return stream.getvalue()


PYTHON_STARTER = '''#!/usr/bin/env python3
"""Python 3.10+ standard library. Run: python qualia-analysis.py qualia-analysis.csv
Local descriptive analysis only. Does not import Qualia or run supplied code.
Case metadata can be sensitive; the absence of transcripts does not anonymize it.
"""
import csv
import json
import math
import re
import statistics
import sys

METADATA = json.loads(__METADATA__)
NUMBER = re.compile(r"[+-]?(?:[0-9]+(?:\\.[0-9]*)?|\\.[0-9]+)(?:[eE][+-]?[0-9]+)?")

def numeric(row, info):
    status = row[info['status_column']]
    if status == 'missing':
        return 'missing', None
    if status != 'value':
        return 'invalid', None
    raw = row[info['column']]
    if row[info['escaped_column']] == '1':
        if not raw.startswith("'"):
            raise ValueError('Invalid CSV escape flag')
        raw = raw[1:]
    raw = raw.strip()
    if not raw:
        return 'missing', None
    if not NUMBER.fullmatch(raw):
        return 'invalid', None
    value = float(raw)
    if not math.isfinite(value) or abs(value) > 1e150:
        return 'invalid', None
    return 'valid', value

def summary(field, classified):
    values = [value for status, value in classified if status == 'valid']
    return dict(field=field, valid=len(values),
        missing=sum(status == 'missing' for status, _ in classified),
        invalid=sum(status == 'invalid' for status, _ in classified),
        mean=statistics.mean(values) if values else None,
        median=statistics.median(values) if values else None,
        sample_sd=statistics.stdev(values) if len(values) > 1 else None,
        minimum=min(values) if values else None, maximum=max(values) if values else None)

def pearson(points):
    if len(points) < 3:
        return None
    x, y = zip(*points)
    if len(set(x)) < 2 or len(set(y)) < 2:
        return None
    xscale, yscale = max(map(abs, x)), max(map(abs, y))
    return max(-1., min(1., statistics.correlation(
        [value/xscale for value in x], [value/yscale for value in y])))

def main():
    with open(sys.argv[1] if len(sys.argv) > 1 else 'qualia-analysis.csv',
              encoding='utf-8-sig', newline='') as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames != list(METADATA['column_dictionary']):
            raise ValueError('CSV columns do not match the embedded dictionary')
        rows = list(reader)
    attributes = {info['field']: dict(info, column=column)
                  for column, info in METADATA['column_dictionary'].items()
                  if info['kind'] == 'attribute'}
    fields = METADATA['options']['numeric_fields']
    values = {field: [numeric(row, attributes[field]) for row in rows] for field in fields}
    prevalence = [dict(code_id=info['code_id'],
        case_count=sum(int(row[column]) > 0 for row in rows),
        case_percent=100*sum(int(row[column]) > 0 for row in rows)/len(rows) if rows else 0)
        for column, info in METADATA['column_dictionary'].items() if info['kind'] == 'code_count']
    correlations = []
    for index, left in enumerate(fields):
        for right in fields[index+1:]:
            points = [(a[1], b[1]) for a, b in zip(values[left], values[right])
                      if a[0] == b[0] == 'valid']
            correlations.append(dict(x_field=left, y_field=right, n=len(points),
                                     pearson_r=pearson(points)))
    result = dict(case_count=len(rows), code_prevalence=prevalence,
        numeric=[summary(field, values[field]) for field in fields], correlations=correlations)
    print(json.dumps(result, ensure_ascii=False, allow_nan=False, sort_keys=True))

if __name__ == '__main__':
    main()
'''


R_STARTER = '''# Run explicitly: Rscript qualia-analysis.R qualia-analysis.csv
# Base R only; no packages, network, or evaluation of imported strings.
# Case metadata can be sensitive. No-text is not anonymization.
__METADATA_COMMENTS__
args <- commandArgs(trailingOnly = TRUE)
path <- if (length(args)) args[[1]] else "qualia-analysis.csv"
data <- read.csv(path, colClasses = "character", check.names = FALSE,
                 na.strings = character(), fileEncoding = "UTF-8", strip.white = FALSE)
expected <- __COLUMNS__
if (!identical(names(data), expected)) stop("CSV columns do not match the embedded dictionary")
numeric_columns <- __NUMERIC__
code_columns <- __CODES__
decode_numeric <- function(column) {
    status <- data[[paste0(column, "_status")]]
    raw <- data[[column]]
    escaped <- data[[paste0(column, "_escaped")]] == "1"
    if (any(escaped & !startsWith(raw, "'"))) stop("Invalid CSV escape flag")
    raw[escaped] <- substring(raw[escaped], 2)
    raw <- trimws(raw, whitespace = "[\\\\h\\\\v]")
    missing <- status == "missing" | (status == "value" & raw == "")
    syntax <- grepl("^[+-]?(?:[0-9]+(?:\\\\.[0-9]*)?|\\\\.[0-9]+)(?:[eE][+-]?[0-9]+)?$", raw, perl = TRUE)
    value <- suppressWarnings(as.numeric(raw))
    valid <- status == "value" & syntax & is.finite(value) & abs(value) <= 1e150
    valid[is.na(valid)] <- FALSE
    value[!valid] <- NA_real_
    list(value = value, missing = missing, valid = valid)
}
values <- setNames(lapply(numeric_columns, decode_numeric), numeric_columns)
numeric_summary <- lapply(numeric_columns, function(column) {
    item <- values[[column]]
    x <- item$value[item$valid]
    list(column = column, valid = length(x), missing = sum(item$missing),
         invalid = nrow(data) - length(x) - sum(item$missing),
         mean = if (length(x)) mean(x) else NA_real_,
         median = if (length(x)) median(x) else NA_real_,
         sample_sd = if (length(x) >= 2) sd(x) else NA_real_,
         minimum = if (length(x)) min(x) else NA_real_,
         maximum = if (length(x)) max(x) else NA_real_)
})
prevalence <- lapply(code_columns, function(column) {
    count <- sum(as.numeric(data[[column]]) > 0)
    list(column = column, case_count = count,
         case_percent = if (nrow(data)) 100 * count/nrow(data) else 0)
})
correlations <- list()
if (length(numeric_columns) >= 2) {
    pairs <- combn(numeric_columns, 2, simplify = FALSE)
    correlations <- lapply(pairs, function(pair) {
        x <- values[[pair[[1]]]]$value
        y <- values[[pair[[2]]]]$value
        keep <- is.finite(x) & is.finite(y)
        x <- x[keep]; y <- y[keep]
        r <- NA_real_
        if (length(x) >= 3 && length(unique(x)) > 1 && length(unique(y)) > 1) {
            r <- cor(x/max(abs(x)), y/max(abs(y)), method = "pearson")
        }
        list(x_column = pair[[1]], y_column = pair[[2]], n = length(x), pearson_r = r)
    })
}
print(list(case_count = nrow(data), code_prevalence = prevalence,
           numeric = numeric_summary, correlations = correlations))
'''


def _r_vector(values):
    values = list(values)
    return 'c('+', '.join(json.dumps(value) for value in values)+')' if values else 'character()'


def export_analysis(report: AnalysisReport, format: str) -> dict:
    if format not in ('json', 'csv', 'python', 'r'):
        raise ValueError('unsupported analysis export format')
    columns = _dictionary(report)
    metadata = _metadata(report, columns)
    if format == 'json':
        redacted = report.model_dump()
        redacted.pop('words')
        redacted['excerpts'] = [{key: value for key, value in row.items()
                                 if key not in ('text', 'speaker', 'source_name')}
                                for row in redacted['excerpts']]
        content, extension, media = _json({**metadata, 'report': redacted}), 'json', 'application/json'
    elif format == 'csv':
        content, extension, media = _csv(report, columns), 'csv', 'text/csv'
    elif format == 'python':
        # repr quotes one JSON string literal; metadata is never interpolated as code.
        content = PYTHON_STARTER.replace('__METADATA__', repr(json.dumps(metadata, ensure_ascii=True)))
        extension, media = 'py', 'text/x-python'
    else:
        attributes = {info['field']: column for column, info in columns.items()
                      if info['kind'] == 'attribute'}
        comments = '\n'.join('# '+line for line in json.dumps(metadata, ensure_ascii=True, indent=2).splitlines())
        content = R_STARTER.replace('__METADATA_COMMENTS__', comments).replace(
            '__COLUMNS__', _r_vector(columns)).replace('__NUMERIC__', _r_vector(
                attributes[field] for field in report.options.numeric_fields)).replace(
            '__CODES__', _r_vector(column for column, info in columns.items()
                                  if info['kind'] == 'code_count'))
        extension, media = 'R', 'text/plain'
    return {'filename': f'qualia-analysis.{extension}', 'media_type': media, 'content': content}
