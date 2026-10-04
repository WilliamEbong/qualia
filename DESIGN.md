# Qualia design system

## Atmosphere

An archival research instrument: paper reading surfaces, inked rules, catalogue drawers, and field-note evidence. The working interface stays quiet enough for long coding sessions. The home plate and experiment timeline provide visual character without changing any computation or trust language.

The approved contract is [doc 04](docs/04-qualia-design.md), implemented under [doc 05](docs/05-qualia-design-build.md). The installed gpt-taste skill informs intentional composition and legibility; this contract overrides its randomized layouts, font choices, cinematic spacing, and animation libraries. Variance low, motion low, density medium.

## Palette roles

All source color values and font declarations live in `web/src/styles/tokens.css`. Light paper uses ivory, cream, ink, graphite, and rust. Dark paper uses charcoal, night, ivory, and ochre. Focus is Prussian in light and sky in dark. Fixed code colors retain their ordered Prussian, rust, viridian, gamboge, mineral green, dusty blue, ochre, and sage identities across themes. Repeated colors gain a hatch stripe.

KEEP is a viridian rule and literal mono label; REVERT is rust with the same grammar. Uncertainty and errors retain words and an accompanying mark. Matrix intensity is Prussian with printed counts. Color never carries a decision alone.

## Typography and measure

Self-hosted Fontsource 5.3 fonts: Cormorant Garamond 400 for sentence-case display headings; Libre Franklin Variable 400/500 for text; IBM Plex Mono 400 for IDs, provenance, captions, and metrics. The scale is 12 / 13 / 15 / 17 / 20 / 24 / 32 / 44px. UI text uses 15px/1.3, transcript text 17px/1.6 at no more than 68ch, and mono captions 13px/1.4. No synthetic bold display headings.

## Structure and component states

- Source and coding rails are 280px and 340px on wide screens; the reading column gets the remaining space. Narrow screens stack in reading order without page overflow.
- Human decisions have solid 3px stripes. Suggestions retain dashed stripes and their exact model-reported score, calibration, and trigger captions. Accepted model decisions retain solid stripes plus the mono `m`. Historical decisions remain in provenance.
- Codebook drawers use ruled boundaries and cream field-note slips. Frozen versions keep their IDs and timestamps visible.
- Experiments use a horizontal ruled timeline with 16px decision dots. Selection opens the hypothesis, measurements, changed files, and decision provenance.
- Home uses the original seed-3 title-dome plate, a horizon at 63.3%, and project drawers. Empty states borrow the original star-chart plate and horizon without obscuring instructions.
- Data tables keep exact labels and mono counts. Frequency and scatter charts scroll within their own containers to preserve readable labels and 40px interactive hit areas.
- Every interactive control has visible keyboard focus and a minimum 40px touch target. Disabled actions remain recognizable and explain their availability through existing copy.

## Motion and restraint

Square corners, no shadows, one-pixel keylines, and a four-point spacing rhythm. UI transitions are 150ms; media fades are 300ms with the prescribed easing. Reduced-motion preferences remove transitions and animations. No extra animation dependency, ornamental status badges, fabricated metrics, or hidden trust captions.

## Preservation

Presentation changes are limited to styles, markup/classes, public presentation assets, and this document. State, handlers, calculations, generated API types, privacy behavior, and protected project files remain unchanged from the D0 baseline. Root performs browser evidence and accessibility/performance audits before final acceptance.

## Measured accessibility and loading adjustments

The light caption token is slightly darker than the initial contract example to reach AA against both ivory and cream. Fixed code and decision colors are unchanged. The seed-3 dome plate has 640px and 1280px WebP derivatives encoded with existing FFmpeg/libwebp quality65; these preserve the original composition while removing excess grain payload. Responsive image and preload declarations use the same candidate sizes and deployment base. Initial loading reserves a viewport of content height to keep the footer from jumping through the visible page.
