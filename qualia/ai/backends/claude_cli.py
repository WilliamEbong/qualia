"""Claude subscription CLI adapter; no API keys, tools or stored session transcripts."""

import json
import os
import re
import shutil
import stat
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

VERIFIED_VERSION = '2.1.284'
CLASSIFICATION_UNAVAILABLE_REASON = (
    'Claude classification is unavailable pending an explicit CLI request-accounting decision. '
    'Version 2.1.284 can send multiple model requests per invocation despite zero HTTP retries; '
    'one invocation reservation does not satisfy one egress record per HTTP request.'
)
OPERATOR_UNAVAILABLE_REASON = (
    'Claude operator is unavailable until native file confinement and per-model-request '
    'egress accounting are verified. Classification availability is independent.'
)


def operator_available():
    return False


def operator_settings(project, report_path):
    """Generate explicit protected-file denies; dontAsk alone permits workspace reads."""
    project = Path(project).absolute()
    if not re.fullmatch(r'experiments/[0-9]{4}\.md', report_path):
        raise BackendError('invalid_input')
    if project.is_symlink() or project.is_junction() or not project.is_dir():
        raise BackendError('scope')
    if (project / report_path).exists():
        raise BackendError('scope')
    proposal_dir = 'experiments/proposals/' + Path(report_path).stem
    allowed = ['config/prompts/**', 'config/routing.yaml', 'config/segmentation.yaml',
               report_path, proposal_dir + '/**']
    deny = ['Read(./.git/**)', 'Edit(./.git/**)', 'Read(./.env*)', 'Edit(./.env*)',
            'Read(./project.db*)', 'Edit(./project.db*)']
    for path in project.rglob('*'):
        info = path.lstat()
        if (path.is_symlink() or path.is_junction()
                or getattr(info, 'st_file_attributes', 0) & getattr(stat, 'FILE_ATTRIBUTE_REPARSE_POINT', 0x400)
                or (path.is_file() and info.st_nlink > 1)):
            raise BackendError('scope')
        relative = path.relative_to(project).as_posix()
        if any(character in relative for character in '*?[]'):
            raise BackendError('scope')
        if path.is_file():
            mutable = (relative.startswith('config/prompts/')
                       or relative in ('config/routing.yaml', 'config/segmentation.yaml'))
            if (path.name.lower().startswith(('.env', 'codebook.'))
                    or any(suffix.lower().startswith('.db') for suffix in path.suffixes)):
                mutable = False
            if not mutable:
                deny.append(f'Edit(./{relative})')
            if not mutable and relative != 'IMPROVEMENT.md':
                deny.append(f'Read(./{relative})')
    return {'permissions': {'allow': [f'Edit(./{path})' for path in allowed], 'deny': deny,
                            'defaultMode': 'dontAsk', 'disableBypassPermissionsMode': 'disable',
                            'disableAutoMode': 'disable'}}


def build_operator_argv(command, model, settings_path):
    if not isinstance(model, str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.:/-]{0,119}', model):
        raise BackendError('invalid_model')
    return [*command, '-p', '--output-format', 'json', '--model', model,
            '--tools', 'Read,Edit,Write', '--restricted', '--safe-mode',
            '--permission-mode', 'dontAsk', '--permission-prompts', 'none',
            '--strict-mcp-config', '--setting-sources', '', '--disallowedTools', 'mcp__*',
            '--disable-slash-commands', '--no-chrome', '--no-session-persistence',
            '--max-turns', '4', '--settings', str(settings_path)]


def run_operator(project, prompt, *, model=None, max_output_tokens=8192,
                 report_path='experiments/0001.md'):
    if not operator_available():
        raise BackendError('operator_unavailable')
    return _run_operator(project, prompt, model=model, max_output_tokens=max_output_tokens,
                         report_path=report_path)


