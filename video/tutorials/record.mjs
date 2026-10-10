// Records one tutorial from the real local app: node tutorials/record.mjs 02
// Starts a private Qualia server on a scratch QUALIA_HOME, seeds it with the CLI, drives a headless
// browser through the tutorial's steps and writes public/recordings/NN.webm plus NN.json (step timeline).
import {execFileSync, spawn} from 'node:child_process';
import fs from 'node:fs';
import net from 'node:net';
import os from 'node:os';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
import {chromium} from '../../web/node_modules/playwright-core/index.mjs';

const VIDEO = path.resolve(import.meta.dirname, '..');
const REPO = path.resolve(VIDEO, '..');
const VIEW = {width: 1600, height: 900};
const STEP_TIMEOUT = 30_000;
const LEAD = 1000;

const id = process.argv[2];
const file = id && fs.readdirSync(path.join(VIDEO, 'tutorials/scripts')).find((f) => f.startsWith(`${id}-`));
if (!file) throw new Error('Usage: node tutorials/record.mjs <NN> (a script in tutorials/scripts/)');
const tutorial = await import(pathToFileURL(path.join(VIDEO, 'tutorials/scripts', file)).href);

// Never touch real projects: the workspace must be a fresh folder under the system temp directory.
const scratch = path.resolve(process.env.QUALIA_TUTORIAL_SCRATCH ?? '');
if (!process.env.QUALIA_TUTORIAL_SCRATCH || !scratch.toLowerCase().startsWith(os.tmpdir().toLowerCase())
    || scratch.toLowerCase().startsWith(REPO.toLowerCase())) {
  throw new Error('Set QUALIA_TUTORIAL_SCRATCH to a scratch folder under the system temp directory.');
}
const stamp = `${id}-${Date.now()}`;
const home = path.join(scratch, 'homes', stamp);
const work = path.join(scratch, 'work', stamp);
fs.mkdirSync(home, {recursive: true});
fs.mkdirSync(work, {recursive: true});

const port = await new Promise((resolve) => {
  const probe = net.createServer().listen(0, '127.0.0.1', () => {
    const {port: free} = probe.address();
    probe.close(() => resolve(free));
  });
});
const env = {...process.env, QUALIA_HOME: home, QUALIA_PORT: String(port)};
const python = path.join(REPO, '.venv/Scripts/python.exe');
const cli = (...args) => execFileSync(python, ['-m', 'qualia.cli', ...args.map(String)], {env, cwd: work, encoding: 'utf8'});
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
// Minimum time each step stays on screen, so its caption can be read while the action plays.
const hold = (caption) => Math.min(8000, Math.max(3800, caption.length * 70)) * (tutorial.pace ?? 1);
const withTimeout = (promise, label, ms = STEP_TIMEOUT) => Promise.race([
  promise, sleep(ms).then(() => { throw new Error(`${label} timed out after ${ms} ms`); }),
]);

// A visible pointer for the recording (headless captures have none). CSSOM only, so the app's CSP allows it.
const CURSOR = `(() => {
  const add = () => {
    const c = document.createElement('div');
    Object.assign(c.style, {position: 'fixed', left: '-50px', top: '-50px', width: '24px', height: '24px',
      margin: '-12px 0 0 -12px', borderRadius: '50%', border: '2px solid #1D1C1A', boxSizing: 'border-box',
      background: 'rgba(185, 138, 62, 0.35)', pointerEvents: 'none', zIndex: '2147483647'});
    document.body.appendChild(c);
    const at = window.__tutorialMouse;
    if (at) Object.assign(c.style, {left: at.x + 'px', top: at.y + 'px'});
    addEventListener('mousemove', (e) => { c.style.left = e.clientX + 'px'; c.style.top = e.clientY + 'px'; }, true);
    addEventListener('mousedown', () => { c.style.transform = 'scale(0.7)'; }, true);
    addEventListener('mouseup', () => { c.style.transform = 'scale(1)'; }, true);
  };
  if (document.body) add(); else addEventListener('DOMContentLoaded', add);
})()`;

