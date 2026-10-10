// One command per tutorial: node tutorials/make.mjs 02 [--no-record]
// Records (unless --no-record), renders, makes the poster, checks the MP4 with ffprobe, samples six review
// frames into out/review/NN/ and copies the MP4 and poster to docs/media/tutorials/.
import {execFileSync} from 'node:child_process';
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
remotion('render', `tutorial-${id}`, mp4);
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
].filter(Boolean);
console.log(`${name}: ${video.codec_name} ${video.width}x${video.height} ${video.r_frame_rate} ${seconds.toFixed(1)} s ${megabytes.toFixed(1)} MB`);

// Intro, four points through the steps, outro; scaled down for inspection.
const review = path.join(VIDEO, 'out/review', id);
fs.mkdirSync(review, {recursive: true});
for (const [n, t] of [2, 0.2, 0.4, 0.6, 0.8, seconds - 2].map((x, n) => [n + 1, x < 1 ? x * seconds : x])) {
  execFileSync('ffmpeg', ['-v', 'error', '-y', '-ss', t.toFixed(2), '-i', mp4, '-frames:v', '1', '-vf', 'scale=960:-1',
    path.join(review, `${n}.jpg`)], {cwd: VIDEO});
}

if (problems.length) throw new Error(`${name} failed checks: ${problems.join('; ')}`);
fs.mkdirSync(MEDIA, {recursive: true});
fs.copyFileSync(path.join(VIDEO, mp4), path.join(MEDIA, `${name}.mp4`));
fs.copyFileSync(path.join(VIDEO, poster), path.join(MEDIA, `${name}.jpg`));
console.log(`copied to docs/media/tutorials/${name}.mp4 and .jpg; review frames in out/review/${id}/`);
