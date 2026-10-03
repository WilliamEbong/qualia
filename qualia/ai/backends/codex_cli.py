"""Isolated Codex CLI recipe; live availability fails closed at the token-bound gate."""

import copy
import json
import os
import re
import shutil
import tempfile
from pathlib import Path

from qualia.ai.backends.process import (
    MAX_OUTPUT_BYTES,
    BackendError,
    classification_prompt,
    first_segment,
    json_object,
    run_process,
    subscription_environment,
    token_count,
)

VERIFIED_VERSION = '0.160.0'
PROVIDER_ID = 'qualia-subscription'
OPERATOR_UNAVAILABLE_REASON = (
    'Codex operator is unavailable: native Windows confinement setup/profile, provider '
    'generation limits and authentication-retry accounting remain unresolved.'
)


def operator_available():
    return False


def run_operator(project, prompt, *, model=None, max_output_tokens=8192,
                 report_path='experiments/0001.md'):
    raise BackendError('operator_unavailable')


DISABLED_FEATURES = (
    'shell_tool', 'apps', 'plugins', 'browser_use', 'browser_use_external',
    'browser_use_full_cdp_access', 'computer_use', 'in_app_browser', 'image_generation',
    'view_image', 'multi_agent', 'multi_agent_v2', 'code_mode', 'code_mode_only',
    'code_mode_host', 'hooks', 'goals', 'memories', 'sleep_tool', 'tool_suggest',
    'skill_search', 'workspace_dependencies', 'request_permissions_tool',
    'send_message_to_user_async',
)


def resolve_command():
    found = shutil.which('codex')
    if not found:
        return None
    path = Path(found).resolve()
    if os.name != 'nt' or path.suffix.lower() == '.exe':
        return [str(path)]
    wrapper = path.parent / 'node_modules/@openai/codex/bin/codex.js'
    node = shutil.which('node')
    if wrapper.is_file() and node:
        # Official wrapper supplies the bundled helper PATH; avoid .cmd/.ps1 shells.
        return [str(Path(node).resolve()), str(wrapper)]
    return None


def restricted_catalog(catalog, model):
    """Clone current genuine metadata, changing only tool capabilities for this run."""
    try:
        matches = [record for record in catalog['models'] if record.get('slug') == model]
        if len(matches) != 1:
            raise ValueError
        record = copy.deepcopy(matches[0])
        record.update(apply_patch_tool_type=None, experimental_supported_tools=[],
                      shell_type='disabled', tool_mode='direct', supports_search_tool=False)
        return {'models': [record]}
    except (KeyError, TypeError, AttributeError, ValueError):
        raise BackendError('unavailable') from None


def build_argv(command, model, schema_path, output_path, catalog_path):
    if not isinstance(model, str) or not re.fullmatch(r'gpt-[a-zA-Z0-9_.-]{1,110}', model):
        raise BackendError('invalid_model')
    argv = [*command, 'exec', '--ignore-user-config', '--strict-config', '-s', 'read-only',
            '--ephemeral', '--skip-git-repo-check', '--output-schema', str(schema_path),
            '-o', str(output_path), '-m', model, '--json']
    settings = {'web_search': 'disabled', 'model_reasoning_effort': 'low',
                'agents.enabled': False, 'tools.update_plan.enabled': False,
                'tools.experimental_request_user_input.enabled': False,
                'project_doc_max_bytes': 0, 'model_catalog_json': str(catalog_path),
                'model_provider': PROVIDER_ID, 'forced_login_method': 'chatgpt',
                f'model_providers.{PROVIDER_ID}.name': 'OpenAI',
                f'model_providers.{PROVIDER_ID}.requires_openai_auth': True,
                f'model_providers.{PROVIDER_ID}.wire_api': 'responses',
                f'model_providers.{PROVIDER_ID}.supports_websockets': False,
                f'model_providers.{PROVIDER_ID}.request_max_retries': 0,
                f'model_providers.{PROVIDER_ID}.stream_max_retries': 0}
    # Omit base_url and credential fields. The native provider chooses its official
    # ChatGPT endpoint from the existing subscription login, without token copying.
    for key, value in settings.items():
        argv.extend(('-c', key + '=' + json.dumps(value)))
    for feature in DISABLED_FEATURES:
        argv.extend(('--disable', feature))
    return [*argv, '-']


def load_catalog(model):
    """Read only the CLI's nonsecret model catalog; never config or authentication files."""
    home = Path(os.environ.get('CODEX_HOME', Path.home() / '.codex'))
    try:
        with (home / 'models_cache.json').open('rb') as stream:
            data = stream.read(8_388_609)
        if len(data) > 8_388_608:
            raise ValueError
        return restricted_catalog(json_object(data), model)
    except (OSError, ValueError, UnicodeError, RecursionError):
        raise BackendError('unavailable') from None


