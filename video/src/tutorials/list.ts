// The tutorial series in order. Ids match tutorials/scripts/NN-*.mjs and public/recordings/NN.json.
// Chapters: [first step, title]; listed on the intro and announced by a card before each later part.
export const tutorials: {id: string; title: string; guide: string; chapters: [number, string][]}[] = [
  {id: '01', title: 'Install and open', guide: '§2',
    chapters: [[1, 'Download and install'], [7, 'Open Qualia'], [10, 'Close and reopen'], [13, 'Where your work lives']]},
  {id: '02', title: 'First project in 5 minutes', guide: '§3',
    chapters: [[1, 'Create the project'], [4, 'Import the practice data'], [11, 'Build the codebook'], [15, 'Code the responses'], [19, 'Read the analysis']]},
  {id: '03', title: 'Import material', guide: '§4',
    chapters: [[1, 'Plain text'], [7, 'Markdown'], [9, 'Mapped CSV'], [14, 'Repeats and revisions']]},
  {id: '04', title: 'Cases and attributes', guide: '§5',
    chapters: [[1, 'Edit a case'], [9, 'Filter by case'], [10, 'Create a case']]},
  {id: '05', title: 'Build and freeze a codebook', guide: '§6',
    chapters: [[1, 'Define a code'], [10, 'Freeze the codebook'], [15, 'Revise and freeze again']]},
  {id: '06', title: 'Code by keyboard', guide: '§7',
    chapters: [[1, 'Set up'], [6, 'Code with keys'], [12, 'Code a span'], [15, 'Correct a decision'], [20, 'New code from a passage']]},
  {id: '07', title: 'Memos, themes, reflexivity', guide: '§8',
    chapters: [[1, 'An analytic memo'], [8, 'Reflexive and method memos'], [14, 'Build a theme'], [23, 'Retrieve the evidence']]},
  {id: '08', title: 'AI suggestions and review queue', guide: '§12',
    chapters: [[1, 'Run classification'], [9, 'Review a suggestion'], [18, 'Reject a suggestion']]},
  {id: '09', title: 'Draft codes with proposals', guide: '§6',
    chapters: [[1, 'Draft new codes'], [11, 'Accept a proposal'], [17, 'Refine a code'], [23, 'Find evidence offline']]},
  {id: '10', title: 'Evaluation explained', guide: '§14',
    chapters: [[1, 'Run an evaluation'], [6, 'Read the metrics'], [13, 'Provenance and calibration'], [16, 'Check repeatability']]},
  {id: '11', title: 'Experiments: KEEP or REVERT', guide: '§15',
    chapters: [[1, 'Run an experiment'], [6, 'Read the decision'], [16, 'Tune thresholds']]},
  {id: '12', title: 'Matrix and Analysis workbench', guide: '§9–10',
    chapters: [[1, 'The matrix'], [5, 'Frequencies and evidence'], [9, 'Filter the analysis'], [17, 'Groups and co-occurrence'], [22, 'Words and numbers']]},
  {id: '13', title: 'Export, Python/R, backup', guide: '§11, §16, §18',
    chapters: [[1, 'Download analysis files'], [8, 'Continue in Python or R'], [13, 'Export the project'], [21, 'Back up your work']]},
];

// Written by tutorials/record.mjs.
export type Card = {title: string; lines: string[]; command?: string; terminal?: boolean};
export type Box = {x: number; y: number; width: number; height: number};
// One on-screen action in viewport CSS pixels; action null means "frame this region" without a caption.
export type Action = {verb: string; value?: string; target?: string};
export type Event = {t: number; action: Action | null; box: Box | null};
export type Step = {
  caption: string;
  demo: boolean;
  card: Card | null;
  cardMs?: number;
  rate?: number;
  startMs: number;
  endMs: number;
};
export type Timeline = {id: string; video: string; view: {width: number; height: number}; steps: Step[]; events: Event[]};
