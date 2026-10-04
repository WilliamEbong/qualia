/**
 * Opt-in mutation test for a fresh, authorized AnnoMI demo and an already running local server.
 * Required: QUALIA_E2E_URL, QUALIA_E2E_PROJECT (slug), QUALIA_E2E_HOME,
 * QUALIA_E2E_PYTHON (absolute interpreter path). The server must use that same home.
 * Optional: QUALIA_E2E_OUTPUT_DIR (absolute screenshot directory).
 * Seed and commit the demo first; do not use a project whose fake_mode is already "all".
 * Run from the repository root, without installing another dependency:
 * node web/node_modules/@playwright/test/cli.js test tests/e2e/mvp.spec.ts --workers=1 --retries=0 --output=web/test-results
 * This spec intentionally uses the existing web package because tests/ is outside web/.
 */
import { expect, test, type Page } from '../../web/node_modules/@playwright/test'
import { execFile } from 'node:child_process'
import { createHash } from 'node:crypto'
import { access, mkdir, readFile, realpath } from 'node:fs/promises'
import { isAbsolute, join, resolve } from 'node:path'
import { promisify } from 'node:util'

const execute = promisify(execFile)
const urlSetting = process.env.QUALIA_E2E_URL
const projectSetting = process.env.QUALIA_E2E_PROJECT

type Evidence = {
  sources: Array<{ id: number; content_hash: string }>
  segments: Array<{ id: number }>
  codebook_versions: Array<{ id: number; hash: string }>
  coding_events: Array<{
    id: number; segment_id: number; codebook_version_id: number; actor: string
    actor_type: string; pipeline_version: string; action: string; suggestion_id: number | null
    backend: string | null; model: string | null; cli_version: string | null; prompt_hash: string
  }>
  experiments: Array<{ id: number; decision: string; commit_hash: string; tag: string }>
  pipeline_version: string
}

function identity(value: Evidence): string {
  // Compare identities without copying research text into assertion diagnostics or artifacts.
  return createHash('sha256').update(JSON.stringify({
    sources: value.sources.map(row => [row.id, row.content_hash]),
    segments: value.segments.map(row => row.id),
    versions: value.codebook_versions.map(row => [row.id, row.hash]),
    events: value.coding_events.map(row => row.id),
    pipeline: value.pipeline_version,
  })).digest('hex')
}

async function screenshot(page: Page, filename: string): Promise<void> {
  const directory = process.env.QUALIA_E2E_OUTPUT_DIR
  if (!directory) return
  expect(isAbsolute(directory), 'Screenshot directory must be explicitly absolute').toBe(true)
  await mkdir(directory, { recursive: true })
  await page.screenshot({ path: join(directory, filename), fullPage: true })
}