def _usage(data):
    inputs = outputs = 0
    seen = False
    violation = None
    for line in data.splitlines():
        if not line.strip():
            continue
        try:
            event = json_object(line)
            if event.get('type') == 'turn.completed':
                usage = event['usage']
                used_input = token_count(usage['input_tokens'])
                used_output = token_count(usage['output_tokens'])
                inputs += used_input
                outputs += used_output
                seen = True
            if event.get('type') in ('item.started', 'item.completed', 'item.updated'):
                if event['item'].get('type') not in ('agent_message', 'reasoning'):
                    violation = 'tool_call'
            if event.get('type') in ('function_call', 'custom_tool_call', 'tool_call'):
                violation = 'tool_call'
        except (ValueError, KeyError, TypeError, AttributeError, UnicodeError, RecursionError):
            violation = violation or 'invalid_response'
    return inputs, outputs, seen, violation


class CodexCLIBackend:
    name = 'codex'
    external = True
    unavailable_reason = (
        'Codex classification is unavailable: native CLI 0.160.0 has no verified provider '
        'output-token cap or verified zero-retry subscription configuration. The owner '
        'decision is pending; local byte/time limits are not a generation-token cap. '
        'No provider request will be started.'
    )

    def __init__(self, model='gpt-6-luna', *, runner=None, timeout_seconds=90,
                 max_output_bytes=MAX_OUTPUT_BYTES):
        self.model = model
        self.runner = runner or run_process
        self.timeout_seconds = timeout_seconds
        self.max_output_bytes = max_output_bytes

    def available(self):
        return False

    def classify(self, segments, schema, context):
        # No constructor/env/context switch bypasses the unresolved owner gate.
        record = first_segment(segments)
        if not self.available():
            raise BackendError('unavailable', record)
        command = resolve_command()
        if command is None:
            raise BackendError('unavailable', record)
        prompt = classification_prompt(segments, schema, context)
        environment = subscription_environment()
        model = context.get('model', self.model)
        catalog = load_catalog(model)
        version = 'unknown'
        with tempfile.TemporaryDirectory(prefix='qualia-codex-') as directory:
            root = Path(directory)
            version_cwd = root / 'version'
            version_cwd.mkdir()
            probe = self.runner([*command, '--version'], prompt='', cwd=version_cwd,
                                env=environment, timeout_seconds=10, max_output_bytes=8192)
            match = re.search(rb'\b(\d+\.\d+\.\d+)\b', probe.stdout)
            if probe.failure or probe.returncode or not match:
                raise BackendError('unavailable', record)
            version = match.group(1).decode('ascii')
            if version != VERIFIED_VERSION:
                raise BackendError('unsupported_version', record, cli_version=version)
            schema_path, output_path = root / 'schema.json', root / 'result.json'
            catalog_path = root / 'catalog.json'
            schema_path.write_text(json.dumps(schema, allow_nan=False), encoding='utf-8')
            catalog_path.write_text(json.dumps(catalog, allow_nan=False), encoding='utf-8')
            cwd = root / 'cwd'
            cwd.mkdir()
            argv = build_argv(command, model, schema_path, output_path, catalog_path)
            result = self.runner(argv, prompt=prompt, cwd=cwd, env=environment,
                                 timeout_seconds=self.timeout_seconds,
                                 max_output_bytes=self.max_output_bytes, output_path=output_path)
            inputs = outputs = 0
            seen = False
            inputs, outputs, seen, violation = _usage(result.stdout)
            error_args = {'input_tokens': inputs, 'output_tokens': outputs,
                          'cli_version': version}
            if violation:
                raise BackendError(violation, record, **error_args)
            if result.failure or result.returncode:
                raise BackendError(result.failure or 'provider_error', record, **error_args)
            try:
                with output_path.open('rb') as stream:
                    data = stream.read(self.max_output_bytes + 1)
                if len(data) > self.max_output_bytes:
                    raise BackendError('output_limit', record, **error_args)
                prediction = json_object(data)
                if (not seen or set(prediction) != {'predictions'}
                        or not isinstance(prediction['predictions'], list)):
                    raise ValueError
            except BackendError:
                raise
            except (OSError, ValueError, TypeError, UnicodeError, RecursionError):
                raise BackendError('invalid_response', record, **error_args) from None
            return {'predictions': prediction['predictions'], **error_args}
