// Tutorial 11 · Experiments: KEEP or REVERT (guide §15). Storyboard: ../storyboards/11-experiments-keep-revert.md
// The seed runs one real offline experiment (fake operator and fake classifier) so the app shows its recorded
// decision; the command cards show that run's actual outcome, never a promised one.
import {button, field} from '../shared.mjs';

const IMPROVE = 'uv run qualia improve --project demo --agent fake --backend fake --budget 1';
const HISTORY = 'uv run qualia history --project demo';
const outcome = {title: 'Recorded outcome', lines: [], command: ''};
const history = {title: 'Experiment history', lines: ['The command prints every recorded attempt as JSON, including:'], command: HISTORY};

export const seed = ({cli}) => {
  cli('demo');
  const [run] = JSON.parse(cli('improve', '--project', 'demo', '--agent', 'fake', '--backend', 'fake', '--budget', '1'));
  outcome.lines = [`Decision: ${run.decision} · ${run.slug}`, `Reason: ${run.reason}`, `Tag: ${run.tag || 'none'}`];
  history.command = `${HISTORY}\n# ${run.id} · ${run.slug} · ${run.decision} · agent ${run.agent}`;
};

const attempts = (page) => page.getByLabel('Recorded attempts');
const provenance = (page) => page.locator('details', {has: page.getByText('Experiment provenance', {exact: true})});
const table = (page) => page.getByRole('table', {name: 'Experiment measurement comparison', exact: true});
const LONG = 240_000;

export const steps = [
  {caption: 'Experiments measure changes to implementation configuration and prompts.',
    do: async (ui) => {
      await ui.select(ui.page.getByLabel('Local project'), 'demo');
      await ui.click(button(ui.page, 'Experiments'));
    }},
  {caption: 'Save and review intended workspace changes before starting an experiment.',
    card: {title: 'Before running', lines: ['A prepared validation benchmark', 'A clean project Git baseline', 'Enough local budget']}},
  {caption: 'Use the fake operator and classifier to practice offline.', demo: true,
    card: {title: 'Run one offline experiment', lines: ['From the application folder:'], command: IMPROVE}},
  {caption: "Qualia's measured policy decides KEEP or REVERT automatically.", demo: true, card: outcome},
  {caption: 'History retains the attempt and its measured decision.', demo: true, card: history},
  {caption: 'Completed attempts appear with their evidence in the experiment history.', demo: true,
    do: (ui) => ui.hover(ui.page.getByRole('heading', {name: 'Experiment history'}))},
  {caption: 'Read the recorded decision rather than assuming a gain was kept.', demo: true,
    do: (ui) => ui.click(attempts(ui.page).getByRole('button').first())},
  {caption: 'REVERT is a valid outcome, not an instruction to bypass the policy.', demo: true,
    do: (ui) => ui.hover(attempts(ui.page).locator('.decision-caption').first())},
  {caption: 'The hypothesis is a proposed explanation rather than proof of improvement.', demo: true,
    do: (ui) => ui.hover(ui.page.getByRole('heading', {name: 'Operator hypothesis'}))},
  {caption: 'A candidate gain alone does not establish a KEEP decision.', demo: true,
    do: async (ui) => {
      for (const col of ['Baseline', 'Candidate', 'Confirmation']) await ui.hover(table(ui.page).getByRole('columnheader', {name: col}));
    }},
  {caption: 'One improved metric is not a blanket claim of better qualitative judgment.', demo: true,
    do: async (ui) => {
      await ui.hover(table(ui.page).getByRole('rowheader', {name: /^Macro F1/}));
      await ui.hover(table(ui.page).getByRole('rowheader', {name: /^Exact code-set/}));
    }},
  {caption: 'Unavailable measurements must not be inferred from the hypothesis.', demo: true,
    do: (ui) => ui.hover(table(ui.page))},
  {caption: 'Experiments do not authorize changes to research code definitions or methodology.', demo: true,
    do: (ui) => ui.hover(ui.page.getByRole('heading', {name: 'Changed files'}))},
  {caption: 'The recorded identities distinguish the operator from the validation classifier.', demo: true,
    do: async (ui) => {
      await ui.click(ui.page.getByText('Experiment provenance', {exact: true}));
      await ui.zoom(provenance(ui.page).locator('dl'));
      for (const term of ['Operator', 'Baseline backend / model', 'Candidate backend / model']) {
        await ui.hover(provenance(ui.page).locator('dt', {hasText: term}).first());
      }
    }},
  {caption: 'Kept changes receive a local commit and tag while rejected evidence remains.', demo: true,
    do: async (ui) => {
      for (const term of ['Commit', 'Tag', 'Frozen codebook']) await ui.hover(provenance(ui.page).locator('dt', {hasText: term}).first());
    }},
  {caption: 'Threshold tuning fits cutoffs on dev data and measures them on validation data.', demo: true,
    do: async (ui) => {
      await ui.hover(ui.page.getByRole('heading', {name: 'Tune suggestion thresholds'}));
      await ui.select(field(ui.page, 'Classifier to tune'), 'fake');
    }},
  {caption: 'Tuning needs dev and validation benchmarks and a clean project Git state.', demo: true, timeout: LONG, fast: true,
    do: async (ui) => {
      await ui.click(button(ui.page, 'Tune thresholds'));
      await attempts(ui.page).getByRole('listitem').nth(1).waitFor({timeout: LONG});
    }},
  {caption: 'Fake uses constant scores, so threshold tuning rarely helps it.', demo: true,
    do: async (ui) => {
      await ui.hover(attempts(ui.page).getByRole('button').first());
      await ui.hover(ui.page.getByRole('heading', {name: 'Measured validation results'}));
    }},
  {caption: 'An interrupted operation requires recovery rather than bypassing its safeguards.',
    card: {title: 'If an experiment is interrupted', lines: ['Qualia reports a pending recovery.', 'Preserve the workspace and the recovery evidence.', 'Do not remove the lock file.']}},
];
