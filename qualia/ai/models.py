"""Model catalog and task defaults: strength for interpretive work, economy for high volume.

Descriptors cite Anthropic's published API prices (October 2026; subscription usage scales
similarly) and the Codex CLI catalog's own wording. Projects override a default per task in
routing.yaml `tasks`, and any exact model ID can be entered to pin a version.
"""

CATALOG = {
    'claude': [
        {'id': 'haiku', 'label': 'Claude Haiku 4.5',
         'description': 'Fastest and lightest on your plan. Good for high-volume classification '
                        'with clear code definitions.'},
        {'id': 'sonnet', 'label': 'Claude Sonnet 5.5',
         'description': 'Balanced speed and judgment, about twice Haiku\'s usage. Try it when Haiku '
                        'misses nuance.'},
        {'id': 'opus', 'label': 'Claude Opus 5.5',
         'description': 'Strong reasoning at about four times Haiku\'s usage. Default for codebook '
                        'proposals, uncertain passages and improvement experiments.'},
        {'id': 'fable', 'label': 'Claude Fable 5.1',
         'description': 'Anthropic\'s most capable and most expensive model, about ten times Haiku. '
                        'Use for the hardest interpretive work in small batches.'},
    ],
    'codex': [
        {'id': 'gpt-6-luna', 'label': 'GPT-6-Luna',
         'description': 'Fast and affordable model for easier tasks. Default for high-volume '
                        'classification.'},
        {'id': 'gpt-6.1-sol', 'label': 'GPT-6.1-Sol',
         'description': 'Latest workhorse model with balanced cost. Default for codebook proposals.'},
        {'id': 'gpt-6-astra', 'label': 'GPT-6-Astra',
         'description': 'Frontier intelligence for the most demanding work; uses the most quota. '
                        'Default for uncertain passages and improvement experiments.'},
    ],
    'jev': [
        {'id': 'jev-1.13.0', 'label': 'Jev 1.13',
         'description': 'Yes/no decision model that returns probabilities. Very cheap: about $1 per '
                        '12,000 short passages with 7 codes.'},
    ],
    'rules': [{'id': 'rules-v1', 'label': 'Keyword rules',
               'description': 'Offline keyword matching on inclusion terms. Free and transparent.'}],
    'fake': [{'id': 'fake-v1', 'label': 'Offline demonstration',
              'description': 'Deterministic synthetic output for practice. Not a real model.'}],
}

# Rare, interpretive tasks get stronger models; high-volume classification gets economical ones.
TASK_DEFAULTS = {
    'classification': {'claude': 'haiku', 'codex': 'gpt-6-luna'},
    'escalation': {'claude': 'opus', 'codex': 'gpt-6-astra'},
    'proposal': {'claude': 'opus', 'codex': 'gpt-6.1-sol'},
}


def default_model(task: str, backend: str) -> str:
    """The built-in default for a task on a backend (projects may override in routing.yaml)."""
    if backend in TASK_DEFAULTS.get(task, {}):
        return TASK_DEFAULTS[task][backend]
    choices = CATALOG.get(backend)
    return choices[0]['id'] if choices else f'{backend}-v1'
