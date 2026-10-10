# Qualia video tutorials

Thirteen silent, captioned 1080p tutorials (about two to four minutes each), recorded from the real local app and finished in Remotion with the same look as the explainer. The published MP4s and posters are in `docs/media/tutorials/`. Like the explainer, this is a portfolio asset: it changes no app code, tests, scripts or CI.

## How it works

- `storyboards/NN-*.md`: the plan for each tutorial (starting state, numbered UI steps, captions taken from the user guide).
- `scripts/NN-*.mjs`: what the recorder does. `seed()` prepares a scratch workspace with the Qualia CLI; `steps` pairs each caption with UI actions, or with a card for things a browser cannot show (the installer, a terminal, a file manager).
- `record.mjs`: starts a private Qualia server on a fresh scratch `QUALIA_HOME` and a free port, drives headless Chromium (the project's own Playwright in `web/node_modules`) at 1600x900, and saves `public/recordings/NN.mp4` plus `NN.json`, the step timeline. Each step has a timeout; an app error on screen fails the step.
- `make.mjs`: records, renders the `tutorial-NN` composition (`src/tutorials/`), makes the poster, checks the MP4 with ffprobe (1920x1080, 30 fps, video only, 115–250 s), saves six review frames to `out/review/NN/` and copies the MP4 and poster to `docs/media/tutorials/`.

## Rebuild one tutorial

Needs the project's Python environment (`uv sync`), the built web app (`web/dist`), Playwright's Chromium and ffmpeg/ffprobe on PATH. In PowerShell:

```
cd video
npm ci
$env:QUALIA_TUTORIAL_SCRATCH = "$env:TEMP\qualia-tutorials"
node tutorials/make.mjs 06
```

`node tutorials/make.mjs 06 --no-record` re-renders from the last recording. If a recording hangs, stop only that recorder's node process (it prints its PID; the browser and server are its children) and run the command again.

## Data and honesty

- The workspace must be a new folder under the system temp directory, so a recording can never open real projects.
- Data is the invented practice study from guide §3 and the public AnnoMI demo. AI scenes use the deterministic offline `fake` backend and carry a "demonstration" tag; tutorial 11's command cards show the outcome of the experiment the seed actually ran.
- No keys or tokens appear: the per-launch API token lives only in a page meta tag and request header.
- Long waits are sped up and labelled "sped up N×".
