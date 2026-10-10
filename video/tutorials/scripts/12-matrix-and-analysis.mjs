// Tutorial 12 · Matrix and Analysis workbench (guide §9–10). Storyboard: ../storyboards/12-matrix-and-analysis.md
import {button, field, practice} from '../shared.mjs';

export const seed = (q) => practice(q, 'coded');

const criteria = (page) => page.locator('details', {has: page.locator('summary', {hasText: /^Analysis criteria$/})});
const apply = (ui) => ui.click(button(ui.page, 'Apply analysis criteria'));
const summary = (page, text) => page.locator('summary', {hasText: text}).first();
const heading = (page, name) => page.getByRole('heading', {name, exact: true});
const openDetails = async (ui, text) => {
  const s = summary(ui.page, text);
  if ((await s.locator('..').getAttribute('open')) === null) await ui.click(s);
  else await ui.hover(s);
};

export const steps = [
  {caption: 'Each cell counts distinct currently coded segments for one code and case.',
    do: async (ui) => {
      await ui.select(ui.page.getByLabel('Local project'), 'practice-study');
      await ui.click(button(ui.page, 'Matrix'));
    }},
  {caption: 'Repeated spans of one code on a segment count once in a matrix cell.',
    do: async (ui) => { for (const c of ['p01', 'p02', 'p03']) await ui.hover(ui.page.getByRole('button', {name: new RegExp(`^Support · ${c} ·`)})); }},
  {caption: 'A matrix cell leads back to its supporting coded excerpts.',
    do: (ui) => ui.click(ui.page.getByRole('button', {name: /^Support · p03 ·/}))},
  {caption: 'Use the passage context to interpret the count.',
    do: async (ui) => {
      await ui.hover(field(ui.page, 'Code'));
      await ui.hover(field(ui.page, 'Case'));
      await ui.click(button(ui.page, 'Open in transcript').first());
    }},
  {caption: 'Analysis describes current manual and accepted coding.',
    do: async (ui) => { await ui.click(button(ui.page, 'Analysis')); await ui.hover(heading(ui.page, 'Code frequencies')); }},
  {caption: 'Each code appears on two of the three practice segments and cases.',
    do: async (ui) => {
      const table = ui.page.getByRole('table', {name: 'Code frequencies', exact: true});
      await ui.zoom(table);
      await ui.hover(table.getByRole('columnheader', {name: 'Segment %'}));
      await ui.hover(table.getByRole('columnheader', {name: 'Case %'}));
    }},
  {caption: 'Chart bars and counts open the evidence contributing to the result.',
    do: async (ui) => {
      await ui.click(ui.page.getByRole('button', {name: /^Support: \d+ segments/}));
      await ui.hover(heading(ui.page, 'Source evidence'));
    }},
  {caption: 'Coding evidence keeps event identities, actors, spans and frozen versions.',
    do: (ui) => ui.click(summary(ui.page, /^Coding evidence/))},
  {caption: 'Source and case filters narrow the selected evidence.',
    do: async (ui) => {
      await openDetails(ui, /^Analysis criteria$/);
      await ui.hover(field(criteria(ui.page), 'Analysis source'));
      await ui.hover(field(criteria(ui.page), 'Analysis case'));
    }},
  {caption: 'The text query is a case-insensitive substring search.',
    do: async (ui) => {
      await ui.type(field(criteria(ui.page), 'Literal text query'), 'support');
      await ui.click(summary(ui.page, /^Code filter/));
      await ui.click(criteria(ui.page).getByRole('checkbox', {name: 'Support'}));
    }},
  {caption: 'All filter types intersect when the report is calculated.',
    do: async (ui) => { await ui.select(field(criteria(ui.page), 'Match selected codes'), 'any'); await apply(ui); }},
  {caption: 'No code selection imposes no code filter.',
    do: async (ui) => {
      await ui.hover(ui.page.getByText(/^Applied criteria/).first());
      await ui.fill(field(criteria(ui.page), 'Literal text query'), '');
      await ui.click(criteria(ui.page).getByRole('checkbox', {name: 'Support'}));
    }},
  {caption: 'Choose numeric measurements explicitly rather than treating identifiers as numbers.',
    do: async (ui) => {
      await ui.select(field(criteria(ui.page), 'Group by case attribute'), 'group');
      await ui.click(criteria(ui.page).getByRole('checkbox', {name: 'age'}));
      await ui.click(criteria(ui.page).getByRole('checkbox', {name: 'wellbeing'}));
    }},
  {caption: 'Segment co-occurrence counts passages carrying both codes anywhere.',
    do: (ui) => ui.select(field(criteria(ui.page), 'Co-occurrence unit'), 'segment')},
  {caption: 'Word-frequency options control the descriptive word list.',
    do: async (ui) => {
      await ui.click(summary(ui.page, 'Word-frequency options'));
      await ui.fill(field(criteria(ui.page), 'Minimum word length'), '3');
      await ui.fill(field(criteria(ui.page), 'Top words'), '10');
    }},
  {caption: 'Stopwords are explicit, with no hidden stemming or synonym groups.',
    do: async (ui) => { await ui.type(field(criteria(ui.page), 'Explicit stopwords'), 'the, and'); await apply(ui); }},
  {caption: "Group percentages use each group's own segment and case denominators.",
    do: async (ui) => {
      await ui.hover(heading(ui.page, 'Case-group comparisons'));
      await ui.click(summary(ui.page, /^north ·/));
      await ui.click(summary(ui.page, /^south ·/));
    }},
  {caption: 'Selecting a code pair opens its contributing passages.',
    do: async (ui) => {
      await ui.hover(heading(ui.page, 'Code co-occurrence'));
      await ui.click(ui.page.getByRole('button', {name: /^Support and Pressure:/}).first());
    }},
  {caption: 'Jaccard measures segments carrying both codes divided by those carrying either.',
    do: (ui) => ui.click(summary(ui.page, 'Exact pair counts and segment-presence Jaccard'))},
  {caption: 'Overlap requires coded spans to share more than a touching boundary.',
    do: async (ui) => { await ui.select(field(criteria(ui.page), 'Co-occurrence unit'), 'overlap'); await apply(ui); }},
  {caption: 'Jaccard still uses segment presence even when the count uses span overlap.',
    do: async (ui) => {
      await ui.hover(heading(ui.page, 'Code co-occurrence'));
      await openDetails(ui, 'Exact pair counts and segment-presence Jaccard');
    }},
  {caption: 'Repeated words and the number of passages containing them are different counts.',
    do: async (ui) => {
      await ui.hover(heading(ui.page, 'Words in selected text'));
      await ui.hover(ui.page.getByRole('columnheader', {name: 'Occurrences'}).first());
      await ui.hover(ui.page.getByRole('columnheader', {name: 'Distinct segments'}).last());
    }},
  {caption: 'Check data quality before interpreting numeric summaries.',
    do: async (ui) => {
      const table = ui.page.getByRole('table', {name: 'Numeric descriptive statistics', exact: true});
      await ui.hover(heading(ui.page, 'Numeric case attributes'));
      for (const col of ['Valid', 'Missing']) await ui.hover(table.getByRole('columnheader', {name: col, exact: true}));
    }},
  {caption: 'Each eligible case contributes one numeric observation.',
    do: async (ui) => {
      const table = ui.page.getByRole('table', {name: 'Numeric descriptive statistics', exact: true});
      for (const col of ['Mean', 'Median', 'Sample SD']) await ui.hover(table.getByRole('columnheader', {name: col, exact: true}));
    }},
  {caption: 'The constructed practice pairs give a correlation of one, not a causal finding.',
    do: async (ui) => {
      await ui.hover(field(ui.page, 'Scatter fields'));
      await ui.hover(heading(ui.page, 'Numeric relationships'));
    }},
  {caption: 'Trace a numeric point back to the selected source material.',
    do: async (ui) => {
      await ui.click(summary(ui.page, 'Exact paired case values'));
      await ui.click(ui.page.getByRole('button', {name: /^Case \d+:/}).first());
    }},
  {caption: 'Standalone charts include labels and criteria that may contain research metadata.',
    do: async (ui) => {
      await ui.click(button(ui.page, 'Download frequency SVG'));
      await ui.click(button(ui.page, 'Download scatter SVG'));
    }},
  {caption: 'The report records its input identity and contributing coding evidence.',
    do: (ui) => ui.click(summary(ui.page, 'Analysis methods and provenance'))},
  {caption: 'Refresh reloads evidence and preserves applied criteria, not unsaved form changes.',
    do: async (ui) => {
      await ui.click(button(ui.page, 'Refresh analysis'));
      await ui.hover(ui.page.getByText(/^Applied criteria/).first());
    }},
];
