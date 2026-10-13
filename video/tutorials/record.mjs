// Records one tutorial from the real local app: node tutorials/record.mjs 02
// Starts a private Qualia server on a scratch QUALIA_HOME, seeds it with the CLI, drives a headless
// browser through the tutorial's steps and writes public/recordings/NN.mp4 plus NN.json: the step timeline and
// every on-screen action with its position, which the composition uses to follow the action up close.
import {execFileSync, spawn} from 'node:child_process';
import fs from 'node:fs';
import net from 'node:net';
import os from 'node:os';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
import {chromium} from '../../web/node_modules/playwright-core/index.mjs';

const VIDEO = path.resolve(import.meta.dirname, '..');
const REPO = path.resolve(VIDEO, '..');
// The app's own window size (launcher: 1280 wide), captured at double resolution so close-ups stay sharp.
const VIEW = {width: 1280, height: 720};
const SCALE = 2;
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

// A visible pointer for the recording (headless captures have none), with a ripple on each click.
// CSSOM only, so the app's CSP allows it.
const CURSOR = `(() => {
  const add = () => {
    const c = document.createElement('div');
    Object.assign(c.style, {position: 'fixed', left: '-60px', top: '-60px', width: '24px', height: '24px',
      margin: '-12px 0 0 -12px', borderRadius: '50%', border: '3px solid #1D1C1A', boxSizing: 'border-box',
      background: 'rgba(185, 138, 62, 0.45)', pointerEvents: 'none', zIndex: '2147483647', transition: 'transform 90ms'});
    document.body.appendChild(c);
    const at = window.__tutorialMouse;
    if (at) Object.assign(c.style, {left: at.x + 'px', top: at.y + 'px'});
    const ripple = () => {
      const r = document.createElement('div');
      Object.assign(r.style, {position: 'fixed', left: c.style.left, top: c.style.top, width: '24px', height: '24px',
        margin: '-12px 0 0 -12px', borderRadius: '50%', border: '3px solid #B98A3E', boxSizing: 'border-box',
        pointerEvents: 'none', zIndex: '2147483646', opacity: '1', transform: 'scale(1)',
        transition: 'transform 500ms ease-out, opacity 500ms ease-out'});
      document.body.appendChild(r);
      requestAnimationFrame(() => requestAnimationFrame(() => { r.style.transform = 'scale(2.6)'; r.style.opacity = '0'; }));
      setTimeout(() => r.remove(), 600);
    };
    addEventListener('mousemove', (e) => { c.style.left = e.clientX + 'px'; c.style.top = e.clientY + 'px'; }, true);
    addEventListener('mousedown', () => { c.style.transform = 'scale(0.75)'; ripple(); }, true);
    addEventListener('mouseup', () => { c.style.transform = 'scale(1)'; }, true);
    addEventListener('tutorial-press', () => { c.style.transform = 'scale(0.75)'; ripple(); setTimeout(() => { c.style.transform = 'scale(1)'; }, 150); });
  };
  if (document.body) add(); else addEventListener('DOMContentLoaded', add);
})()`;