test.describe('Explicitly authorized MVP workspace', () => {
test.skip(() => !urlSetting || !projectSetting, 'Set both QUALIA_E2E_URL and QUALIA_E2E_PROJECT to authorize this mutation test')
test('five keyboard codes, reviews, measured KEEP and reproducibility export', async ({ page }) => {
  test.setTimeout(300_000)
  const homeSetting = process.env.QUALIA_E2E_HOME
  const python = process.env.QUALIA_E2E_PYTHON
  expect(homeSetting && isAbsolute(homeSetting), 'Set an absolute QUALIA_E2E_HOME for the authorized server and CLI').toBeTruthy()
  expect(python && isAbsolute(python), 'Set an absolute QUALIA_E2E_PYTHON interpreter').toBeTruthy()
  expect(projectSetting).toMatch(/^[a-z0-9]+(?:-[a-z0-9]+)*$/)
  const slug = projectSetting!
  const destination = new URL(urlSetting!)
  expect(['127.0.0.1', 'localhost']).toContain(destination.hostname)
  expect(destination.protocol).toBe('http:')
  expect(destination.username + destination.password).toBe('')
  destination.searchParams.set('project', slug)
  const home = await realpath(homeSetting!)
  const project = await realpath(join(home, 'projects', slug))
  expect(project).toBe(resolve(home, 'projects', slug))
  await access(python!)
  await access(join(project, '.annomi-demo.json'))
  const routing = JSON.parse(await readFile(join(project, 'config/routing.yaml'), 'utf8'))
  expect(routing.allow_external, 'This test only runs the offline fake backend').toBe(false)
  expect(routing.escalate_below ?? null, 'Use a fresh demo without an escalation override').toBeNull()
  expect(routing.fake_mode ?? 'first', 'Use a fresh demo; the measured all-codes gain has already been applied').toBe('first')

  const env = { ...process.env, QUALIA_HOME: home }
  const repository = resolve(__dirname, '../..')
  const cli = (args: string[], timeout = 30_000) => execute(python!, ['-m', 'qualia.cli', ...args], {
    cwd: repository, env, timeout, windowsHide: true, maxBuffer: 64 * 1024 * 1024,
  })
  const git = (args: string[]) => execute('git', ['-C', project, ...args], {
    cwd: repository, timeout: 15_000, windowsHide: true, maxBuffer: 1024 * 1024,
  })
  expect((await git(['status', '--porcelain'])).stdout.trim(), 'Commit the seeded demo before this test').toBe('')
  const local = JSON.parse((await cli(['export', '--project', slug, '--format', 'json', '--bundle', 'reproducibility'])).stdout) as Evidence
  const apiPath = `/api/projects/${encodeURIComponent(slug)}`
  const initialResponse = page.waitForResponse(response => new URL(response.url()).pathname === apiPath && response.request().method() === 'GET')
  await page.goto(destination.toString())
  const initial = await initialResponse
  expect(initial.ok()).toBe(true)
  const remote = await initial.json() as Evidence & { project: { slug: string } }
  expect(remote.project.slug).toBe(slug)
  expect(identity(remote), 'Server and explicit CLI home must refer to the same seeded workspace').toBe(identity(local))
  await expect(page.getByLabel('Local project', { exact: true })).toHaveValue(slug)
  await page.getByRole('button', { name: 'Workspace', exact: true }).click()
  await page.getByLabel('Human actor', { exact: true }).fill('qualia-e2e')
  const segments = page.locator('.segment')
  expect(await segments.count()).toBeGreaterThanOrEqual(5)
  await segments.first().focus()
  const keyboardEventIds: number[] = []
  const codedSegmentIds = new Set<string>()
  for (let index = 0; index < 5; index++) {
    await expect(page.locator('.code-shortcut').first()).toBeEnabled()
    const activeId = await page.locator('.active-segment').getAttribute('id')
    expect(activeId).toBeTruthy()
    codedSegmentIds.add(activeId!)
    const saved = page.waitForResponse(response => new URL(response.url()).pathname === `${apiPath}/coding` && response.request().method() === 'POST')
    await page.keyboard.press('1')
    const response = await saved
    expect(response.ok()).toBe(true)
    keyboardEventIds.push((await response.json()).id)
    // A completed POST does not mean the workspace reload and busy-state update have finished.
    await expect(page.locator('.code-shortcut').first()).toBeEnabled()
    if (index < 4) {
      await page.keyboard.press('ArrowDown')
      await expect(page.locator('.active-segment')).not.toHaveAttribute('id', activeId!)
    }
  }
  expect(codedSegmentIds.size).toBe(5)
  await screenshot(page, 'mvp-five-keyboard-codes.png')

  await page.getByRole('button', { name: /^Review \(/ }).click()
  await expect(page.getByRole('heading', { name: 'Run classification', exact: true })).toBeVisible()
  await page.getByLabel(/^Backend/).selectOption('fake')
  await page.getByLabel(/^Scope/).selectOption('source')
  const classified = page.waitForResponse(response => new URL(response.url()).pathname === `${apiPath}/classify` && response.request().method() === 'POST')
  await page.getByRole('button', { name: 'Run classification', exact: true }).click()
  const classification = await classified
  expect(classification.ok()).toBe(true)
  const classificationResult = await classification.json() as { status: string; suggestion_ids: number[] }
  expect(classificationResult.status).toBe('completed')
  expect(classificationResult.suggestion_ids.length).toBeGreaterThanOrEqual(2)
  await page.locator('.suggestion').first().waitFor({ state: 'visible' })
  await expect(page.getByLabel(/^Backend/)).toBeEnabled()
  const reviewIds = classificationResult.suggestion_ids.slice(0, 2)
  for (const [index, key] of ['a', 'r'].entries()) {
    const id = reviewIds[index]
    const cards = page.locator(`.suggestion[aria-label="Suggestion ${id}"]`)
    const select = cards.first().locator('.suggestion-select')
    await select.click()
    await expect(select).toHaveAttribute('aria-pressed', 'true')
    const reviewed = page.waitForResponse(response => new URL(response.url()).pathname === `${apiPath}/review` && response.request().method() === 'POST')
    await page.keyboard.press(key)
    expect((await reviewed).ok()).toBe(true)
    await expect(cards).toHaveCount(0)
    await expect(page.getByLabel(/^Backend/)).toBeEnabled()
  }
  await screenshot(page, 'mvp-accepted-rejected.png')

  // Explicit home and fake override keep the real CLI run bound to the authorized offline fixture.
  const improved = JSON.parse((await cli(['improve', '--project', slug, '--agent', 'fake', '--budget', '1', '--backend', 'fake'], 180_000)).stdout)
  expect(improved).toHaveLength(1)
  const kept = improved[0] as Evidence['experiments'][number]
  expect(kept.decision).toBe('KEEP')
  expect(kept.tag).toMatch(/^exp-\d{4}-/)
  expect((await git(['rev-parse', kept.tag])).stdout.trim()).toBe(kept.commit_hash)
  expect((await git(['status', '--porcelain'])).stdout.trim()).toBe('')
  const report = await readFile(join(project, 'experiments', `${String(kept.id).padStart(4, '0')}.md`), 'utf8')
  expect(report).toMatch(/^# KEEP/)
  await page.reload()
  await expect(page.getByLabel('Local project', { exact: true })).toHaveValue(slug)
  await page.getByRole('button', { name: 'Experiments', exact: true }).click()
  const detail = page.getByRole('article', { name: `Experiment ${kept.id}`, exact: true })
  await expect(detail).toHaveAttribute('data-decision', 'KEEP')
  await expect(page.getByRole('table', { name: 'Experiment measurement comparison' })).toBeVisible()
  await screenshot(page, 'mvp-measured-keep.png')

  await page.getByRole('button', { name: 'Export', exact: true }).click()
  await page.getByLabel('Reproducibility bundle', { exact: true }).check()
  await expect(page.getByLabel('Include source text and excerpts', { exact: true })).not.toBeChecked()
  const downloading = page.waitForEvent('download')
  await page.getByRole('button', { name: 'Download export', exact: true }).click()
  const download = await downloading
  const stream = await download.createReadStream()
  const chunks: Buffer[] = []
  let size = 0
  for await (const chunk of stream) {
    const bytes = Buffer.from(chunk)
    size += bytes.length
    expect(size, 'Export must remain within the fixture output bound').toBeLessThanOrEqual(64 * 1024 * 1024)
    chunks.push(bytes)
  }
  const bundle = JSON.parse(Buffer.concat(chunks).toString('utf8')) as Evidence & { text_excluded: boolean; bundle: string }
  expect(bundle.bundle).toBe('reproducibility')
  expect(bundle.text_excluded).toBe(true)
  const knownSegments = new Set(bundle.segments.map(row => row.id))
  const knownVersions = new Set(bundle.codebook_versions.map(row => row.id))
  for (const event of bundle.coding_events) {
    expect(knownSegments.has(event.segment_id)).toBe(true)
    expect(knownVersions.has(event.codebook_version_id)).toBe(true)
    expect(event.actor.trim()).not.toBe('')
    expect(event.pipeline_version).toMatch(/^[a-f0-9]{64}$/)
    if (event.actor_type === 'model' || event.action === 'accept' || event.action === 'reject') {
      expect(event.backend && event.model && event.cli_version && event.prompt_hash).toBeTruthy()
    }
  }
  expect(bundle.coding_events.filter(row => keyboardEventIds.includes(row.id))).toHaveLength(5)
  expect(bundle.coding_events.some(row => row.action === 'accept' && row.suggestion_id === reviewIds[0])).toBe(true)
  expect(bundle.coding_events.some(row => row.action === 'reject' && row.suggestion_id === reviewIds[1])).toBe(true)
  expect(bundle.experiments.some(row => row.id === kept.id && row.decision === 'KEEP' && row.tag === kept.tag)).toBe(true)
})
})
