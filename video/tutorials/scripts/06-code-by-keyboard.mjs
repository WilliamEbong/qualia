// Tutorial 6 · Code by keyboard (guide §7). Storyboard: ../storyboards/06-code-by-keyboard.md
import {button, code, practice, saved, segmentText} from '../shared.mjs';

export const seed = (q) => practice(q, 'frozen');

const TEXT = `My sister gives me support when work feels stressful.

I feel pressure at work and take a short walk afterward.

Support from friends helps me manage pressure.`;

const assignments = (page) => page.getByRole('heading', {name: 'Current assignments'});

export const steps = [
  {caption: 'Work from the source to the passage, then inspect its coding and provenance.',
    do: async (ui) => {
      await ui.select(ui.page.getByLabel('Local project'), 'practice-study');
      await ui.click(button(ui.page, 'Workspace'));
    }},
  {caption: 'A short practice source makes keyboard navigation easy to see.',
    do: async (ui) => {
      await ui.click(button(ui.page, 'Import source'));
      await ui.type(ui.page.getByLabel('Source name'), 'keyboard-practice');
      await ui.select(ui.page.getByLabel('File format'), 'txt');
    }},
  {caption: 'Blank lines separate the three practice passages.',
    do: async (ui) => {
      await ui.fill(ui.page.getByLabel('Or paste source text'), TEXT);
      await ui.click(button(ui.page, 'Import into project'));
      await ui.page.getByLabel('Sources and cases').getByRole('button', {name: 'keyboard-practice'}).waitFor();
    }},
  {caption: 'Coding decisions record who made them.',
    do: async (ui) => {
      await ui.click(ui.page.getByLabel('Sources and cases').getByRole('button', {name: 'keyboard-practice'}));
      await ui.fill(ui.page.getByLabel('Human actor'), '');
      await ui.type(ui.page.getByLabel('Human actor'), 'researcher');
    }},
  {caption: 'The selected frozen version supplies the available codes.',
    do: (ui) => ui.select(ui.page.getByLabel('Frozen codebook'), {index: 1})},
  {caption: 'With no selected text, coding applies to the whole segment.',
    do: async (ui) => { await ui.click(segmentText(ui.page, 1)); await ui.hover(ui.page.getByText('Whole segment selected')); }},
  {caption: 'Keys 1 through 9 apply the corresponding displayed code.',
    do: async (ui) => {
      await ui.zoom(ui.page.locator('.code-shortcuts'));
      await ui.hover(code(ui.page, 'Support'));
      await ui.sleep(1200);
      await ui.press('1');
      await saved(ui.page);
    }},
  {caption: 'The assignment shows the coded excerpt and its span.',
    do: (ui) => ui.hover(ui.page.locator('.assignment').first())},
  {caption: 'Arrow keys move between segments in the current source.',
    do: (ui) => ui.press('ArrowDown')},
  {caption: 'Wait until the code buttons are enabled before the next shortcut.',
    do: async (ui) => { await ui.press('2'); await saved(ui.page); }},
  {caption: 'Navigation keeps the selected passage and coding panel together.',
    do: (ui) => ui.press('ArrowUp')},
  {caption: 'Select text when the code should cover only part of the passage.',
    do: (ui) => ui.selectText(segmentText(ui.page, 1), 'My sister gives me support')},
  {caption: 'Span offsets are relative to the segment and count Unicode code points.',
    do: async (ui) => {
      await ui.zoom(ui.page.locator('.selection-note'));
      await ui.hover(ui.page.locator('.selection-note blockquote'));
      await ui.sleep(1500);
      await ui.click(code(ui.page, 'Support'));
      await saved(ui.page);
    }},
  {caption: 'Several coded spans can belong to the same segment.',
    do: async (ui) => { await ui.hover(assignments(ui.page)); await ui.hover(ui.page.locator('.assignment').nth(1)); }},
  {caption: 'Removal changes current coding while retaining the original decision.',
    do: async (ui) => {
      await ui.click(ui.page.locator('.assignment').filter({hasText: '0:53'}).getByRole('button', {name: 'Remove assignment'}));
      await saved(ui.page);
    }},
  {caption: 'The audit trail retains both the assignment and its removal.',
    do: async (ui) => {
      await ui.click(ui.page.locator('details.provenance summary', {hasText: 'remove · Support'}).first());
      // Newest events come first: the whole-segment assignment is the oldest Support event.
      await ui.click(ui.page.locator('details.provenance summary', {hasText: 'assign · Support'}).last());
    }},
  {caption: 'Escape clears the current span selection.',
    do: async (ui) => {
      await ui.selectText(segmentText(ui.page, 1), 'when work feels stressful');
      await ui.press('Escape');
      await ui.hover(ui.page.getByText('Whole segment selected'));
    }},
  {caption: 'The visible button also clears a selected span.',
    do: async (ui) => {
      await ui.selectText(segmentText(ui.page, 1), 'when work feels stressful');
      await ui.click(button(ui.page, 'Use whole segment'));
    }},
  {caption: 'Multiple codes can apply to the same passage.',
    do: async (ui) => {
      await ui.click(segmentText(ui.page, 3));
      await ui.press('1');
      await saved(ui.page);
      await ui.press('2');
      await saved(ui.page);
    }},
  {caption: 'You can name a new idea without leaving the transcript.',
    do: async (ui) => {
      await ui.selectText(segmentText(ui.page, 2), 'a short walk');
      await ui.click(ui.page.getByText('New code from this passage', {exact: true}));
    }},
  {caption: "A code can use the participant's own words.",
    do: async (ui) => {
      await ui.type(ui.page.getByLabel('Code name'), 'a short walk');
      await ui.type(ui.page.getByLabel('Definition (optional)'), 'Walking as a response to pressure.');
    }},
  {caption: 'The selected words can become a positive example for the new code.',
    do: (ui) => ui.hover(ui.page.getByLabel('Keep the selected text as a positive example'))},
  {caption: 'This creates the code, freezes a version and assigns it to the selected passage.',
    do: async (ui) => { await ui.click(button(ui.page, 'Create, freeze and assign')); await saved(ui.page); }},
  {caption: 'The new frozen version includes all current draft edits.',
    do: async (ui) => {
      await ui.hover(ui.page.getByLabel('Frozen codebook'));
      await ui.hover(ui.page.locator('.assignment').first());
      await ui.hover(ui.page.locator('details.provenance summary', {hasText: 'a short walk'}).first());
    }},
];
