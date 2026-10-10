// Tutorial 8 · AI suggestions and review queue (guide §12). Storyboard: ../storyboards/08-ai-suggestions-review.md
// Every classification uses the deterministic offline `fake` backend; those steps carry the demonstration tag.
import {button, field, practice, source} from '../shared.mjs';

export const seed = (q) => practice(q, 'frozen');

const review = (page) => page.getByRole('button', {name: /^Review/}).first();
const card = (page) => page.locator('article.suggestion').first();
const classify = async (ui) => {
  await ui.select(field(ui.page, 'Backend'), 'fake');
  await ui.select(field(ui.page, 'Scope'), 'source');
  await ui.click(button(ui.page, 'Run classification'));
  await ui.page.getByRole('status').filter({hasText: 'Classification'}).waitFor();
};

// Slower pacing keeps this short tutorial near two minutes.
export const pace = 1.1;

export const steps = [
  {caption: 'Suggestions require a frozen codebook and imported passages.',
    do: async (ui) => {
      await ui.select(ui.page.getByLabel('Local project'), 'practice-study');
      await ui.click(button(ui.page, 'Workspace'));
    }},
  {caption: 'Start with one small source.',
    do: (ui) => ui.click(source(ui.page, 0))},
  {caption: 'Classification proposes codes for you to review.',
    do: (ui) => ui.click(review(ui.page))},
  {caption: 'The fake backend is an offline deterministic demonstration.', demo: true,
    do: async (ui) => {
      await ui.click(ui.page.getByText('Backend availability and privacy'));
      await ui.hover(ui.page.locator('details p strong', {hasText: /^fake$/}));
    }},
  {caption: 'Fake suggestions are practice output, not research-quality recommendations.', demo: true,
    do: async (ui) => {
      await ui.click(ui.page.getByText('Backend availability and privacy'));
      await ui.select(field(ui.page, 'Backend'), 'fake');
    }},
  {caption: "Classification uses the project's latest frozen codebook.", demo: true,
    do: async (ui) => {
      await ui.select(field(ui.page, 'Scope'), 'source');
      await ui.hover(field(ui.page, 'Model'));
    }},
  {caption: 'A suggestion does not become current coding until you accept it.', demo: true,
    do: async (ui) => {
      await ui.click(button(ui.page, 'Run classification'));
      await ui.page.getByRole('status').filter({hasText: 'Classification'}).waitFor();
    }},
  {caption: 'The result reports suggestions, segments, calls and cache hits.', demo: true,
    do: async (ui) => { await ui.hover(ui.page.getByRole('status').filter({hasText: 'Classification'})); await ui.hover(card(ui.page)); }},
  {caption: 'Your review identity becomes part of the decision history.', demo: true,
    do: async (ui) => { await ui.fill(field(ui.page, 'Reviewer'), ''); await ui.type(field(ui.page, 'Reviewer'), 'researcher'); }},
  {caption: 'Read the passage and rationale together before deciding.', demo: true,
    do: async (ui) => {
      await ui.click(card(ui.page).locator('.suggestion-select'));
      await ui.hover(card(ui.page).locator('blockquote'));
    }},
  {caption: 'Model-reported scores are not measured accuracy.', demo: true,
    do: async (ui) => {
      await ui.zoom(card(ui.page).locator('.caption').first());
      await ui.hover(card(ui.page).getByText(/^suggested ·/));
    }},
  {caption: 'Missing calibration is not evidence of perfect accuracy.', demo: true,
    do: (ui) => ui.hover(card(ui.page).locator('p.caption').nth(1))},
  {caption: 'Provenance records the model and frozen definitions behind the suggestion.', demo: true,
    do: async (ui) => {
      await ui.click(card(ui.page).getByText('Suggestion provenance'));
      await ui.hover(card(ui.page).getByText('Backend / model'));
    }},
  {caption: 'Check the source context before accepting or rejecting a suggestion.', demo: true,
    do: (ui) => ui.click(card(ui.page).getByRole('button', {name: 'Open segment'}))},
  {caption: 'A review note records the reason for your decision.', demo: true,
    do: async (ui) => {
      await ui.click(review(ui.page));
      await ui.type(field(ui.page, 'Review note (optional)'), 'Practice acceptance after checking context.');
    }},
  {caption: 'Acceptance creates a current coding decision with the model identity and reviewer.', demo: true,
    do: async (ui) => {
      await ui.click(card(ui.page).locator('.suggestion-select'));
      await ui.click(card(ui.page).getByRole('button', {name: /^Accept/}));
      await ui.sleep(800);
    }},
  {caption: 'The original suggestion remains in history after review.', demo: true,
    do: async (ui) => {
      await ui.click(button(ui.page, 'Workspace'));
      await ui.click(ui.page.locator('.segment-text').first());
      await ui.hover(ui.page.getByRole('heading', {name: 'Current assignments'}));
      await ui.hover(ui.page.getByRole('heading', {name: 'Provenance'}));
    }},
  {caption: 'A second source lets you practice rejecting a suggestion.', demo: true,
    do: async (ui) => { await ui.click(source(ui.page, 1)); await ui.click(review(ui.page)); }},
  {caption: 'Keep this practice run local and limited to the selected source.', demo: true,
    do: classify},
  {caption: 'Every suggestion still needs your decision, whatever its score.', demo: true,
    do: async (ui) => {
      await ui.click(card(ui.page).locator('.suggestion-select'));
      await ui.hover(card(ui.page).locator('blockquote'));
      await ui.click(card(ui.page).getByText('Suggestion provenance'));
    }},
  {caption: 'Typing in a form does not trigger review shortcuts.', demo: true,
    do: async (ui) => {
      await ui.fill(field(ui.page, 'Review note (optional)'), '');
      await ui.type(field(ui.page, 'Review note (optional)'), 'Practice rejection after checking the passage.');
      await ui.page.locator(':focus').blur();
    }},
  {caption: 'Rejection appends review evidence without creating a current assignment.', demo: true,
    do: async (ui) => {
      await ui.click(card(ui.page).locator('.suggestion-select'));
      await ui.press('r');
      await ui.sleep(800);
    }},
  {caption: 'Review resolves the same suggestion across any groups where it appeared.', demo: true,
    do: async (ui) => {
      await ui.click(button(ui.page, 'Workspace'));
      await ui.click(source(ui.page, 1));
      await ui.click(ui.page.locator('.segment-text').first());
      await ui.hover(ui.page.getByRole('heading', {name: 'Provenance'}));
    }},
];
