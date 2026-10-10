// Tutorial 13 · Export, Python/R, backup (guide §11, §16, §18). Storyboard: ../storyboards/13-export-python-r-backup.md
// Steps outside the browser (terminal, file manager) are cards; R is not claimed to have been run.
import {button, field, practice} from '../shared.mjs';

export const seed = (q) => practice(q, 'coded');

const criteria = (page) => page.locator('details', {has: page.locator('summary', {hasText: /^Analysis criteria$/})});
const exportForm = (page) => page.locator('form', {has: button(page, 'Download export')});
const card = (title, ...lines) => ({title, lines});

export const steps = [
  {caption: 'Set the intended analysis scope before downloading related files.',
    do: async (ui) => {
      await ui.select(ui.page.getByLabel('Local project'), 'practice-study');
      await ui.click(button(ui.page, 'Analysis'));
    }},
  {caption: "The exported case table follows the report's selected evidence.",
    do: async (ui) => {
      await ui.hover(field(criteria(ui.page), 'Analysis source'));
      await ui.hover(field(criteria(ui.page), 'Analysis case'));
    }},
  {caption: 'Choose the measurements you want to continue analyzing.',
    do: async (ui) => {
      await ui.click(criteria(ui.page).getByRole('checkbox', {name: 'age'}));
      await ui.click(criteria(ui.page).getByRole('checkbox', {name: 'wellbeing'}));
      await ui.click(button(ui.page, 'Apply analysis criteria'));
    }},
  {caption: 'The CSV has one row per eligible case.',
    do: async (ui) => {
      await ui.hover(ui.page.getByText(/^Applied criteria/).first());
      await ui.click(button(ui.page, 'Download case CSV'));
    }},
  {caption: 'The companion JSON retains criteria, input identity and the column dictionary.',
    do: (ui) => ui.click(button(ui.page, 'Download analysis JSON'))},
  {caption: 'The Python starter uses Python 3.10 or newer and its standard library.',
    do: (ui) => ui.click(button(ui.page, 'Download Python starter'))},
  {caption: 'The R starter uses base R, which must be installed separately.',
    do: (ui) => ui.click(button(ui.page, 'Download R starter'))},
  {caption: 'Keep the files from one report together in a research output folder.',
    card: {title: 'Keep the four files together', lines: ['qualia-analysis.csv', 'qualia-analysis.json', 'qualia-analysis.py', 'qualia-analysis.R']}},
  {caption: 'Analysis exports retain case metadata and query criteria, so they are not anonymous.',
    card: card('Before running anything', 'Review the downloaded data and starter files.')},
  {caption: 'Run the Python starter deliberately outside Qualia.',
    card: {title: 'Continue in Python', lines: ['From the output folder:'], command: 'python qualia-analysis.py qualia-analysis.csv'}},
  {caption: 'The guide does not claim verified R execution in its tested environment.',
    card: {title: 'Continue in R', lines: ['With R installed:'], command: 'Rscript qualia-analysis.R qualia-analysis.csv'}},
  {caption: 'A case table cannot reconstruct every segment-level chart or source excerpt.',
    card: card('What the starters reproduce', 'Numeric summaries, correlations and case-level code prevalence.')},
  {caption: 'If research data changes, refresh and download the related files again as a set.',
    do: (ui) => ui.click(button(ui.page, 'Refresh analysis'))},
  {caption: 'Workspace exports have different privacy defaults from Analysis downloads.',
    do: (ui) => ui.click(button(ui.page, 'Export'))},
  {caption: 'JSON keeps structured research identities and provenance together.',
    do: (ui) => ui.select(field(exportForm(ui.page), 'Format'), 'json')},
  {caption: 'The default export removes source text and free-text content.',
    do: async (ui) => {
      const text = exportForm(ui.page).getByRole('checkbox', {name: 'Include source text and excerpts'});
      await ui.zoom(exportForm(ui.page));
      await ui.hover(text);
    }},
  {caption: 'A bundle adds experiment, evaluation, usage and egress evidence.',
    do: (ui) => ui.click(exportForm(ui.page).getByRole('checkbox', {name: 'Reproducibility bundle'}))},
  {caption: 'Names and identifiers can still be sensitive in a redacted export.',
    do: (ui) => ui.click(button(ui.page, 'Download export'))},
  {caption: 'Exports include proposal decisions and earlier memo versions.',
    card: card('Before sharing', 'Review the downloaded bundle.')},
  {caption: 'Choose the export format that fits the next stage of your work.',
    do: async (ui) => {
      if (!(await exportForm(ui.page).isVisible())) await ui.click(button(ui.page, 'Export'));
      await ui.select(field(exportForm(ui.page), 'Format'), 'csv');
      await ui.hover(exportForm(ui.page).getByRole('checkbox', {name: 'Include source text and excerpts'}));
      await ui.click(button(ui.page, 'Download export'));
    }},
  {caption: 'Even a text-inclusive bundle is not an automatically restorable project.',
    card: card('An export is evidence, not a backup', 'There is no general bundle import.')},
  {caption: 'A complete manual backup begins with all operations finished.',
    card: card('Back up · 1', 'Finish running imports, evaluations and experiments.')},
  {caption: 'Stop the application before copying the research workspace.',
    card: card('Back up · 2', 'Close Qualia and wait about three minutes.', 'Confirm no Qualia command is running.')},
  {caption: 'Use the actual research location if you selected a custom home folder.',
    card: {title: 'Back up · 3', lines: ['Locate the actual QUALIA_HOME folder. The default is:'], command: '%USERPROFILE%\\Qualia'}},
  {caption: 'Include projects, vault, recovery, hidden project .git folders and database sidecars.',
    card: card('Back up · 4', 'Copy the entire home folder to a new, dated backup location.')},
  {caption: 'Do not copy only project.db while the app is running.',
    card: card('Back up · 5', 'Check the copied project folders and files.', 'Keep the original untouched.')},
  {caption: 'Git history and JSON or CSV exports do not replace a full-folder backup.',
    card: card('Back up · 6', 'Protect the backup as research data.', 'Inspect a separate copy, with all instances stopped.')},
  {caption: 'Opening a restored copy can upgrade its database, so retain the original backup.',
    card: card('Inspect a restored copy', 'Select a separate copy as QUALIA_HOME.', 'Preserve the untouched backup.')},
  {caption: 'Do not delete recovery journals, locks or sidecars to bypass an interruption.',
    card: card('If a recovery is pending', 'Preserve the workspace and recovery directory, then seek help.')},
];
