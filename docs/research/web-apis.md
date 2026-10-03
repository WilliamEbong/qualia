# Frontend integration API notes

Checked 2026-10-03 (America/Denver). This is implementation research, not evidence that the app integration has run. Read against docs 01–02 and 04: logic in `web/src/lib/`, generated API types in `web/src/api/`, markup in components, token values only in `web/src/styles/tokens.css`. Design rules outrank framework defaults.

## Verified package metadata

Live `npm view <package> version peerDependencies --json` returned the following. Exact versions in the first column can be pinned in the lockfile; no requested pin was missing, so the runbook's nearest-release exception was unnecessary.

| Package | Published version checked | Compatibility note |
|---|---|---|
| `react`, `react-dom`, `@types/react` | 19.3.0 | Use matching React/DOM versions; Context7's nearest version-specific React source was 19.2.8. |
| `@tanstack/react-table` | 9.2.4 | Peer React >=18; use v9 APIs below. |
| `@recogito/text-annotator` | 4.3.6 | Requested pin exists. |
| `@recogito/react-text-annotator` | 4.3.6 | Peers include React/DOM 18 and 19; exact core dependency 4.3.6. |
| `@annotorious/react` | 3.9.3 | Fits wrapper dependency `^3.8.10`; provider/hook package. |
| `tailwindcss`, `@tailwindcss/vite` | 4.3.3 | Vite plugin peer permits Vite 5.2, 6, 7, 8. |
| `shadcn` | 4.21.1 | CLI/source distribution, not a monolithic UI runtime. |
| `openapi-typescript` | 7.13.0 | TypeScript peer `^5.x`; do not upgrade to TS6. |
| `typescript` | 5.9.3 | Requested `~5.9.3` exists. |
| `vite`, `@vitejs/plugin-react` | 8.3.2 / 6.1.1 | Metadata observed; main lane owns final runtime/Node compatibility checks. |

Reproduce metadata reads with a writable npm cache if the sandbox blocks the default cache:

```powershell
$qualiaResearchCache = Join-Path $env:TEMP 'qualia-web-api-npm-cache'
npm view @recogito/react-text-annotator@4.3.6 version peerDependencies peerDependenciesMeta --json --cache $qualiaResearchCache
```

