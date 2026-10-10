// Tutorial 10 · Evaluation explained (guide §14). Storyboard: ../storyboards/10-evaluation.md
// The AnnoMI demo project with its validation benchmark; every run uses the deterministic offline `fake` backend.
import {button, field} from '../shared.mjs';

export const seed = ({cli}) => cli('demo');

// Each metric's row header also holds its one-line explanation.
const metric = (page, name) => page.getByRole('table', {name: 'Validation metrics', exact: true}).getByRole('rowheader', {name: new RegExp(`^${name}`)});
const perCode = (page) => page.getByRole('table', {name: 'Per-code validation metrics', exact: true});
const repeat = (page) => page.getByLabel('Repeatability check');
const LONG = 240_000;

// Slower pacing keeps this short tutorial near two minutes.
export const pace = 1.2;

export const steps = [
  {caption: 'Evaluation measures predictions against separately supplied reference labels.',
    do: async (ui) => {
      await ui.select(ui.page.getByLabel('Local project'), 'demo');
      await ui.click(button(ui.page, 'Evaluation'));
    }},
  {caption: 'Evaluation predictions do not become research coding assignments.',
    do: (ui) => ui.hover(ui.page.getByRole('heading', {name: 'Evaluate validation split'}))},
  {caption: 'Fake is a synthetic test backend for practicing the workflow.', demo: true,
    do: (ui) => ui.select(field(ui.page, 'Evaluation backend'), 'fake')},
  {caption: 'A successful evaluation requires complete coverage of the validation records.', demo: true, timeout: LONG, fast: true,
    do: async (ui) => {
      await ui.hover(field(ui.page, 'Model'));
      await ui.click(button(ui.page, 'Run validation evaluation'));
      await metric(ui.page, 'Macro F1').waitFor({timeout: LONG});
    }},
  {caption: 'The local demo validation split contains 1,258 utterances.', demo: true,
    do: (ui) => ui.hover(field(ui.page, 'Recorded validation run'))},
  {caption: 'Macro F1 averages over every code, so rare codes count equally.', demo: true,
    do: (ui) => ui.hover(metric(ui.page, 'Macro F1'))},
  {caption: 'Micro F1 pools code decisions, giving common codes more weight.', demo: true,
    do: async (ui) => { await ui.hover(metric(ui.page, 'Micro F1')); await ui.hover(metric(ui.page, 'Macro F1')); }},
  {caption: 'Exact and partial matching answer different questions.', demo: true,
    do: async (ui) => {
      await ui.hover(metric(ui.page, 'Exact code-set match'));
      await ui.hover(metric(ui.page, 'Partial match'));
    }},
  {caption: 'Reference-versus-prediction agreement is not human intercoder reliability.', demo: true,
    do: async (ui) => {
      await ui.hover(metric(ui.page, 'Cohen kappa'));
      await ui.hover(metric(ui.page, 'Nominal alpha'));
      await ui.hover(ui.page.getByText(/^Alpha basis:/));
    }},
  {caption: 'Read performance together with the number of reference examples for each code.', demo: true,
    do: async (ui) => {
      await ui.hover(ui.page.getByRole('heading', {name: 'Per-code performance'}));
      await ui.hover(perCode(ui.page).getByRole('columnheader', {name: 'Support'}));
    }},
  {caption: 'Wide 95 percent Wilson intervals signal fewer examples and more uncertainty.', demo: true,
    do: async (ui) => {
      await ui.zoom(perCode(ui.page));
      await ui.hover(perCode(ui.page).getByRole('row').nth(1));
    }},
  {caption: 'Calibration describes this validation set rather than guaranteed future accuracy.', demo: true,
    do: (ui) => ui.hover(metric(ui.page, 'Validation ECE'))},
  {caption: 'Provenance binds the result to its benchmark, codebook and classifier identity.', demo: true,
    do: (ui) => ui.click(ui.page.getByText('Evaluation provenance and metric definitions'))},
  {caption: 'Use the recorded identities when comparing or reproducing a run.', demo: true,
    do: async (ui) => {
      for (const term of ['Backend / model', 'Frozen codebook', 'Benchmark hash']) {
        await ui.hover(ui.page.locator('dt', {hasText: term}).first());
      }
    }},
  {caption: 'Compare model-reported scores with how often suggestions matched the reference.', demo: true,
    do: async (ui) => {
      const table = ui.page.getByRole('table', {name: 'Calibration by score band', exact: true});
      await ui.hover(table.getByRole('columnheader', {name: 'Mean score'}));
      await ui.hover(table.getByRole('columnheader', {name: 'Correct'}));
    }},
  {caption: 'Repeatability asks whether the same model makes the same decisions twice.', demo: true,
    do: async (ui) => {
      await ui.fill(field(repeat(ui.page), 'Passages in the sample'), '');
      await ui.type(field(repeat(ui.page), 'Passages in the sample'), '50');
    }},
  {caption: 'The check classifies the same sample twice without stored answers.', demo: true, timeout: LONG, fast: true,
    do: async (ui) => {
      await ui.hover(field(ui.page, 'Evaluation backend'));
      await ui.click(repeat(ui.page).getByRole('button', {name: 'Check repeatability'}));
      await ui.page.getByRole('table', {name: 'Run-to-run agreement by code', exact: true}).waitFor({timeout: LONG});
    }},
  {caption: 'The sample stays the same for a project so comparisons are fair.', demo: true,
    do: async (ui) => {
      await ui.hover(repeat(ui.page).getByText(/Identical code sets/).first());
      await ui.hover(ui.page.getByRole('table', {name: 'Run-to-run agreement by code', exact: true}));
    }},
  {caption: 'Kappa is unavailable when neither run varies for a code.', demo: true,
    do: async (ui) => {
      const table = ui.page.getByRole('table', {name: 'Run-to-run agreement by code', exact: true});
      await ui.hover(table.getByRole('columnheader', {name: 'Same decision'}));
      await ui.hover(table.getByRole('columnheader', {name: 'Kappa between runs'}));
    }},
  {caption: 'Deterministic fake results demonstrate the workflow rather than model quality.', demo: true,
    do: async (ui) => { await ui.hover(field(ui.page, 'Recorded validation run')); await ui.hover(metric(ui.page, 'Macro F1')); }},
];
