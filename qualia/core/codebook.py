"""Pure validation for explicitly requested human draft-codebook edits."""


def validate_code(values: dict, codes: list[dict], code_id: int | None = None) -> dict:
    allowed = {'parent_id', 'name', 'status', 'definition', 'include', 'exclude',
               'examples_pos', 'examples_neg'}
    if not values or set(values) - allowed:
        raise ValueError('invalid code fields')
    existing = {code['id']: code for code in codes}
    if code_id is not None and code_id not in existing:
        raise ValueError(f'code {code_id} not found')
    if code_id is None and 'name' not in values:
        raise ValueError('code name is required')
    for field in ('name', 'definition', 'include', 'exclude', 'status'):
        if field in values and not isinstance(values[field], str):
            raise ValueError(f'code {field} must be text')
    if 'name' in values and not values['name'].strip():
        raise ValueError('code name must not be empty')
    if 'status' in values and values['status'] not in ('active', 'archived'):
        raise ValueError('code status must be active or archived')
    for field in ('examples_pos', 'examples_neg'):
        if field in values and (not isinstance(values[field], list)
                                or any(not isinstance(item, str) for item in values[field])):
            raise ValueError(f'code {field} must be a list of strings')
    parent = values.get('parent_id', existing.get(code_id, {}).get('parent_id'))
    if parent is not None and (type(parent) is not int or parent not in existing):
        raise ValueError(f'parent code {parent} not found')
    seen = {code_id} if code_id is not None else set()
    while parent is not None:
        if parent in seen:
            raise ValueError('code hierarchy would contain a cycle')
        seen.add(parent)
        parent = existing[parent]['parent_id']
    return dict(values)
