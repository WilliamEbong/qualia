// One command per tutorial: node tutorials/make.mjs 02 [--no-record]
// Records (unless --no-record), renders, makes the poster, checks the MP4 with ffprobe, samples six review
// frames into out/review/NN/ and copies the MP4 and poster to docs/media/tutorials/.
import {execFileSync, spawnSync} from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';

const VIDEO = path.resolve(import.meta.dirname, '..');
const MEDIA = path.resolve(VIDEO, '../docs/media/tutorials');
const id = process.argv[2];
const file = id && fs.readdirSync(path.join(VIDEO, 'tutorials/scripts')).find((f) => f.startsWith(`${id}-`));
if (!file) throw new Error('Usage: node tutorials/make.mjs <NN> [--no-record]');
const name = file.replace(/\.mjs$/, '');
const run = (cmd, args) => execFileSync(cmd, args, {cwd: VIDEO, stdio: 'inherit'});
const remotion = (...args) => run(process.execPath, ['node_modules/@remotion/cli/remotion-cli.js', ...args, '--log=error']);
const read = (cmd, args) => execFileSync(cmd, args, {cwd: VIDEO, encoding: 'utf8'});

if (!process.argv.includes('--no-record')) run(process.execPath, ['tutorials/record.mjs', id]);

const mp4 = `out/tutorials/${name}.mp4`;
const poster = `out/tutorials/${name}.jpg`;
// CRF 23 keeps each file under jsDelivr's 20 MB limit; the 1440p recordings make rendering CPU-bound.
// Under memory pressure the frame extractor can drop a request; retry once with fewer workers.
try {
  remotion('render', `tutorial-${id}`, mp4, '--crf=23', '--concurrency=7');
} catch {
  console.log('render failed; retrying with --concurrency=3');
  remotion('render', `tutorial-${id}`, mp4, '--crf=23', '--concurrency=3');
}
remotion('still', `tutorial-${id}`, poster, '--frame=60', '--image-format=jpeg', '--jpeg-quality=85');

const probe = JSON.parse(read('ffprobe', ['-v', 'error', '-show_entries',
  'stream=codec_type,codec_name,width,height,r_frame_rate:format=duration,size', '-of', 'json', mp4]));
const [video, ...others] = probe.streams;
const seconds = Number(probe.format.duration);
const megabytes = Number(probe.format.size) / 1e6;
const problems = [
  video.codec_type !== 'video' && 'first stream is not video',
  others.length && 'extra streams (audio?)',
  (video.width !== 1920 || video.height !== 1080) && `size ${video.width}x${video.height}`,
  video.r_frame_rate !== '30/1' && `fps ${video.r_frame_rate}`,
  (seconds < 115 || seconds > 250) && `duration ${seconds.toFixed(1)} s`,
  // jsDelivr, which plays the published files in the browser, serves files up to 20 MB.
  megabytes > 19 && `size ${megabytes.toFixed(1)} MB`,
].filter(Boolean);
console.log(`${name}: ${video.codec_name} ${video.width}x${video.height} ${video.r_frame_rate} ${seconds.toFixed(1)} s ${megabytes.toFixed(1)} MB`);

// Intro, four points through the steps, outro; scaled down for inspection.
const review = path.join(VIDEO, 'out/review', id);
fs.mkdirSync(review, {recursive: true});
for (const [n, t] of [2, 0.2, 0.4, 0.6, 0.8, seconds - 2].map((x, n) => [n + 1, x < 1 ? x * seconds : x])) {
  execFileSync('ffmpeg', ['-v', 'error', '-y', '-ss', t.toFixed(2), '-i', mp4, '-frames:v', '1', '-vf', 'scale=960:-1',
    path.join(review, `${n}.jpg`)], {cwd: VIDEO});
}

// Self-critique input: a sheet of those frames at viewing size, plus every stretch of five seconds or more where
// nothing on screen changes, named by step (cards are static by design and skipped).
execFileSync('ffmpeg', ['-v', 'error', '-y', ...[1, 2, 3, 4, 5, 6].flatMap((n) => ['-i', path.join(review, `${n}.jpg`)]),
  '-filter_complex', '[0][1]hstack[a];[2][3]hstack[b];[4][5]hstack[c];[a][b][c]vstack=3', path.join(review, 'sheet.jpg')], {cwd: VIDEO});
const timeline = JSON.parse(fs.readFileSync(path.join(VIDEO, `public/recordings/${id}.json`), 'utf8'));
const f30 = (ms) => Math.round((ms * 30) / 1000);
let at = 4;
const windows = timeline.steps.map((step, n) => {
  const len = (step.card ? f30(step.cardMs ?? 4000) : Math.round((f30(step.endMs) - f30(step.startMs)) / (step.rate ?? 1))) / 30;
  const w = {n: n + 1, from: at, to: at + len, card: Boolean(step.card)};
  at += len;
  return w;
});
const scan = spawnSync('ffmpeg', ['-hide_banner', '-i', mp4, '-vf', 'freezedetect=n=0.003:d=5', '-map', '0:v', '-f', 'null', '-'],
  {cwd: VIDEO, encoding: 'utf8'}).stderr;
const starts = [...scan.matchAll(/freeze_start: ([\d.]+)/g)].map((m) => Number(m[1]));
const lengths = [...scan.matchAll(/freeze_duration: ([\d.]+)/g)].map((m) => Number(m[1]));
const dead = starts.map((start, i) => ({start, length: lengths[i] ?? seconds - start}))
  .map((f) => ({...f, step: windows.find((w) => f.start >= w.from && f.start < w.to)}))
  .filter((f) => f.step && !f.step.card);
const report = dead.map((f) => `step ${f.step.n}: ${f.length.toFixed(1)} s still from ${f.start.toFixed(1)} s`);
fs.writeFileSync(path.join(review, 'dead-frames.txt'), `${report.join('\n') || 'none'}\n`);
console.log(`dead stretches (5 s+, cards excluded): ${report.length ? report.join('; ') : 'none'}`);

if (problems.length) throw new Error(`${name} failed checks: ${problems.join('; ')}`);
fs.mkdirSync(MEDIA, {recursive: true});
fs.copyFileSync(path.join(VIDEO, mp4), path.join(MEDIA, `${name}.mp4`));
fs.copyFileSync(path.join(VIDEO, poster), path.join(MEDIA, `${name}.jpg`));
console.log(`copied to docs/media/tutorials/${name}.mp4 and .jpg; review frames in out/review/${id}/`);
