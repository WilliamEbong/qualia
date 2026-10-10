// Tutorial 7 · Memos, themes, reflexivity (guide §8). Storyboard: ../storyboards/07-memos-themes-reflexivity.md
import {button, field, practice} from '../shared.mjs';

export const seed = (q) => practice(q, 'coded');
export const start = '/?project=practice-study';

const label = (page, name) => field(page, name);
const text = (page, name) => page.getByRole('textbox', {name, exact: true});
const codeField = (page, name) => field(page.locator('#code-editor'), name);
const saveMemo = async (ui) => {
  await ui.click(button(ui.page, 'Save memo'));
  await ui.sleep(600);
};
const reparent = async (ui, code) => {
  await ui.click(button(ui.page, `Edit ${code}`));
  await ui.select(codeField(ui.page, 'Parent code'), {label: 'Responding to pressure'});
  await ui.click(button(ui.page, 'Save draft code'));
};

export const steps = [
  {caption: 'Keep your interpretation beside the evidence.',
    do: async (ui) => { await ui.click(button(ui.page, 'Memos')); await ui.click(button(ui.page, 'New memo')); }},
  {caption: 'Analytic memos hold interpretations, questions and exceptions.',
    do: async (ui) => {
      await ui.type(text(ui.page, 'Title'), 'Support and pressure');
      await ui.select(label(ui.page, 'Kind'), 'analytic');
    }},
  {caption: 'A memo can hold a question rather than a finished conclusion.',
    do: (ui) => ui.type(text(ui.page, 'Memo'), 'How does help from others change the experience of pressure?')},
  {caption: 'Link the memo to the evidence and concepts it concerns.',
    do: async (ui) => {
      await ui.select(label(ui.page, 'Linked code'), {label: 'Support'});
      await ui.select(label(ui.page, 'Linked case'), {label: 'p03'});
      await ui.select(label(ui.page, 'Linked source'), {label: 'practice.csv: row 4'});
    }},
  {caption: 'Memos can link to a segment, code, case and source.',
    do: async (ui) => { await ui.select(label(ui.page, 'Linked segment'), '3'); await saveMemo(ui); }},
  {caption: 'Revise your interpretation as you read more closely.',
    do: async (ui) => {
      await ui.click(button(ui.page, 'Edit memo').first());
      const memo = text(ui.page, 'Memo');
      await ui.click(memo);
      await memo.press('End');
      await ui.type(memo, ' Look for cases where support does not reduce pressure.');
    }},
  {caption: 'Earlier memo versions remain available with their replacement times.',
    do: async (ui) => {
      await saveMemo(ui);
      await ui.click(ui.page.getByText(/^Earlier versions \(\d+\)$/).first());
    }},
  {caption: 'Reflexive memos record how your position shapes what you notice.',
    do: async (ui) => {
      await ui.click(button(ui.page, 'New memo'));
      await ui.type(text(ui.page, 'Title'), 'My assumptions');
      await ui.select(label(ui.page, 'Kind'), 'reflexive');
    }},
  {caption: 'Describe the assumptions that may affect your interpretation.',
    do: (ui) => ui.type(text(ui.page, 'Memo'), 'I may notice helpful relationships more readily than unresolved stress.')},
  {caption: 'Link a reflexive note to the case or source it concerns.',
    do: async (ui) => {
      await ui.select(label(ui.page, 'Linked case'), {label: 'p01'});
      await ui.select(label(ui.page, 'Linked source'), {label: 'practice.csv: row 2'});
      await saveMemo(ui);
    }},
  {caption: 'Use the kind filter to review one part of your memo record.',
    do: async (ui) => {
      await ui.select(label(ui.page, 'Show'), {label: 'Reflexive memos'});
      await ui.sleep(1200);
      await ui.select(label(ui.page, 'Show'), {label: 'All memo kinds'});
    }},
  {caption: 'Method memos record decisions about sampling, coding and analysis.',
    do: async (ui) => {
      await ui.click(button(ui.page, 'New memo'));
      await ui.type(text(ui.page, 'Title'), 'Unit of comparison');
      await ui.select(label(ui.page, 'Kind'), 'method');
    }},
  {caption: "Make the study's unit of analysis explicit.",
    do: async (ui) => {
      await ui.type(text(ui.page, 'Memo'), 'This practice study compares participants as cases.');
      await saveMemo(ui);
    }},
  {caption: 'A theme is an interpreted pattern relevant to the research question.',
    do: async (ui) => { await ui.click(button(ui.page, 'Codebook')); await ui.type(codeField(ui.page, 'Name'), 'Responding to pressure'); }},
  {caption: 'Develop the pattern through interpretation rather than frequency alone.',
    do: (ui) => ui.type(codeField(ui.page, 'Definition'), 'A provisional pattern connecting experienced demands and help from others.')},
  {caption: 'A parent code can organize the codes supporting a theme.',
    do: async (ui) => {
      await ui.hover(codeField(ui.page, 'Parent code'));
      await ui.click(button(ui.page, 'Save draft code'));
      await ui.page.getByRole('heading', {name: 'Responding to pressure', exact: true}).waitFor();
    }},
  {caption: 'Place a supporting code beneath the proposed theme.',
    do: (ui) => reparent(ui, 'Support')},
  {caption: 'Hierarchy organizes definitions without rolling child counts into the parent.',
    do: (ui) => reparent(ui, 'Pressure')},
  {caption: 'Freeze the revised draft when its definitions are ready for use.',
    do: async (ui) => {
      await ui.click(button(ui.page, 'Freeze codebook'));
      await ui.sleep(800);
      await ui.click(button(ui.page, 'Memos'));
      await ui.click(button(ui.page, 'New memo'));
    }},
  {caption: 'A theme memo explains the pattern and why it matters.',
    do: async (ui) => {
      await ui.type(text(ui.page, 'Title'), 'Responding to pressure: provisional theme');
      await ui.select(label(ui.page, 'Kind'), 'theme');
    }},
  {caption: 'Describe where the proposed pattern holds and where it does not.',
    do: (ui) => ui.type(text(ui.page, 'Memo'), 'Help and pressure meet in these accounts; the short walk offers another response.')},
  {caption: 'Link the theme memo to its parent code.',
    do: async (ui) => {
      await ui.select(label(ui.page, 'Linked code'), {label: 'Responding to pressure'});
      await saveMemo(ui);
    }},
  {caption: 'Retrieve the supporting passages across cases.',
    do: async (ui) => {
      await ui.click(button(ui.page, 'Retrieval'));
      await ui.select(label(ui.page, 'Code'), {label: 'Support'});
      await ui.select(label(ui.page, 'Case'), {label: 'All cases'});
    }},
  {caption: 'Retrieval shows current coded spans with their historical frozen versions.',
    do: async (ui) => {
      await ui.hover(button(ui.page, 'Open in transcript').first());
      await ui.select(label(ui.page, 'Code'), {label: 'Pressure'});
    }},
  {caption: 'Return to the transcript to check the surrounding context.',
    do: (ui) => ui.click(button(ui.page, 'Open in transcript').first())},
  {caption: 'Compare the evidence across cases before settling on a theme.',
    do: async (ui) => { await ui.click(button(ui.page, 'Matrix')); await ui.hover(ui.page.getByRole('table').first()); }},
  {caption: 'Co-occurrence can guide reading, but it does not establish a theme.',
    do: async (ui) => {
      await ui.click(button(ui.page, 'Analysis'));
      await ui.hover(ui.page.getByRole('heading', {name: 'Code co-occurrence'}));
    }},
];
