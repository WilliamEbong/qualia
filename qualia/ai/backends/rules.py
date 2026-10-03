"""Offline keyword classification using human-supplied code names/include terms."""

import re


class RulesBackend:
    name = 'rules'
    external = False

    def available(self) -> bool:
        return True

    def classify(self, segments, schema, context):
        predictions = []
        for segment in segments:
            found = []
            for code in context['codebook']:
                if code.get('status', 'active') != 'active':
                    continue
                terms = [term.strip().casefold() for term in re.split(r'[,\n]',
                         code.get('include') or code.get('name', '')) if term.strip()]
                if any(term in segment['text'].casefold() for term in terms):
                    found.append({'code_id': code['id'], 'score': 0.75,
                                  'rationale': 'Deterministic declared keyword matched.',
                                  'span_start': 0, 'span_end': len(segment['text'])})
            predictions.append({'segment_id': str(segment['id']), 'codes': found})
        return {'predictions': predictions, 'input_tokens': 0, 'output_tokens': 0,
                'cli_version': 'rules-v1'}
