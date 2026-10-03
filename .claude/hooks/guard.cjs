/* Qualia PreToolUse protocol: https://code.claude.com/docs/en/hooks */
const fs = require('node:fs');
const path = require('node:path');
const root = path.resolve(__dirname, '../..');
const norm = value => value.replaceAll('\\', '/').toLowerCase();
const relative = value => norm(path.relative(root, path.resolve(root, value)));
const escape = value => value.replace(/[.*+?^\x24{}()|[\]\\]/g, '\\$&');
function matches(file, pattern) {
  const rule = norm(pattern);
  if (rule.endsWith('/')) return file === rule.slice(0, -1) || file.startsWith(rule);
  return new RegExp('^' + rule.split('*').map(escape).join('.*') + '$').test(file);
}
function withoutState(text) {
  const start = text.indexOf('## 10. Current state');
  const end = text.indexOf('\n## 11.', start);
  if (start < 0 || end < 0) throw new Error('Missing current-state boundaries');
  return text.slice(0, start) + text.slice(end);
}
function stateOnly(tool, input, target, mode) {
  if (mode !== 'build' || relative(target) !== 'docs/01-qualia-context.md') return false;
  const before = fs.readFileSync(path.resolve(root, target), 'utf8');
  let after;
  if (tool === 'Write' && typeof input.content === 'string') after = input.content;
  else if (tool === 'Edit' && typeof input.old_string === 'string' && input.old_string.length && typeof input.new_string === 'string') {
    const count = before.split(input.old_string).length - 1;
    if (!count || (!input.replace_all && count !== 1)) return false;
    after = input.replace_all ? before.split(input.old_string).join(input.new_string) : before.replace(input.old_string, () => input.new_string);
  } else return false;
  return withoutState(before) === withoutState(after);
}
function inspect(call, config) {
  if (!['build', 'design'].includes(config.mode)) return 'Unknown guard mode';
  const input = call.tool_input || {};
  const tool = call.tool_name;
  const patterns = config.alwaysProtected.concat(config.mode === 'design' ? config.designProtected : []);
  if (['Edit', 'Write', 'NotebookEdit'].includes(tool)) {
    const target = input.file_path || input.notebook_path;
    if (typeof target !== 'string') return 'Missing file path';
    if (patterns.some(pattern => matches(relative(target), pattern)) && !stateOnly(tool, input, target, config.mode)) {
      return 'Protected source-of-truth or design path. Record the required contract change in OWNER-NEEDED.md; continue unaffected work.';
    }
  }
  if (['Bash', 'PowerShell'].includes(tool)) {
    const command = String(input.command || '');
    if (/\bgit\b[^\r\n;&|]*\bpush\b[^\r\n;&|]*(?:--force(?:-with-lease)?\b|(?:^|\s)-f(?:\s|$))/i.test(command) ||
        /\bgit\b[^\r\n;&|]*\breset\s+--hard\b|\bgit\b[^\r\n;&|]*\bclean\b|\bgit\b[^\r\n;&|]*\bbranch\s+-D(?:\s|$)/.test(command) ||
        /\brm\s+-[a-z]*r[a-z]*f|\brm\s+-[a-z]*f[a-z]*r|\bgh\s+repo\s+(?:edit|delete)\b|\bRemove-Item\b[^\r\n;]*-Recurse\b/i.test(command)) {
      return 'Destructive command requires owner action; preserve the working tree and record the request.';
    }
    // Explicit shell targets only; this is not an arbitrary-program sandbox.
    // The design pre-commit gate provides a separate staged-path control.
    const normalized = norm(command);
    const mentions = patterns.some(pattern => normalized.includes(norm(pattern).split('*')[0]));
    const mutates = /(?:^|\s)(?:Set-Content|Add-Content|Out-File|Remove-Item|Move-Item|Copy-Item|New-Item|tee|cp|mv|rm|sed|perl|python|node|ruby|git\s+(?:restore|checkout|apply))\b|(?:^|[^<])>{1,2}|\.(?:write|write_text|write_bytes|writeFile|unlink|rename)\b/i.test(command);
    if (mentions && mutates) return 'Shell mutation references a protected path. Use an allowed file edit or record the contract change for the owner.';
  }
  return null;
}
function deny(reason) {
  process.stdout.write(JSON.stringify({hookSpecificOutput: {hookEventName: 'PreToolUse', permissionDecision: 'deny', permissionDecisionReason: reason}}));
}
try {
  const config = JSON.parse(fs.readFileSync(path.join(__dirname, 'guard-config.json'), 'utf8').replace(/^\uFEFF/, ''));
  const call = JSON.parse(fs.readFileSync(0, 'utf8').replace(/^\uFEFF/, ''));
  const reason = inspect(call, config);
  if (reason) deny(reason);
} catch {
  deny('Qualia guard could not validate the request. Diagnose its input without weakening the detector.');
}