def _run_operator(project, prompt, *, model=None, max_output_tokens=8192,
                  report_path='experiments/0001.md', runner=run_process):
    command = resolve_command()
    if command is None:
        raise BackendError('unavailable')
    if (not isinstance(prompt, str) or not prompt.strip() or len(prompt.encode('utf-8')) > 1_048_576
            or type(max_output_tokens) is not int or not 0 < max_output_tokens <= 8192):
        raise BackendError('input_limit')
    settings = operator_settings(project, report_path)
    environment = subscription_environment()
    environment.update(CLAUDE_CODE_MAX_OUTPUT_TOKENS=str(max_output_tokens),
                       CLAUDE_CODE_MAX_RETRIES='0', MAX_STRUCTURED_OUTPUT_RETRIES='1',
                       CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC='1')
    with tempfile.TemporaryDirectory(prefix='qualia-operator-') as directory:
        temporary = Path(directory)
        probe = runner([*command, '--version'], prompt='', cwd=temporary, env=environment,
                       timeout_seconds=10, max_output_bytes=8192)
        match = re.search(rb'\b(\d+\.\d+\.\d+(?:[-.][a-zA-Z0-9]+)?)\b', probe.stdout)
        if probe.failure or probe.returncode or not match or match.group(1).decode() != VERIFIED_VERSION:
            raise BackendError('unsupported_version')
        settings_path = temporary / 'settings.json'
        settings_path.write_text(json.dumps(settings), encoding='utf-8')
        argv = build_operator_argv(command, model or 'sonnet', settings_path)
        task = (prompt + '\nWrite your report to ' + report_path
                + '. Return only JSON {"hypothesis":"your tested implementation hypothesis"}. '
                  'Qualia determines KEEP/REVERT, not the operator.')
        result = runner(argv, prompt=task, cwd=Path(project), env=environment,
                        timeout_seconds=90, max_output_bytes=MAX_OUTPUT_BYTES)
    inputs = outputs = 0
    try:
        envelope = json_object(result.stdout)
        inputs, outputs = _usage(envelope)
        metadata = {'input_tokens': inputs, 'output_tokens': outputs, 'cli_version': VERIFIED_VERSION}
        if result.failure or result.returncode or envelope.get('is_error'):
            raise BackendError(result.failure or 'provider_error', **metadata)
        if envelope.get('permission_denials'):
            raise BackendError('scope', **metadata)
        if (not isinstance(envelope.get('usage'), dict)
                or not {'input_tokens', 'output_tokens'} <= envelope['usage'].keys()):
            raise ValueError
        value = json_object(envelope['result'])
        if (set(value) != {'hypothesis'} or not isinstance(value['hypothesis'], str)
                or not 1 <= len(value['hypothesis'].strip()) <= 4000):
            raise ValueError
    except BackendError:
        raise
    except (KeyError, ValueError, TypeError, UnicodeError, RecursionError):
        raise BackendError('invalid_response', input_tokens=inputs, output_tokens=outputs,
                           cli_version=VERIFIED_VERSION) from None
    return {**value, **metadata}


def resolve_command():
    """Resolve native/npm installations without sending prompts through a shell."""
    found = shutil.which('claude')
    if not found:
        return None
    path = Path(found).resolve()
    if os.name != 'nt' or path.suffix.lower() == '.exe':
        return [str(path)]
    native = path.parent / 'node_modules/@anthropic-ai/claude-code/bin/claude.exe'
    if native.is_file():
        return [str(native)]
    return None


def build_argv(command, model, schema):
    if not isinstance(model, str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.:/-]{0,119}', model):
        raise BackendError('invalid_model')
    return [*command, '-p', '--output-format', 'json', '--json-schema',
            json.dumps(schema, allow_nan=False), '--model', model, '--max-turns', '2',
            '--no-session-persistence', '--tools', '', '--disallowedTools', 'mcp__*',
            '--strict-mcp-config', '--setting-sources', '', '--safe-mode',
            '--disable-slash-commands', '--no-chrome', '--permission-mode', 'dontAsk',
            '--permission-prompts', 'none']


def _usage(envelope):
    usage = envelope.get('usage', {})
    if not isinstance(usage, dict):
        raise ValueError('invalid usage')
    inputs = sum(token_count(usage.get(key, 0)) for key in
                 ('input_tokens', 'cache_read_input_tokens', 'cache_creation_input_tokens'))
    return inputs, token_count(usage.get('output_tokens', 0))


