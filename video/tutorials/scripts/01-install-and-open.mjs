// Tutorial 1 · Install and open (guide §2). Storyboard: ../storyboards/01-install-and-open.md
// The installer and Windows steps cannot be shown in the browser, so they are cards; the app itself is recorded
// with the AnnoMI demonstration project the installer adds.
import {button} from '../shared.mjs';

export const seed = ({cli}) => cli('demo');

const card = (title, ...lines) => ({title, lines});
const catalogue = (page) => page.getByRole('heading', {name: 'Project catalogue'});

// Slower pacing keeps this short tutorial near two minutes.
export const pace = 1.25;

export const steps = [
  {caption: 'Download the latest release zip for Windows.',
    card: {title: 'Download', lines: ['Download the latest Qualia-<version>.zip from the Releases page:'],
      command: 'github.com/WilliamEbong/qualia/releases'}},
  {caption: 'Unblock the downloaded zip before extracting it.',
    card: card('Unblock', 'Right-click the zip, choose Properties,', 'tick Unblock and select OK.')},
  {caption: 'Keep the application in a folder you will retain.',
    card: {title: 'Extract', lines: ['Extract the zip to a folder you will keep, for example:'], command: 'Documents\\Qualia'}},
  {caption: 'The installer explains each step as it runs.',
    card: card('Install', 'Open that folder and double-click Install Qualia.')},
  {caption: 'The installer adds the tools Qualia needs and the AnnoMI demonstration project.',
    card: card('First run', 'Needs internet access and takes a few minutes.', 'If a step fails, the window says what to do. Re-running is safe.')},
  {caption: 'Qualia opens automatically when installation finishes.',
    card: card('Shortcuts', 'A Qualia icon appears on your Desktop and in the Start menu.')},
  {caption: 'The demonstration lets you explore public research material locally.',
    do: async (ui) => { await ui.hover(catalogue(ui.page)); await ui.hover(ui.page.locator('.project-drawer').first()); }},
  {caption: "Use Qualia's own window for your research.",
    do: async (ui) => {
      await ui.select(ui.page.getByLabel('Local project'), 'demo');
      await ui.click(button(ui.page, 'Workspace'));
    }},
  {caption: 'Manual coding does not require an AI account.',
    do: async (ui) => { await ui.click(button(ui.page, 'Home')); await ui.hover(catalogue(ui.page)); }},
  {caption: 'Closing the window lets Qualia shut itself down.',
    card: card('Close', 'Close the Qualia window.', 'Qualia shuts itself down within about three minutes.')},
  {caption: 'The same icon opens your local workspace again.',
    card: card('Open again', 'Double-click the Qualia icon.')},
  {caption: 'Each local project keeps its material, codebook and history together.',
    do: async (ui) => {
      await ui.page.reload();
      await ui.page.waitForLoadState('networkidle');
      await ui.select(ui.page.getByLabel('Local project'), 'demo');
    }},
  {caption: 'Research workspaces are stored separately from the application folder.',
    card: {title: 'Where your work is stored', lines: ['Projects and their protected data live in your Qualia home folder:'],
      command: '%USERPROFILE%\\Qualia\\projects\n%USERPROFILE%\\Qualia\\vault'}},
  {caption: 'Updating keeps your separately stored research projects.',
    card: card('Update', 'Extract the newer release and double-click Install Qualia again.')},
];
