// Tutorial 5 · Build and freeze a codebook (guide §6). Storyboard: ../storyboards/05-build-and-freeze-codebook.md
import {button, field as labelled, practice} from '../shared.mjs';

export const seed = (q) => practice(q, 'imported');

const field = (page, label) => labelled(page.locator('#code-editor'), label);
const versions = (page) => page.locator('details.version summary', {hasText: /^cb_v/});

// Slower pacing keeps this short tutorial near two minutes.
export const pace = 1.5;

export const steps = [
  {caption: 'Your codebook belongs to you.',
    do: async (ui) => {
      await ui.select(ui.page.getByLabel('Local project'), 'practice-study');
      await ui.click(button(ui.page, 'Codebook'));
    }},
  {caption: 'Give the idea you want to track a clear name.',
    do: (ui) => ui.type(field(ui.page, 'Name'), 'Support')},
  {caption: 'A definition explains what the code means.',
    do: (ui) => ui.type(field(ui.page, 'Definition'), 'Practical or emotional help from other people.')},
  {caption: 'Parent codes organize related definitions into a hierarchy.',
    do: (ui) => ui.hover(field(ui.page, 'Parent code'))},
  {caption: 'Inclusion guidance explains when the code should apply.',
    do: (ui) => ui.type(field(ui.page, 'Include'), 'Practical help or emotional support from other people.')},
  {caption: 'Exclusion guidance helps distinguish neighboring codes.',
    do: (ui) => ui.type(field(ui.page, 'Exclude'), 'Demands or stress without help from others.')},
  {caption: 'Use examples to make the definition easier to apply consistently.',
    do: (ui) => ui.type(field(ui.page, 'Positive examples, one per line'), 'My sister gives me support when work feels stressful.')},
  {caption: 'Negative examples clarify what lies outside the code.',
    do: (ui) => ui.type(field(ui.page, 'Negative examples, one per line'), 'I feel pressure at work and take a short walk afterward.')},
  {caption: 'Saving creates a draft that you can still edit.',
    do: async (ui) => {
      await ui.hover(field(ui.page, 'Status'));
      await ui.click(button(ui.page, 'Save draft code'));
      await ui.page.getByRole('heading', {name: 'Support', exact: true}).waitFor();
    }},
  {caption: 'Add the other codes your study needs.',
    do: async (ui) => {
      await ui.type(field(ui.page, 'Name'), 'Pressure');
      await ui.type(field(ui.page, 'Definition'), 'Experienced demands or stress.');
    }},
  {caption: 'An active draft code is needed before you can freeze a usable version.',
    do: async (ui) => {
      await ui.hover(field(ui.page, 'Status'));
      await ui.click(button(ui.page, 'Save draft code'));
      await ui.page.getByRole('heading', {name: 'Pressure', exact: true}).waitFor();
    }},
  {caption: 'Freezing captures an immutable version of the draft codebook.',
    do: async (ui) => {
      await ui.hover(ui.page.locator('.code-card').first());
      await ui.hover(ui.page.locator('.code-card').nth(1));
      await ui.click(button(ui.page, 'Freeze codebook'));
      await versions(ui.page).first().waitFor();
    }},
  {caption: 'The saved version keeps the definitions used for coding.',
    do: async (ui) => {
      await ui.click(versions(ui.page).first());
      await ui.zoom(ui.page.locator('details.version').first());
    }},
  {caption: 'Choose the intended frozen version before assigning a code.',
    do: async (ui) => { await ui.click(button(ui.page, 'Workspace')); await ui.hover(ui.page.getByLabel('Frozen codebook')); }},
  {caption: 'Later edits change the draft rather than an existing frozen version.',
    do: async (ui) => { await ui.click(button(ui.page, 'Codebook')); await ui.click(button(ui.page, 'Edit Support')); }},
  {caption: 'Refine the wording when your understanding develops.',
    do: async (ui) => {
      await ui.fill(field(ui.page, 'Definition'), '');
      await ui.type(field(ui.page, 'Definition'), 'Practical or emotional help from family, friends or other people.');
    }},
  {caption: 'Freeze again when the revised definitions are ready for use.',
    do: async (ui) => {
      await ui.click(button(ui.page, 'Save draft code'));
      await ui.click(button(ui.page, 'Freeze codebook'));
      await versions(ui.page).nth(1).waitFor();
    }},
  {caption: 'Existing decisions retain their original version and historical code name.',
    do: async (ui) => {
      await ui.hover(versions(ui.page).first());
      await ui.hover(versions(ui.page).nth(1));
      await ui.click(button(ui.page, 'Workspace'));
      await ui.hover(ui.page.getByLabel('Frozen codebook'));
    }},
];
