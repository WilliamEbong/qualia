# Qualia video tutorials

Thirteen silent, captioned 1080p tutorials (about two to four minutes each), recorded from the real local app and finished in Remotion with the same look as the explainer. They show what you would see, in an editorial screencast style kept to Qualia's visual language (square corners, keylines, paper plates, its three typefaces, the house easing, no springs or shadows): the app sits in a keylined stage; the camera follows each action up close; an ochre focus ring marks the control in use; pressed keys appear as key chips; dropdowns show their real choices; the caption names the action as it happens ("Click **Create local project**") above a one-line note from the user guide; a top line names the chapter and step over a progress rule; and the intro lists the tutorial's three to five parts, each announced by a short chapter card. Chapters are set per tutorial in `src/tutorials/list.ts`. The style board is a Design artifact ("Qualia tutorial video style"). The published MP4s and posters are in `docs/media/tutorials/`. Like the explainer, this is a portfolio asset: it changes no app code, tests, scripts or CI.

## How it works

- `storyboards/NN-*.md`: the plan for each tutorial (starting state, numbered UI steps, captions taken from the user guide).
- `scripts/NN-*.mjs`: what the recorder does. `seed()` prepares a scratch workspace with the Qualia CLI; `steps` pairs each caption with UI actions, or with a card for things a browser cannot show (the installer, a terminal, a file manager).
- `record.mjs`: starts a private Qualia server on a fresh scratch `QUALIA_HOME` and a free port, drives headless Chromium (the project's own Playwright in `web/node_modules`) at the app window's size, 1280x720, captured at double resolution, and saves `public/recordings/NN.mp4` plus `NN.json`: the step timeline and every action with its words and on-screen position. Each step has a timeout; an app error on screen fails the step.
- `src/tutorials/Tutorial.tsx`: the composition. Frames each action up close and holds still while the next one is already in view (house easing, no springs); draws the focus ring, key chips, caption panel, top line, chapter cards and intro outline from the recorded actions, so a style change needs only a re-render (`--no-record`).
- `make.mjs`: records, renders the `tutorial-NN` composition (`src/tutorials/`), makes the poster, checks the MP4 with ffprobe (1920x1080, 30 fps, video only, 115–250 s, under 19 MB so jsDelivr can stream it), saves six review frames and a review sheet to `out/review/NN/`, lists every stretch of five seconds or more where nothing on screen changes (`dead-frames.txt`; cards excluded) and copies the MP4 and poster to `docs/media/tutorials/`. The sheet and dead-frame list feed a scored review: each tutorial is marked 1–10 for readable UI, visible action, caption matching the screen and no dead air, and anything under 8 is fixed and re-rendered.

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
