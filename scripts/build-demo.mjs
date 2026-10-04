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
const sitemapTarget = resolve(root, 'web/public/sitemap.xml')
const priorSitemap = existsSync(sitemapTarget) ? readFileSync(sitemapTarget) : null
mkdirSync(dirname(target), { recursive: true })
try {
  writeFileSync(target, readFileSync(source))
  if (process.env.PUBLIC_SITE_URL) {
    const site = new URL(process.env.PUBLIC_SITE_URL)
    if (site.protocol !== 'https:' || site.username || site.password || site.search || site.hash) {
      throw new Error('Public site URL must be a plain HTTPS deployment URL.')
    }
    const address = (site.toString().replace(/\/$/, '') + '/').replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;')
    writeFileSync(sitemapTarget, `<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><url><loc>${address}</loc></url></urlset>\n`)
  }
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
  if (priorSitemap) writeFileSync(sitemapTarget, priorSitemap)
  else if (existsSync(sitemapTarget)) unlinkSync(sitemapTarget)
}