let server;
let browser;
try {
  console.log(`recorder pid ${process.pid} · home ${home} · port ${port}`);
  await tutorial.seed?.({cli, work, home});

  const log = fs.openSync(path.join(work, 'server.log'), 'w');
  server = spawn(python, ['-m', 'qualia.cli', 'open', '--no-browser'], {env, cwd: work, stdio: ['ignore', log, log]});
  console.log(`server pid ${server.pid}`);
  const base = `http://127.0.0.1:${port}`;
  for (let i = 0; ; i++) {
    if (await fetch(base).then((r) => r.ok, () => false)) break;
    if (i > 120) throw new Error('Server did not start; see server.log');
    await sleep(500);
  }

  browser = await chromium.launch();
  const context = await browser.newContext({viewport: VIEW, deviceScaleFactor: 1, colorScheme: 'light', acceptDownloads: true});
  await context.addInitScript(CURSOR);
  const page = await context.newPage();
  page.setDefaultTimeout(15_000);
  await page.goto(base + (tutorial.start ?? '/'));
  await page.waitForLoadState('networkidle');
  await tutorial.ready?.(page);

  let mouse = {x: VIEW.width / 2, y: VIEW.height / 2};
  let step;
  // Clicks land on the control's centre; hovers point from just left of it so the pointer never hides its text.
  const moveTo = async (locator, point = false) => {
    await locator.scrollIntoViewIfNeeded();
    const box = await locator.boundingBox();
    if (!box) throw new Error(`Not visible: ${locator}`);
    const x = point ? (box.x > 30 ? box.x - 16 : box.x + 4) : box.x + box.width / 2;
    const to = {x: Math.round(x), y: Math.round(box.y + Math.min(box.height / 2, 18))};
    await page.mouse.move(to.x, to.y, {steps: Math.max(8, Math.round(Math.hypot(to.x - mouse.x, to.y - mouse.y) / 22))});
    await page.evaluate((at) => { window.__tutorialMouse = at; }, to);
    mouse = to;
    await sleep(250);
  };
  const ui = {
    page, cli, work, home, sleep,
    hover: (locator) => moveTo(locator, true),
    click: async (locator) => { await moveTo(locator); await locator.click(); await sleep(450); },
    type: async (locator, text) => {
      await moveTo(locator); await locator.click(); await locator.pressSequentially(text, {delay: 45}); await sleep(300);
    },
    fill: async (locator, text) => { await moveTo(locator); await locator.click(); await locator.fill(text); await sleep(400); },
    select: async (locator, value) => { await moveTo(locator); await locator.selectOption(value); await sleep(450); },
    press: async (key) => { await page.keyboard.press(key); await sleep(550); },
    upload: async (locator, files) => { await locator.setInputFiles(files); await sleep(450); },
    // Drag across `phrase` inside `locator` like a reader selecting words.
    selectText: async (locator, phrase) => {
      await locator.scrollIntoViewIfNeeded();
      const at = await locator.evaluate((el, words) => {
        const walk = document.createTreeWalker(el, NodeFilter.SHOW_TEXT);
        for (let node = walk.nextNode(); node; node = walk.nextNode()) {
          const i = node.textContent.indexOf(words);
          if (i < 0) continue;
          const range = document.createRange();
          range.setStart(node, i);
          range.setEnd(node, i + words.length);
          const rects = range.getClientRects();
          const [a, b] = [rects[0], rects[rects.length - 1]];
          return {x1: a.left + 1, y1: a.top + a.height / 2, x2: b.right - 1, y2: b.top + b.height / 2};
        }
        return null;
      }, phrase);
      if (!at) throw new Error(`Text not found: ${phrase}`);
      const steps = (to) => Math.max(8, Math.round(Math.hypot(to.x - mouse.x, to.y - mouse.y) / 22));
      await page.mouse.move(at.x1, at.y1, {steps: steps({x: at.x1, y: at.y1})});
      await sleep(250);
      // A drag that starts inside an old selection would move text instead of selecting it.
      await page.evaluate(() => window.getSelection()?.removeAllRanges());
      await page.mouse.down();
      await page.mouse.move(at.x2 - 2, at.y2, {steps: 24});
      await sleep(200);
      await page.mouse.move(at.x2, at.y2);
      await sleep(200);
      await page.mouse.up();
      mouse = {x: at.x2, y: at.y2};
      await page.evaluate((p) => { window.__tutorialMouse = p; }, mouse);
      await sleep(500);
    },
    zoom: async (locator) => {
      const box = await locator.boundingBox();
      if (box) step.zoom = {x: box.x, y: box.y, width: box.width, height: box.height};
    },
  };

  // JPEG frames with browser timestamps, encoded below: sharper text than the built-in webm and exact step timing.
  const steps = [];
  const frames = [];
  const frameDir = path.join(work, 'frames');
  fs.mkdirSync(frameDir);
  await page.screencast.start({size: VIEW, quality: 92, onFrame: ({data, timestamp}) => {
    const name = `${String(frames.length).padStart(6, '0')}.jpg`;
    fs.writeFileSync(path.join(frameDir, name), data);
    frames.push({name, t: timestamp});
  }});
  const t0 = Date.now();
  let cursor = 0;
  for (const [i, s] of tutorial.steps.entries()) {
    step = {caption: s.caption, demo: Boolean(s.demo), zoom: null, card: s.card ?? null, startMs: cursor, endMs: cursor};
    if (s.card) {
      // Cards stay up long enough to skim their text as well as the caption (capped; viewers can pause).
      const text = [s.card.title, ...s.card.lines, s.card.command ?? ''].join(' ').length;
      step.cardMs = Math.min(15000, hold(s.caption) + 1500 + text * 25);
    } else {
      await sleep(LEAD);
      try {
        await withTimeout(Promise.resolve(s.do?.(ui)), `Step ${i + 1}`, s.timeout);
        // An app error on screen means the step did not do what its caption says.
        const alerts = (await page.locator('[role=alert]:visible').allInnerTexts()).filter((t) => t.trim());
        if (alerts.length && !s.allowAlert) throw new Error(`App error shown: ${alerts.join(' | ')}`);
      } catch (error) {
        await page.screenshot({path: path.join(work, `failed-step-${i + 1}.png`)}).catch(() => {});
        throw new Error(`Step ${i + 1} "${s.caption}": ${error.message}`);
      }
      await sleep(Math.max(0, hold(s.caption) - (Date.now() - t0 - cursor)));
      cursor = step.endMs = Date.now() - t0;
      // Long waits (a `fast` step) play back faster so the step lasts about as long as its caption needs.
      if (s.fast) step.rate = Math.max(1, Math.round(((step.endMs - step.startMs) / (hold(s.caption) + 1500)) * 10) / 10);
    }
    steps.push(step);
    console.log(`${i + 1}/${tutorial.steps.length} ${s.caption}`);
  }
  await page.screencast.stop();
  const tEnd = t0 + cursor + 500;

  // Each frame stays on screen until the next one arrives (the browser only sends frames when pixels change).
  const list = ['ffconcat version 1.0'];
  frames.forEach((f, i) => {
    const until = Math.min(frames[i + 1]?.t ?? tEnd, tEnd);
    const from = i === 0 ? t0 : f.t;
    if (until > from) list.push(`file 'frames/${f.name}'`, `duration ${((until - from) / 1000).toFixed(4)}`);
  });
  list.push(`file 'frames/${frames.at(-1).name}'`);
  fs.writeFileSync(path.join(work, 'frames.ffconcat'), list.join('\n') + '\n');
  const out = path.join(VIDEO, 'public/recordings');
  fs.mkdirSync(out, {recursive: true});
  execFileSync('ffmpeg', ['-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', 'frames.ffconcat', '-vf', 'fps=30,format=yuv420p', '-t', ((tEnd - t0) / 1000).toFixed(3),
    '-c:v', 'libx264', '-crf', '14', '-preset', 'medium', path.join(out, `${id}.mp4`)], {cwd: work});
  fs.rmSync(frameDir, {recursive: true});
  fs.writeFileSync(path.join(out, `${id}.json`), JSON.stringify({id, video: `recordings/${id}.mp4`, steps}, null, 2) + '\n');
  console.log(`wrote public/recordings/${id}.mp4 and ${id}.json (${(cursor / 1000).toFixed(1)} s, ${frames.length} frames, first at +${frames[0].t - t0} ms)`);
} finally {
  await browser?.close().catch(() => {});
  // Stop only the server this run started (and its children).
  if (server?.pid) spawn('taskkill', ['/PID', String(server.pid), '/T', '/F'], {stdio: 'ignore'});
}
