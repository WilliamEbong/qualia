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