class ClaudeCLIBackend:
    name = 'claude'
    external = True

    def __init__(self, model='haiku', *, runner=None, timeout_seconds=90,
                 max_output_bytes=MAX_OUTPUT_BYTES):
        self.model = model
        self.runner = runner or run_process
        self.timeout_seconds = timeout_seconds
        self.max_output_bytes = max_output_bytes

    @property
    def unavailable_reason(self):
        return CLASSIFICATION_UNAVAILABLE_REASON

    def available(self):
        return False

    def classify(self, segments, schema, context):
        if not self.available():
            raise BackendError('unavailable', first_segment(segments))
        return self._classify(segments, schema, context)

    def _classify(self, segments, schema, context):
        """Testable dispatch behind the public request-accounting gate."""
        record = first_segment(segments)
        command = resolve_command()
        if command is None:
            raise BackendError('unavailable', record)
        prompt = classification_prompt(segments, schema, context)
        max_tokens = context.get('max_output_tokens', 8192)
        if type(max_tokens) is not int or not 0 < max_tokens <= 8192:
            raise BackendError('input_limit', record)
        environment = subscription_environment()
        environment.update(CLAUDE_CODE_MAX_OUTPUT_TOKENS=str(max_tokens),
                           CLAUDE_CODE_MAX_RETRIES='0', MAX_STRUCTURED_OUTPUT_RETRIES='1',
                           CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC='1')
        version = 'unknown'
        with tempfile.TemporaryDirectory(prefix='qualia-claude-') as directory:
            root = Path(directory)
            version_cwd = root / 'version'
            version_cwd.mkdir()
            probe = self.runner([*command, '--version'], prompt='', cwd=version_cwd,
                                env=environment, timeout_seconds=10, max_output_bytes=8192)
            match = re.search(rb'\b(\d+\.\d+\.\d+(?:[-.][a-zA-Z0-9]+)?)\b', probe.stdout)
            if probe.failure or probe.returncode or not match:
                raise BackendError('unavailable', record)
            version = match.group(1).decode('ascii')
            # These additive isolation switches were verified on this release.
            if version != VERIFIED_VERSION:
                raise BackendError('unsupported_version', record, cli_version=version)
            cwd = root / 'cwd'
            cwd.mkdir()
            try:
                argv = build_argv(command, context.get('model', self.model), schema)
            except (TypeError, ValueError):
                raise BackendError('invalid_input', record, cli_version=version) from None
            result = self.runner(argv, prompt=prompt, cwd=cwd, env=environment,
                                 timeout_seconds=self.timeout_seconds,
                                 max_output_bytes=self.max_output_bytes)
        inputs = outputs = 0
        envelope = {}
        try:
            envelope = json_object(result.stdout)
            inputs, outputs = _usage(envelope)
        except (ValueError, UnicodeError, TypeError, RecursionError):
            raise BackendError(result.failure or 'invalid_response', record,
                               cli_version=version) from None
        error_args = {'input_tokens': inputs, 'output_tokens': outputs, 'cli_version': version}
        if result.failure:
            raise BackendError(result.failure, record, **error_args)
        if envelope.get('permission_denials'):
            raise BackendError('tool_call', record, **error_args)
        if result.returncode or envelope.get('is_error') is True:
            # Inspect only to categorize; never echo provider errors, bodies or stderr.
            text = str(envelope.get('result', '')).lower()
            code = 'quota' if any(word in text for word in ('quota', 'limit', 'rate')) else 'provider_error'
            raise BackendError(code, record, **error_args)
        try:
            if not isinstance(envelope.get('usage'), dict):
                raise ValueError
            if not {'input_tokens', 'output_tokens'} <= envelope['usage'].keys():
                raise ValueError
            prediction = envelope.get('structured_output')
            if prediction is None:
                prediction = json_object(envelope.get('result', ''))
            if (not isinstance(prediction, dict) or set(prediction) != {'predictions'}
                    or not isinstance(prediction['predictions'], list)):
                raise ValueError
        except (ValueError, TypeError, UnicodeError, RecursionError):
            raise BackendError('invalid_response', record, **error_args) from None
        return {'predictions': prediction['predictions'], **error_args}