The initial default-cache lookup failed with `EPERM` under `%LOCALAPPDATA%/npm-cache`; retry with the temp cache succeeded. No global configuration change or elevated access was needed. Metadata sources: [React registry](https://registry.npmjs.org/react), [Table registry](https://registry.npmjs.org/@tanstack%2freact-table), [Recogito registry](https://registry.npmjs.org/@recogito%2freact-text-annotator), [Tailwind registry](https://registry.npmjs.org/tailwindcss), [shadcn registry](https://registry.npmjs.org/shadcn), [openapi-typescript registry](https://registry.npmjs.org/openapi-typescript).

## React 19

Context7 resolved `/react/react/v19.2.8`; queried client rendering and external DOM lifecycle. Stable bootstrap API:

```tsx
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'

createRoot(document.getElementById('root')!).render(
  <StrictMode><App /></StrictMode>,
)
```

Keep subscription setup and teardown paired. Development StrictMode intentionally reruns effects, so annotation listeners must be removed in cleanup and direct annotator instances destroyed. Do not hide duplicate-event defects by disabling StrictMode. The exact installed 19.3.0 types and compiler remain the final check because the versioned Context7 source was older. [React DOM source](https://github.com/react/react/blob/v19.2.8/packages/react-dom/README.md), [StrictMode reference](https://react.dev/reference/react/StrictMode)

## TanStack Table v9

Context7 `/tanstack/table` returned current v9 React quick start and migration documentation. Minimal hook shape (place in `web/src/lib/`):

```tsx
import { createColumnHelper, tableFeatures, useTable } from '@tanstack/react-table'

type MatrixRow = { code: string; count: number }
const features = tableFeatures({})
const helper = createColumnHelper<typeof features, MatrixRow>()
const columns = helper.columns([
  helper.accessor('code', { header: 'Code' }),
  helper.accessor('count', { header: 'Count' }),
])

export function useMatrixTable(data: MatrixRow[]) {
  return useTable({ features, columns, data })
}
```

Rendering uses `table.getHeaderGroups()`, `table.getRowModel().rows`, `row.getAllCells()`, and `<table.FlexRender header={header} />` / `<table.FlexRender cell={cell} />`. Preserve stable references for data, columns, and features. V8's `useReactTable` and `getCoreRowModel()` recipe must not be pasted into v9. Add sorting/filtering only when required; v9 declares those in `tableFeatures`. [Official React quick start](https://github.com/tanstack/table/blob/main/docs/framework/react/quick-start.md), [migration guide](https://github.com/tanstack/table/blob/main/docs/framework/react/guide/migrating.md)

For Qualia's matrix, render real table markup; numeric cells retain printed counts and a button for drill-down, with heat styling supplied by tokens. Color must never be the only representation.

## Recogito 4.3.6 and React

Context7 tried both `Recogito Text Annotator` and `@recogito/text-annotator`; results were unrelated Studio/legacy Annotator packages. Do not treat those results as documentation for this dependency. Used official repository docs, then downloaded the exact published 4.3.6 npm tarballs with `npm pack --ignore-scripts` into a temporary research directory and inspected declarations. Context7 `/annotorious/annotorious` additionally verified shared lifecycle methods.

Use these imports and composition:

```tsx
import { Annotorious, useAnnotator } from '@annotorious/react'
import { TextAnnotator } from '@recogito/react-text-annotator'
import type { RecogitoTextAnnotator, TextAnnotation } from '@recogito/react-text-annotator'
import '@recogito/text-annotator/text-annotator.css'

// Markup component; synchronization logic belongs in a lib hook/controller.
<Annotorious>
  <TextAnnotator selectionMode="all">
    <p>{transcriptText}</p>
  </TextAnnotator>
</Annotorious>
```

Inside a descendant controller, `useAnnotator<RecogitoTextAnnotator>()` accesses the instance. Guard the initially unavailable instance at runtime. The provider must surround both controller and annotator. Load saved annotations with `anno.setAnnotations(savedAnnotations)` after the transcript DOM exists. Subscribe using `anno.on('createAnnotation', handler)` and remove the same callback with `anno.off('createAnnotation', handler)` in cleanup. The React wrapper owns destruction of its annotator; do not also destroy that instance in a child controller. Recreate the provider/annotator subtree when changing the immutable source version rather than reusing stale text offsets. [Official wrapper guide](https://raw.githubusercontent.com/recogito/text-annotator-js/main/packages/text-annotator-react/README.md), [wrapper lifecycle source](https://raw.githubusercontent.com/recogito/text-annotator-js/main/packages/text-annotator-react/src/TextAnnotator.tsx)

Core persistence shape is an annotation ID, `bodies`, and `target.selector` array containing `{ quote, start, end }`. Save serializable selectors; revived selectors can contain live `Range` and `HTMLElement` references that do not belong in API payloads. Apply saved records through the same validated conversion used after a server response. Multi-code and overlapping spans remain separate assignments in Qualia, even if the viewer groups them. [Official core API/data model](https://github.com/recogito/text-annotator-js)

**Offset boundary:** inspected 4.3.6 core code computes offsets using JavaScript string `.length`, hence UTF-16 code units. Python's normal string indices count Unicode code points. The implementation must explicitly convert at the boundary if the frozen API uses code-point indices. Also preserve rendered whitespace and source text exactly. Verify emoji, combining marks, overlap, and save/reload before claiming persistence works. This is an integration finding from the exact package, not proof that the application's conversion is correct.

Verified declaration files from [core 4.3.6 artifact](https://registry.npmjs.org/@recogito/text-annotator/-/text-annotator-4.3.6.tgz) and [React 4.3.6 artifact](https://registry.npmjs.org/@recogito/react-text-annotator/-/react-text-annotator-4.3.6.tgz): `dist/text-annotator.d.ts`, `dist/model/core/text-annotation.d.ts`, `dist/text-annotator-options.d.ts`, React `dist/index.d.ts`. The React package's OpenSeaDragon peer is optional; do not add an explicit image-viewer dependency for text coding. These packages carry transitive dependencies; the main lane must audit the actual lockfile.

No manual-span fallback is justified merely by documentation lookup trouble. The runbook permits that fallback only if Recogito cannot reload saved spans; first run the required round-trip proof.

## Tailwind 4 and shadcn

Context7 `/websites/tailwindcss` confirms the Vite integration; `/shadcn-ui/ui` confirms Vite aliases and Tailwind4 configuration. Add `tailwindcss()` from `@tailwindcss/vite` beside `react()` in Vite plugins. In the main CSS entry, use `@import "tailwindcss";`; do not use v3 `@tailwind` directives. Map semantic colors through `@theme inline` to existing CSS variables. Keep the actual color/font values in `tokens.css`. [Vite installation](https://tailwindcss.com/docs/installation/using-vite), [theme variables](https://tailwindcss.com/docs/theme)

For shadcn configuration: `rsc: false`, `tsx: true`, `tailwind.config: ""`, `tailwind.css` pointing to the real CSS entry, and `cssVariables: true`. Map `@/*` to `src/*` in both TypeScript and Vite. Use the CLI/source components actually needed; the generated defaults are a starting point and must be restyled to doc04. Do not import a stock shadcn data-table implementation that assumes TanStack v8. [Vite setup](https://ui.shadcn.com/docs/installation/vite), [manual installation](https://ui.shadcn.com/docs/installation/manual)

Qualia-specific obligations: remove rounded/shadow component classes; preserve focus outlines, semantic labels, solid/dashed provenance stripes, and the literal `model-reported` label. Put keyboard/state/data transformations in `web/src/lib/`. Before claiming the resulting UI works, use Playwright MCP navigation, snapshot/screenshot, and the specific layout/interaction checks from doc04.

## openapi-typescript 7.13

Context7 `/openapi-ts/openapi-typescript` confirmed local schema generation and imports of `paths`/`components`. From `web/`, with the project's dependency installed:

```powershell
npm exec openapi-typescript -- ../openapi.json -o src/api/schema.d.ts
```

The main lane must confirm the exported schema's actual filename. Do not hand-edit generated output. Prefer schema types such as `components['schemas']['ActualModelName']` after inspecting the generated file, rather than guessing a model name or blindly copying a nested response access from an example. No runtime fetch package is required just to generate types. [Official CLI](https://openapi-ts.dev/cli), [introduction](https://openapi-ts.dev/introduction)

The live npm peer range is `typescript: ^5.x`, so retain `~5.9.3`. Regenerate after contract changes and run TypeScript compilation; the generated type file alone does not validate runtime responses or authorize bypassing `X-Qualia-Token`.
