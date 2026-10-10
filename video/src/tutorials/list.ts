// The tutorial series in order. Ids match tutorials/scripts/NN-*.mjs and public/recordings/NN.json.
export const tutorials = [
  {id: '01', title: 'Install and open', guide: '§2'},
  {id: '02', title: 'First project in 5 minutes', guide: '§3'},
  {id: '03', title: 'Import material', guide: '§4'},
  {id: '04', title: 'Cases and attributes', guide: '§5'},
  {id: '05', title: 'Build and freeze a codebook', guide: '§6'},
  {id: '06', title: 'Code by keyboard', guide: '§7'},
  {id: '07', title: 'Memos, themes, reflexivity', guide: '§8'},
  {id: '08', title: 'AI suggestions and review queue', guide: '§12'},
  {id: '09', title: 'Draft codes with proposals', guide: '§6'},
  {id: '10', title: 'Evaluation explained', guide: '§14'},
  {id: '11', title: 'Experiments: KEEP or REVERT', guide: '§15'},
  {id: '12', title: 'Matrix and Analysis workbench', guide: '§9–10'},
  {id: '13', title: 'Export, Python/R, backup', guide: '§11, §16, §18'},
];

// Written by tutorials/record.mjs.
export type Card = {title: string; lines: string[]; command?: string};
export type Step = {
  caption: string;
  demo: boolean;
  zoom: {x: number; y: number; width: number; height: number} | null;
  card: Card | null;
  cardMs?: number;
  rate?: number;
  startMs: number;
  endMs: number;
};
export type Timeline = {id: string; video: string; steps: Step[]};
