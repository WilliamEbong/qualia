import { expect, test } from '../../web/node_modules/@playwright/test'

test.describe('Read-only static demo', () => {
  test.skip(() => !process.env.QUALIA_DEMO_URL, 'Set QUALIA_DEMO_URL to the built static preview')
  test('all screens remain local and mutation controls stay disabled', async ({ page }) => {
    const requests: string[] = []
    page.on('request', request => requests.push(request.url()))
    await page.goto(process.env.QUALIA_DEMO_URL!)
    await expect(page.getByText('Read-only public snapshot', { exact: false }).first()).toBeVisible()
    for (const view of ['Home', 'Workspace', 'Codebook', 'Memos', 'Retrieval', 'Matrix', 'Analysis', 'Review', 'Evaluation', 'Experiments']) {
      await page.getByRole('button', { name: new RegExp(`^${view}(?: \\(|$)`) }).click()
      await expect(page.locator('main')).toBeVisible()
    }
    await page.getByRole('button', { name: 'Workspace', exact: true }).click()
    await expect(page.locator('.code-shortcut').first()).toBeDisabled()
    const before = await page.locator('.code-mark').count()
    await page.locator('.segment').first().focus()
    await page.keyboard.press('1')
    await page.keyboard.press('a')
    await page.keyboard.press('r')
    expect(await page.locator('.code-mark').count()).toBe(before)
    expect(requests.filter(url => new URL(url).pathname.includes('/api/'))).toEqual([])
    await page.setViewportSize({ width: 375, height: 812 })
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true)
    await page.getByRole('button', { name: 'Home', exact: true }).click()
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true)
  })
})