// The words a viewer would use for a control: its label, aria-label or own text, kept short.
const describe = (locator) => locator.evaluate((el) => {
  const clean = (s) => (s || '').replace(/\s+/g, ' ').replace(/\(\s+/g, '(').replace(/\s+\)/g, ')').trim();
  const own = (node) => clean([...node.childNodes].filter((n) => n.nodeType === 3).map((n) => n.textContent).join(' '));
  const label = el.labels?.[0] ? own(el.labels[0]) || clean(el.labels[0].textContent) : '';
  const mine = own(el);
  const text = label || clean(el.getAttribute('aria-label')) || (/[a-z]{3}/i.test(mine) ? mine : clean(el.innerText || el.textContent))
    || clean(el.getAttribute('placeholder'));
  return text.length > 46 ? `${text.slice(0, 44).replace(/\s+\S*$/, '')}…` : text;
});
const KEYS = {ArrowDown: '↓', ArrowUp: '↑', Escape: 'Esc', Enter: 'Enter', 'Control+End': 'Ctrl+End'};

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

  // The flag (not only the context setting) makes the captured frames device pixels.
  browser = await chromium.launch({args: [`--force-device-scale-factor=${SCALE}`]});
  const context = await browser.newContext({viewport: VIEW, deviceScaleFactor: SCALE, colorScheme: 'light', acceptDownloads: true});
  await context.addInitScript(CURSOR);
  const page = await context.newPage();
  page.setDefaultTimeout(15_000);
  const downloads = [];
  page.on('download', async (d) => {
    const to = path.join(work, d.suggestedFilename());
    await d.saveAs(to).catch(() => {});
    downloads.push(to);
  });
  // A tutorial may start on an outside page (tutorial 1 opens the public Releases page).
  await page.goto(/^https?:/.test(tutorial.start ?? '') ? tutorial.start : base + (tutorial.start ?? '/'));
  await page.waitForLoadState('networkidle');
  await tutorial.ready?.(page);

  let t0 = 0;
  let mouse = {x: VIEW.width / 2, y: VIEW.height / 2};
  const events = [];
  // One on-screen action: what it is (verb, value, target) and where (box, in viewport CSS pixels).
  const note = (action, box) => events.push({t: Date.now() - t0, action,
    box: box && {x: Math.round(box.x), y: Math.round(box.y), width: Math.round(box.width), height: Math.round(box.height)}});
  const glide = async (to) => {
    await page.mouse.move(to.x, to.y, {steps: Math.max(10, Math.round(Math.hypot(to.x - mouse.x, to.y - mouse.y) / 18))});
    await page.evaluate((at) => { window.__tutorialMouse = at; }, to);
    mouse = to;
  };
  // Clicks land on the control's centre; hovers point from just left of it and typing parks at the field's
  // right end, so the pointer never hides the text being read or typed.
  // Controls near the bottom edge would sit under the caption panel, so bring them to the middle first.
  const reveal = async (locator) => {
    await locator.scrollIntoViewIfNeeded();
    let box = await locator.boundingBox();
    if (box && box.height < VIEW.height * 0.6 && (box.y + box.height > VIEW.height - 150 || box.y < 70)) {
      await locator.evaluate((el) => el.scrollIntoView({block: 'center'}));
      await sleep(350);
      box = await locator.boundingBox();
    }
    return box;
  };
  const moveTo = async (locator, action, point = false) => {
    const box = await reveal(locator);
    if (!box) throw new Error(`Not visible: ${locator}`);
    note(action, box);
    const x = point === 'end' ? box.x + box.width - 16 : point ? (box.x > 30 ? box.x - 18 : box.x + 4) : box.x + box.width / 2;
    await glide({x: Math.round(x), y: Math.round(box.y + Math.min(box.height / 2, 18))});
    await sleep(300);
    return box;
  };
  // Native dropdown lists are not part of a page capture, so show the real options under the control,
  // point at the chosen one, then select it.
  const showOptions = async (locator, value) => {
    const box = await locator.boundingBox();
    const list = await locator.evaluate((sel, want) => {
      const options = [...sel.options].map((o, i) => ({i, label: o.label || o.text, value: o.value, disabled: o.disabled}));
      const pick = typeof want === 'string' ? options.find((o) => o.value === want || o.label === want)
        : want.index !== undefined ? options[want.index] : options.find((o) => o.label === want.label);
      return {options, chosen: pick?.i ?? -1};
    }, value);
    if (list.chosen < 0) throw new Error(`No option ${JSON.stringify(value)} in ${locator}`);
    const rowH = 30;
    await page.evaluate(({box, list, rowH}) => {
      const menu = document.createElement('div');
      menu.id = '__tutorial_menu';
      Object.assign(menu.style, {position: 'fixed', left: box.x + 'px', top: (box.y + box.height + 2) + 'px',
        width: Math.max(box.width, 180) + 'px', background: '#FFFFFF', border: '1px solid #1D1C1A80',
        boxShadow: '0 4px 14px rgba(0,0,0,0.18)', zIndex: '2147483645', pointerEvents: 'none',
        font: '14px "Libre Franklin", Arial, sans-serif', color: '#1D1C1A'});
      for (const o of list.options) {
        const row = document.createElement('div');
        row.textContent = o.label;
        Object.assign(row.style, {height: rowH + 'px', lineHeight: rowH + 'px', padding: '0 10px', whiteSpace: 'nowrap',
          overflow: 'hidden', textOverflow: 'ellipsis', color: o.disabled ? '#1D1C1A66' : '#1D1C1A',
          background: o.i === list.chosen ? 'rgba(35, 98, 146, 0.18)' : 'transparent'});
        menu.appendChild(row);
      }
      document.body.appendChild(menu);
    }, {box, list, rowH});
    await sleep(500);
    await glide({x: Math.round(box.x + Math.min(box.width, 180) / 2), y: Math.round(box.y + box.height + 2 + rowH * (list.chosen + 0.5))});
    await sleep(350);
    await page.evaluate(() => dispatchEvent(new Event('tutorial-press')));
    await sleep(250);
    await page.evaluate(() => document.getElementById('__tutorial_menu')?.remove());
    return list.options[list.chosen].label;
  };
  const ui = {
    page, cli, work, home, sleep, downloads, base, python,
    // `label` replaces the words taken from the page when those would read badly in a caption.
    hover: async (locator, label) => { await moveTo(locator, {verb: 'Look at', target: label ?? await describe(locator)}, true); },
    click: async (locator, label) => {
      await moveTo(locator, {verb: 'Click', target: label ?? await describe(locator)}); await locator.click(); await sleep(500);
    },
    // Add text at the end of a field's existing text.
    append: async (locator, text) => {
      const target = await describe(locator);
      const box = await moveTo(locator, {verb: 'Click', target}, 'end');
      await locator.click();
      await ui.press('Control+End');
      note({verb: 'Type', value: text.trim(), target}, box);
      await locator.pressSequentially(text, {delay: 55}); await sleep(350);
    },
    type: async (locator, text) => {
      await moveTo(locator, {verb: 'Type', value: text, target: await describe(locator)}, 'end');
      await locator.click(); await locator.pressSequentially(text, {delay: 55}); await sleep(350);
    },
    // Clearing a field is silent; long or multi-line text is pasted.
    fill: async (locator, text) => {
      const target = await describe(locator);
      const action = !text ? null : text.length > 40 || text.includes('\n') ? {verb: 'Paste the text into', target}
        : {verb: 'Type', value: text, target};
      if (action) await moveTo(locator, action, 'end'); else await locator.scrollIntoViewIfNeeded();
      await locator.click(); await locator.fill(text); await sleep(text ? 450 : 150);
    },
    select: async (locator, value) => {
      const target = await describe(locator);
      const box = await moveTo(locator, {verb: 'Open', target});
      const chosen = await showOptions(locator, value);
      note({verb: 'Choose', value: chosen, target}, box);
      await locator.selectOption(value); await sleep(500);
    },
    press: async (key) => {
      await page.evaluate(() => dispatchEvent(new Event('tutorial-press')));
      await page.keyboard.press(key);
      await sleep(150);
      const box = await page.evaluate(() => {
        const el = document.activeElement;
        if (!el || el === document.body) return null;
        const r = el.getBoundingClientRect();
        return {x: r.x, y: r.y, width: r.width, height: r.height};
      });
      note({verb: 'Press', target: KEYS[key] ?? key}, box);
      await sleep(450);
    },
    upload: async (locator, files) => {
      await moveTo(locator, {verb: 'Choose', value: path.basename([files].flat()[0]), target: 'the file picker'});
      await locator.setInputFiles(files); await sleep(500);
    },
    // Drag across `phrase` inside `locator` like a reader selecting words.
    selectText: async (locator, phrase) => {
      await reveal(locator);
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
          const box = range.getBoundingClientRect();
          return {x1: a.left + 1, y1: a.top + a.height / 2, x2: b.right - 1, y2: b.top + b.height / 2,
            box: {x: box.x, y: box.y, width: box.width, height: box.height}};
        }
        return null;
      }, phrase);
      if (!at) throw new Error(`Text not found: ${phrase}`);
      note({verb: 'Select', value: phrase}, at.box);
      await glide({x: at.x1, y: at.y1});
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
    // Frame a region without an action (for example a result table).
    zoom: async (locator) => { const box = await locator.boundingBox(); if (box) note(null, box); },
  };

  // JPEG frames with browser timestamps, encoded below: sharper text than the built-in webm and exact step timing.
  const steps = [];
  const frames = [];
  const frameDir = path.join(work, 'frames');
  fs.mkdirSync(frameDir);
  // Chrome's own screencast, so frames carry the browser's timestamps at full device resolution.
  const cdp = await context.newCDPSession(page);
  cdp.on('Page.screencastFrame', ({data, metadata, sessionId}) => {
    const name = `${String(frames.length).padStart(6, '0')}.jpg`;
    fs.writeFileSync(path.join(frameDir, name), Buffer.from(data, 'base64'));
    frames.push({name, t: metadata.timestamp * 1000});
    cdp.send('Page.screencastFrameAck', {sessionId}).catch(() => {});
  });
  await cdp.send('Page.startScreencast', {format: 'jpeg', quality: 90, maxWidth: VIEW.width * SCALE, maxHeight: VIEW.height * SCALE});
  t0 = Date.now();
  let cursor = 0;
  for (const [i, s] of tutorial.steps.entries()) {
    const step = {caption: s.caption, demo: Boolean(s.demo), card: s.card ?? null, startMs: cursor, endMs: cursor};
    if (s.card) {
      await s.prepare?.(ui, s.card);
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
      if (s.fast) step.rate = Math.max(1, Math.round(((step.endMs - step.startMs) / hold(s.caption)) * 10) / 10);
    }
    steps.push(step);
    console.log(`${i + 1}/${tutorial.steps.length} ${s.caption}`);
  }
  await cdp.send('Page.stopScreencast');
  await sleep(300);
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
    '-c:v', 'libx264', '-crf', '16', '-preset', 'medium', path.join(out, `${id}.mp4`)], {cwd: work});
  fs.rmSync(frameDir, {recursive: true});
  fs.writeFileSync(path.join(out, `${id}.json`), JSON.stringify({id, video: `recordings/${id}.mp4`, view: VIEW, steps, events}, null, 2) + '\n');
  console.log(`wrote public/recordings/${id}.mp4 and ${id}.json (${(cursor / 1000).toFixed(1)} s, ${frames.length} frames, ${events.length} actions)`);
} finally {
  await browser?.close().catch(() => {});
  // Stop only the server this run started (and its children).
  if (server?.pid) spawn('taskkill', ['/PID', String(server.pid), '/T', '/F'], {stdio: 'ignore'});
}
