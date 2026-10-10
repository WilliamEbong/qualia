// Tutorial 2 · First project in 5 minutes (guide §3). Storyboard: ../storyboards/02-first-project.md
import path from 'node:path';
import {PRACTICE_CSV, button, code, saved, source, writePractice} from '../shared.mjs';

export const seed = ({work}) => { writePractice(work); };

export const steps = [
  {caption: 'Use synthetic material to learn the workflow before starting real research.',
    do: (ui) => ui.click(ui.page.getByText('New project', {exact: true}))},
  {caption: 'Project identifiers use lowercase letters, digits and hyphens.',
    do: (ui) => ui.type(ui.page.getByLabel('Project identifier'), 'practice-study')},
  {caption: 'A project keeps its own material, codebook, settings and history.',
    do: async (ui) => {
      await ui.click(button(ui.page, 'Create local project'));
      await ui.click(ui.page.getByText('New project', {exact: true}));
    }},
  {caption: 'Keep the practice CSV outside the application folder.',
    card: {title: 'Save practice.csv', lines: ['In Notepad, paste these lines and save as practice.csv', 'with All Files and UTF-8 encoding.'],
      command: PRACTICE_CSV.trim()}},
  {caption: 'Import the three synthetic responses into this project.',
    do: async (ui) => { await ui.click(button(ui.page, 'Workspace')); await ui.click(button(ui.page, 'Import source')); }},
  {caption: 'Choose the UTF-8 file you just saved.',
    do: async (ui) => {
      const file = ui.page.locator('input[type=file][name=file]');
      await ui.hover(file);
      await ui.upload(file, path.join(ui.work, 'practice.csv'));
    }},
  {caption: 'Column mapping connects each response to its case and attributes.',
    do: async (ui) => {
      await ui.select(ui.page.getByLabel('File format'), 'csv');
      await ui.click(ui.page.getByText('CSV column mapping', {exact: true}));
    }},
  {caption: 'Column names must match the CSV headers exactly.',
    do: async (ui) => {
      for (const label of ['Text column', 'Case column', 'Speaker column']) await ui.hover(ui.page.getByLabel(label));
    }},
  {caption: 'The mapped measurements belong to each participant case.',
    do: async (ui) => {
      await ui.type(ui.page.getByLabel('Attribute columns'), 'group,age,wellbeing');
      await ui.click(button(ui.page, 'Import into project'));
      await source(ui.page, 2).waitFor();
    }},
  {caption: 'The expected result is three sources, three segments and three linked cases.',
    do: async (ui) => { for (const n of [0, 1, 2]) await ui.click(source(ui.page, n)); }},
  {caption: 'Start with a code for help from other people.',
    do: async (ui) => { await ui.click(button(ui.page, 'Codebook')); await ui.type(ui.page.getByLabel('Name', {exact: true}), 'Support'); }},
  {caption: 'Saving a draft records your definition before you freeze it.',
    do: async (ui) => {
      await ui.type(ui.page.getByLabel('Definition', {exact: true}), 'Practical or emotional help from other people.');
      await ui.click(button(ui.page, 'Save draft code'));
    }},
  {caption: 'The second code describes experienced demands or stress.',
    do: async (ui) => {
      await ui.type(ui.page.getByLabel('Name', {exact: true}), 'Pressure');
      await ui.type(ui.page.getByLabel('Definition', {exact: true}), 'Experienced demands or stress.');
    }},
  {caption: 'A frozen version makes these definitions available for coding.',
    do: async (ui) => { await ui.click(button(ui.page, 'Save draft code')); await ui.click(button(ui.page, 'Freeze codebook')); }},
  {caption: 'Each coding decision records its actor and frozen codebook version.',
    do: async (ui) => {
      await ui.click(button(ui.page, 'Workspace'));
      await ui.fill(ui.page.getByLabel('Human actor'), '');
      await ui.type(ui.page.getByLabel('Human actor'), 'researcher');
      await ui.hover(ui.page.getByLabel('Frozen codebook'));
    }},
  {caption: 'Assign Support to the whole first response.',
    do: async (ui) => {
      await ui.click(source(ui.page, 0));
      await ui.click(ui.page.locator('.segment-text').first());
      await ui.click(code(ui.page, 'Support'));
      await saved(ui.page);
    }},
  {caption: 'Assign Pressure to the whole second response.',
    do: async (ui) => {
      await ui.click(source(ui.page, 1));
      await ui.click(ui.page.locator('.segment-text').first());
      await ui.click(code(ui.page, 'Pressure'));
      await saved(ui.page);
    }},
  {caption: 'Both codes can apply to the same passage.',
    do: async (ui) => {
      await ui.click(source(ui.page, 2));
      await ui.click(ui.page.locator('.segment-text').first());
      await ui.click(code(ui.page, 'Support'));
      await saved(ui.page);
      await ui.click(code(ui.page, 'Pressure'));
      await saved(ui.page);
    }},
  {caption: 'Each code appears on two of three segments and two of three cases.',
    do: async (ui) => { await ui.click(button(ui.page, 'Analysis')); await ui.hover(ui.page.getByRole('table', {name: 'Code frequencies'})); }},
  {caption: 'Both percentages should be approximately 66.667 percent.',
    do: (ui) => ui.zoom(ui.page.getByRole('table', {name: 'Code frequencies'}))},
  {caption: 'The practice cases belong to north and south groups.',
    do: (ui) => ui.select(ui.page.getByLabel('Group by case attribute'), 'group')},
  {caption: 'Choose deliberately which attributes represent measurements.',
    do: async (ui) => {
      await ui.click(ui.page.getByRole('checkbox', {name: 'age'}));
      await ui.click(ui.page.getByRole('checkbox', {name: 'wellbeing'}));
    }},
  {caption: 'North contains two cases and south contains one.',
    do: async (ui) => {
      await ui.click(button(ui.page, 'Apply analysis criteria'));
      await ui.hover(ui.page.getByRole('heading', {name: 'Case-group comparisons'}));
    }},
  {caption: 'The constructed measurements give results that are easy to check.',
    do: (ui) => ui.hover(ui.page.getByRole('heading', {name: 'Numeric case attributes', exact: true}))},
  {caption: 'This is a software exercise, not a research finding.',
    do: (ui) => ui.hover(ui.page.getByRole('heading', {name: 'Numeric relationships', exact: true}))},
];
