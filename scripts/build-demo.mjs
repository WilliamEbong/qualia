import { existsSync, mkdirSync, readFileSync, writeFileSync, unlinkSync } from 'node:fs'
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
import { spawnSync } from 'node:child_process'

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..')
const base = process.argv[2] ?? '/qualia/'
if (!/^\/(?:[a-zA-Z0-9_-]+\/)*$/.test(base)) throw new Error('Demo base must be a relative site directory ending with a slash.')
const source = resolve(root, 'demo/snapshot.json')
const target = resolve(root, 'web/public/snapshot.json')
const prior = existsSync(target) ? readFileSync(target) : null
mkdirSync(dirname(target), { recursive: true })
try {
  writeFileSync(target, readFileSync(source))
  for (const args of [
    [resolve(root, 'web/node_modules/typescript/bin/tsc'), '--noEmit'],
    [resolve(root, 'web/node_modules/vite/bin/vite.js'), 'build', '--outDir', 'dist-demo', '--base', base],
  ]) {
    const run = spawnSync(process.execPath, args,
      { cwd: resolve(root, 'web'), stdio: 'inherit', env: { ...process.env, VITE_DEMO: '1' } })
    if (run.error) throw run.error
    if (run.status !== 0) throw new Error('Static demo build failed.')
  }
} finally {
  if (prior) writeFileSync(target, prior)
  else if (existsSync(target)) unlinkSync(target)
}
