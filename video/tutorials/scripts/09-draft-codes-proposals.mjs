// Tutorial 9 · Draft codes with proposals (guide §6). Storyboard: ../storyboards/09-draft-codes-proposals.md
// Proposal generation uses the deterministic offline `fake` backend; those steps carry the demonstration tag.
import {button, field, practice} from '../shared.mjs';

export const seed = (q) => practice(q, 'coded');
export const start = '/?project=practice-study';

const panel = (page) => page.getByLabel('Codebook proposals');
const request = (page) => panel(page).locator('details.proposal-request');
const card = (page) => panel(page).locator('article.proposal').first();
const editor = (page, name) => field(page.locator('#code-editor'), name);
const ask = async (ui) => {
  await ui.click(request(ui.page).getByRole('button', {name: 'Ask for proposals', exact: true}));
  await panel(ui.page).getByRole('status').waitFor();
};
const openRequest = async (ui) => {
  if ((await request(ui.page).getAttribute('open')) === null) await ui.click(request(ui.page).locator('summary'));
};

export const steps = [
  {caption: 'A proposal changes nothing until you accept it into the draft codebook.',
    do: async (ui) => { await ui.click(button(ui.page, 'Codebook')); await openRequest(ui); }},
  {caption: 'Drafting proposes new codes from selected passages.', demo: true,
    do: (ui) => ui.select(field(request(ui.page), 'Proposal type'), 'draft')},
  {caption: 'Use the offline fake backend to practice codebook development.', demo: true,
    do: async (ui) => {
      await ui.select(field(request(ui.page), 'Backend'), 'fake');
      await ui.hover(field(request(ui.page), 'Model'));
    }},
  {caption: 'Drafting uses passages from one source and the current code names.', demo: true,
    do: async (ui) => {
      await ui.select(field(request(ui.page), 'Source'), {label: 'practice.csv: row 2'});
      await ui.fill(field(request(ui.page), 'Passages to send'), '1');
    }},
  {caption: 'An optional focus tells the proposal request what to consider.', demo: true,
    do: (ui) => ui.type(field(request(ui.page), 'Focus (optional)'), 'Experiences of support')},
  {caption: 'The returned proposals still require a human decision.', demo: true,
    do: ask},
  {caption: 'Your identity and decision note accompany the proposal decision.',
    do: async (ui) => {
      await ui.fill(field(panel(ui.page), 'Reviewer'), '');
      await ui.type(field(panel(ui.page), 'Reviewer'), 'researcher');
      await ui.type(field(panel(ui.page), 'Decision note (optional)'), 'Practice draft reviewed against the passage.');
    }},
  {caption: 'Read proposed definitions against the data rather than accepting them automatically.', demo: true,
    do: async (ui) => { await ui.hover(card(ui.page).locator('h4')); await ui.hover(card(ui.page).locator('dl.code-fields')); }},
  {caption: 'Supporting passages let you check the proposal against its evidence.', demo: true,
    do: async (ui) => {
      await ui.click(card(ui.page).getByText(/^Supporting passages/));
      await ui.hover(card(ui.page).locator('blockquote').first());
    }},
  {caption: 'Proposal provenance records where the suggested change came from.', demo: true,
    do: async (ui) => {
      await ui.click(card(ui.page).getByText('Proposal provenance'));
      await ui.zoom(card(ui.page).locator('details.provenance'));
      await ui.hover(card(ui.page).getByText('Based on codebook'));
    }},
  {caption: 'The code editor opens with values you can revise before accepting.', demo: true,
    do: (ui) => ui.click(card(ui.page).getByRole('button', {name: 'Review and accept'}))},
  {caption: 'Proposals can miss implicit meaning and blur boundaries between codes.', demo: true,
    do: async (ui) => { for (const name of ['Name', 'Definition', 'Include', 'Exclude']) await ui.hover(editor(ui.page, name)); }},
  {caption: 'Examples in AI proposals are checked against the supplied passages.', demo: true,
    do: async (ui) => {
      await ui.hover(editor(ui.page, 'Positive examples'));
      await ui.hover(editor(ui.page, 'Negative examples'));
    }},
  {caption: 'Acceptance copies the confirmed values into the draft only.', demo: true,
    do: async (ui) => { await ui.click(button(ui.page, 'Accept into draft codebook')); await ui.sleep(800); }},
  {caption: 'Proposals and your decisions remain part of the permanent record.', demo: true,
    do: async (ui) => {
      await ui.hover(ui.page.locator('.code-card').last());
      await ui.click(panel(ui.page).getByText(/^Decided proposals/));
    }},
  {caption: 'Freezing the accepted draft stays a separate human decision.',
    do: async (ui) => { await ui.click(button(ui.page, 'Freeze codebook')); await ui.sleep(800); }},
  {caption: 'Refining suggests revisions to existing code definitions and guidance.', demo: true,
    do: async (ui) => {
      await openRequest(ui);
      await ui.select(field(request(ui.page), 'Proposal type'), 'refine');
    }},
  {caption: 'Refining uses coded and rejected passages with any review notes.', demo: true,
    do: async (ui) => {
      await ui.hover(field(request(ui.page), 'Backend'));
      await ui.click(request(ui.page).getByRole('checkbox', {name: 'Support'}));
    }},
  {caption: 'A revision targets a code supplied in the request.', demo: true,
    do: async (ui) => { await ask(ui); await ui.hover(card(ui.page).locator('h4')); }},
  {caption: 'Compare the suggested boundary with your intended meaning.', demo: true,
    do: async (ui) => { await ui.hover(card(ui.page).locator('dl.code-fields')); await ui.hover(card(ui.page).locator('> p').first()); }},
  {caption: 'Record why the proposed revision does not fit your judgment.',
    do: async (ui) => {
      await ui.fill(field(panel(ui.page), 'Decision note (optional)'), '');
      await ui.type(field(panel(ui.page), 'Decision note (optional)'), 'Keep the existing definition for this practice study.');
    }},
  {caption: 'Rejection keeps the draft unchanged and records your decision.', demo: true,
    do: async (ui) => { await ui.click(card(ui.page).getByRole('button', {name: 'Reject'})); await ui.sleep(800); }},
  {caption: 'Evidence mining runs offline without an AI model.',
    do: async (ui) => { await openRequest(ui); await ui.click(button(ui.page, 'Find evidence in my reviews')); }},
  {caption: 'Evidence proposals need qualifying review or coding patterns.',
    do: async (ui) => {
      await panel(ui.page).getByRole('status').waitFor();
      await ui.hover(panel(ui.page).getByRole('status'));
    }},
  {caption: 'Disclose AI-assisted codebook development in your methods.',
    do: async (ui) => {
      const decided = panel(ui.page).locator('details.version');
      if ((await decided.getAttribute('open')) === null) await ui.click(decided.locator('summary'));
      await ui.hover(decided.locator('p').first());
    }},
];
