// Tutorial 3 · Import material (guide §4). Storyboard: ../storyboards/03-import-material.md
import {PRACTICE_CSV, button, practice, writePractice} from '../shared.mjs';

export const seed = (q) => { practice(q, 'created'); writePractice(q.work); };

const NOTE = `My sister gives me support when work feels stressful.

I feel pressure at work and take a short walk afterward.`;
const sources = (page) => page.getByLabel('Sources and cases');
const notice = (page) => page.getByText(/new sources · \d+ new segments/).first();

// Open the import form and paste text with a format and name.
const paste = async (ui, opener, format, name, text) => {
  await ui.click(button(ui.page, opener));
  await ui.select(ui.page.getByLabel('File format'), format);
  if (name) await ui.type(ui.page.getByLabel('Source name'), name);
  await ui.fill(ui.page.getByLabel('Or paste source text'), text);
};

// Slower pacing keeps this short tutorial near two minutes.
export const pace = 1.3;

export const steps = [
  {caption: 'Check the project before importing research material.',
    do: async (ui) => {
      await ui.select(ui.page.getByLabel('Local project'), 'practice-study');
      await ui.click(button(ui.page, 'Workspace'));
    }},
  {caption: 'The import form accepts text, Markdown and mapped CSV.',
    do: (ui) => ui.click(button(ui.page, 'Import source'))},
  {caption: 'A source name helps you identify the imported document.',
    do: async (ui) => {
      await ui.select(ui.page.getByLabel('File format'), 'txt');
      await ui.type(ui.page.getByLabel('Source name'), 'practice-note');
    }},
  {caption: 'Blank-line paragraphs become separate segments by default.',
    do: (ui) => ui.fill(ui.page.getByLabel('Or paste source text'), NOTE)},
  {caption: 'A new document starts a new source.',
    do: async (ui) => {
      await ui.hover(ui.page.getByLabel('Source version'));
      await ui.click(button(ui.page, 'Import into project'));
      await notice(ui.page).waitFor();
    }},
  {caption: 'Inspect the segmentation before you begin coding.',
    do: async (ui) => {
      await ui.click(sources(ui.page).getByRole('button', {name: 'practice-note'}));
      await ui.hover(ui.page.getByLabel('Segment 2', {exact: true}));
    }},
  {caption: 'Choose the file format explicitly for each import.',
    do: async (ui) => {
      await ui.click(button(ui.page, 'Import transcript'));
      await ui.select(ui.page.getByLabel('File format'), 'md');
      await ui.type(ui.page.getByLabel('Source name'), 'practice-markdown');
    }},
  {caption: 'You can paste source text instead of choosing a file.',
    do: async (ui) => {
      await ui.fill(ui.page.getByLabel('Or paste source text'), 'Support from friends helps me manage pressure.');
      await ui.click(button(ui.page, 'Import into project'));
      await sources(ui.page).getByRole('button', {name: 'practice-markdown'}).waitFor();
    }},
  {caption: 'CSV imports use a header row and one text record per row.',
    card: {title: 'Save practice.csv', lines: ['Save these lines as a UTF-8 file named practice.csv,', 'outside the application folder.'],
      command: PRACTICE_CSV.trim()}},
  {caption: 'Use UTF-8 files so the imported text is read correctly.',
    do: async (ui) => {
      await ui.click(button(ui.page, 'Import source'));
      const file = ui.page.locator('input[type=file][name=file]');
      await ui.hover(file);
      await ui.upload(file, `${ui.work}/practice.csv`);
    }},
  {caption: 'The mapping uses exact, case-sensitive column names.',
    do: async (ui) => {
      await ui.select(ui.page.getByLabel('File format'), 'csv');
      await ui.click(ui.page.getByText('CSV column mapping', {exact: true}));
    }},
  {caption: 'A speaker label alone does not create a case.',
    do: async (ui) => { for (const label of ['Text column', 'Case column', 'Speaker column']) await ui.hover(ui.page.getByLabel(label)); }},
  {caption: 'Mapped attributes belong to the case when the row supplies one.',
    do: async (ui) => {
      await ui.type(ui.page.getByLabel('Attribute columns'), 'group,age,wellbeing');
      await ui.click(button(ui.page, 'Import into project'));
      await ui.page.getByRole('button', {name: 'practice.csv: row 2'}).waitFor();
    }},
  {caption: 'Identical text is stored once, even when it is imported again.',
    do: async (ui) => {
      await ui.hover(notice(ui.page));
      await ui.hover(ui.page.getByRole('heading', {name: 'Cases'}));
    }},
  {caption: 'A repeated import can report zero new sources.',
    do: async (ui) => {
      await paste(ui, 'Import source', 'txt', 'practice-note', NOTE);
      await ui.click(button(ui.page, 'Import into project'));
      await ui.page.getByText('0 new sources').first().waitFor();
      await ui.hover(ui.page.getByText('0 new sources').first());
    }},
  {caption: 'Use explicit source lineage when importing revised text.',
    do: async (ui) => {
      await ui.click(button(ui.page, 'Import source'));
      await ui.type(ui.page.getByLabel('Source name'), 'practice-note-revised');
    }},
  {caption: 'The revision points back to its earlier source.',
    do: (ui) => ui.select(ui.page.getByLabel('Source version'), {label: 'New version of practice-note'})},
  {caption: 'Changed text creates an immutable new source.',
    do: async (ui) => {
      await ui.select(ui.page.getByLabel('File format'), 'txt');
      await ui.fill(ui.page.getByLabel('Or paste source text'), 'My sister gives me support when work feels stressful today.');
    }},
  {caption: 'Old text and coding remain available, but coding does not transfer automatically.',
    do: async (ui) => {
      await ui.click(button(ui.page, 'Import into project'));
      await sources(ui.page).getByRole('button', {name: 'practice-note-revised'}).waitFor();
      await ui.click(sources(ui.page).getByRole('button', {name: 'practice-note', exact: true}));
      await ui.click(sources(ui.page).getByRole('button', {name: 'practice-note-revised'}));
    }},
];
