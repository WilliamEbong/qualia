// Helpers shared by the tutorial scripts.
import fs from 'node:fs';
import path from 'node:path';

// The synthetic practice study from guide §3.
export const PRACTICE_CSV = `text,case,speaker,group,age,wellbeing
"My sister gives me support when work feels stressful.",p01,Participant,north,24,4
"I feel pressure at work and take a short walk afterward.",p02,Participant,south,36,6
"Support from friends helps me manage pressure.",p03,Participant,north,48,8
`;

export const writePractice = (work) => {
  const file = path.join(work, 'practice.csv');
  fs.writeFileSync(file, PRACTICE_CSV);
  return file;
};

// Seeds practice-study with the CLI up to a stage of guide §3: created, imported, frozen or coded.
export const practice = ({cli, work}, stage) => {
  const reached = (s) => ['created', 'imported', 'frozen', 'coded'].indexOf(stage) >= ['created', 'imported', 'frozen', 'coded'].indexOf(s);
  const p = ['--project', 'practice-study'];
  cli('init', 'practice-study');
  if (reached('imported')) cli('import', writePractice(work), ...p, '--attribute-columns', 'group,age,wellbeing');
  if (reached('frozen')) {
    cli('codebook', 'add', 'Support', '--definition', 'Practical or emotional help from other people.', ...p);
    cli('codebook', 'add', 'Pressure', '--definition', 'Experienced demands or stress.', ...p);
    cli('codebook', 'freeze', ...p);
  }
  // Segments 1–3 are the three rows; codes 1 and 2 are Support and Pressure.
  if (reached('coded')) for (const [segment, code] of [[1, 1], [2, 2], [3, 1], [3, 2]]) cli('code', segment, code, ...p);
};

export const button = (page, name) => page.getByRole('button', {name, exact: true});
export const source = (page, n) => page.getByLabel('Sources and cases').locator('li button').nth(n);
export const segmentText = (page, n) => page.getByLabel(`Segment ${n}`, {exact: true}).locator('.segment-text');
export const code = (page, name) => page.locator('.code-shortcut', {hasText: name});
// Coding buttons are disabled while a decision saves.
export const saved = (page) => page.waitForFunction(() => !document.querySelector('.code-shortcut[disabled]'));
// A form control by the start of its label (a select's accessible name also contains its selected option).
export const field = (scope, name) => scope.getByLabel(new RegExp(`^${name.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}`));
