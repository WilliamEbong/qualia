// Tutorial 4 · Cases and attributes (guide §5). Storyboard: ../storyboards/04-cases-and-attributes.md
import {button, practice} from '../shared.mjs';

export const seed = (q) => practice(q, 'imported');

const attributes = (page) => page.getByLabel('Attributes, one name=value per line');
const edit = (page, name) => page.getByRole('button', {name: `Edit case ${name}`});
const sourceList = (page) => page.getByLabel('Sources and cases').locator('ul').first();

// Slower pacing keeps this short tutorial near two minutes.
export const pace = 1.65;

export const steps = [
  {caption: 'A case represents the unit you want to compare.',
    do: async (ui) => {
      await ui.select(ui.page.getByLabel('Local project'), 'practice-study');
      await ui.click(button(ui.page, 'Workspace'));
    }},
  {caption: 'The practice CSV has already created three participant cases.',
    do: async (ui) => { await ui.hover(ui.page.getByRole('heading', {name: 'Cases'})); await ui.click(edit(ui.page, 'p01')); }},
  {caption: 'Choose case names that fit your research design.',
    do: (ui) => ui.hover(ui.page.getByLabel('Case name'))},
  {caption: 'Existing source links remain attached and cannot be removed in this form.',
    do: async (ui) => {
      const links = ui.page.getByRole('group', {name: 'Add linked sources'});
      await ui.zoom(links);
      await ui.hover(links.getByRole('checkbox', {checked: true}).first());
    }},
  {caption: 'Analysis uses case attributes rather than source attributes.',
    do: (ui) => ui.hover(attributes(ui.page))},
  {caption: 'An empty value marks an attribute as missing without deleting its name.',
    do: async (ui) => {
      await ui.fill(attributes(ui.page), 'group=north\nage=\nwellbeing=4');
      await ui.click(button(ui.page, 'Save case'));
    }},
  {caption: 'Missing values are not silently converted to zero.',
    do: async (ui) => { await ui.click(edit(ui.page, 'p01')); await ui.hover(attributes(ui.page)); }},
  {caption: 'Submitted values update the named attributes.',
    do: async (ui) => {
      await ui.fill(attributes(ui.page), 'group=north\nage=24\nwellbeing=4');
      await ui.click(button(ui.page, 'Save case'));
    }},
  {caption: 'The case filter shows sources linked to the selected case.',
    do: async (ui) => { await ui.select(ui.page.getByLabel('Filter by case'), {label: 'p01'}); await ui.hover(sourceList(ui.page)); }},
  {caption: 'A source may link to more than one case.',
    do: async (ui) => {
      await ui.select(ui.page.getByLabel('Filter by case'), {label: 'All cases'});
      await ui.click(button(ui.page, 'Create case'));
    }},
  {caption: 'Choose the unit of comparison deliberately.',
    do: (ui) => ui.type(ui.page.getByLabel('Case name'), 'Practice comparison')},
  {caption: 'Each linked case receives the selected segments from its sources.',
    do: async (ui) => {
      const links = ui.page.getByRole('group', {name: 'Add linked sources'});
      await ui.click(links.getByRole('checkbox', {name: 'practice.csv: row 2'}));
      await ui.click(links.getByRole('checkbox', {name: 'practice.csv: row 4'}));
    }},
  {caption: 'Enter one attribute name and value on each line.',
    do: async (ui) => {
      await ui.type(attributes(ui.page), 'region=north');
      await ui.click(button(ui.page, 'Save case'));
      await edit(ui.page, 'Practice comparison').waitFor();
    }},
  {caption: 'Multiple source links do not automatically separate speakers inside a transcript.',
    do: async (ui) => {
      await ui.select(ui.page.getByLabel('Filter by case'), {label: 'Practice comparison'});
      await ui.hover(sourceList(ui.page));
    }},
  {caption: 'Shared sources can contribute to several groups, so totals may overlap.',
    do: async (ui) => {
      await ui.click(edit(ui.page, 'Practice comparison'));
      await ui.hover(ui.page.getByRole('group', {name: 'Add linked sources'}));
    }},
  {caption: 'Numeric analysis counts eligible cases, not individual segments.',
    do: async (ui) => {
      await ui.click(button(ui.page, 'Close'));
      await ui.select(ui.page.getByLabel('Filter by case'), {label: 'All cases'});
    }},
];
