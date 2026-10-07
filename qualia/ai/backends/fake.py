"""Deterministic synthetic classifier. It never reads gold labels or benchmarks."""


class FakeBackend:
    name = 'fake'
    external = False

    def available(self) -> bool:
        return True

    def classify(self, segments, schema, context):
        codes = [code for code in context['codebook'] if code.get('status', 'active') == 'active']
        mode = context.get('fake_mode', 'first')
        if mode not in ('first', 'all', 'none'):
            raise ValueError('invalid fake mode')
        selected = codes if mode == 'all' else codes[:1] if mode == 'first' else []
        return {'predictions': [{'segment_id': str(segment['id']), 'codes': [
            {'code_id': code['id'], 'score': 0.6, 'rationale': 'Deterministic synthetic fixture.',
             'span_start': 0, 'span_end': len(segment['text'])} for code in selected
        ]} for segment in segments], 'input_tokens': 0, 'output_tokens': 0, 'cli_version': 'fake-v1'}

    def propose(self, segments, schema, context):
        evidence = [str(segments[0]['id'])]
        if context.get('refine'):
            proposals = [{**{key: code[key] for key in ('name', 'definition', 'include', 'exclude',
                                                         'examples_pos', 'examples_neg')},
                          'kind': 'revise_code', 'target_code_id': code['id'],
                          'definition': (code['definition'] + ' Applies when the speaker describes '
                                         'it directly.').strip(),
                          'rationale': 'Deterministic synthetic fixture.',
                          'evidence_segment_ids': evidence} for code in context['refine']]
        else:
            names = {code['name'].casefold() for code in context['codebook']}
            number = next(n for n in range(1, len(names) + 2) if f'proposed code {n}' not in names)
            proposals = [{'kind': 'new_code', 'target_code_id': None, 'name': f'Proposed code {number}',
                          'definition': 'Synthetic draft code for offline demonstration.',
                          'include': '', 'exclude': '', 'examples_pos': [segments[0]['text'][:60]],
                          'examples_neg': [], 'rationale': 'Deterministic synthetic fixture.',
                          'evidence_segment_ids': evidence}]
        return {'proposals': proposals, 'input_tokens': 0, 'output_tokens': 0, 'cli_version': 'fake-v1'}
