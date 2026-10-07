# Qualia user guide

**Qualitative coding you can audit.**

Qualia helps you read research material, apply your own codebook, keep analytic notes, compare patterns across cases, and trace results back to the passages and decisions that produced them. You can work manually without an AI account. Optional classifiers produce suggestions for you to review; they do not decide your methodology.

This guide is for researchers running Qualia on their own computer. Commands are shown for Windows PowerShell; other platforms work the same way with their usual paths. It describes implemented workflows and their limits. Messages in the app are authoritative: native Claude/Codex classification and improvement work with current versions of Claude Code and Codex (at least Claude Code 2.1.284 and Codex 0.160.0), need your own subscription sign-in and project permission, and record the CLI version used for each run, and Jev needs its own TypeSafe account and key ([section 13](#13-set-up-optional-jev-processing)). See [build status](BUILD-STATE.md) for verification evidence.

**Use Qualia's own window for your research.** Start it with the **Qualia** icon (or `uv run qualia app`), then use its Workspace, Codebook, Review and Analysis views. You do not need to keep an AI desktop app open. Native classification launches the installed Codex or Claude CLI as a local subprocess and lets that CLI use its existing official sign-in; it does not ask you to paste a subscription token into Qualia. Follow [AI backend setup](#12-generate-and-review-ai-suggestions) before using it.

Screenshots are cropped from the bundled AnnoMI demonstration project. Review suggestions come from the offline fake backend; evaluation, calibration and threshold-tuning results come from a real Jev run on the demo's validation split.

## Find the workflow you need

- [Understand the basic concepts](#1-understand-the-basic-concepts)
- [Install and open Qualia](#2-install-and-open-qualia)
- [Try a small practice study](#3-try-a-small-practice-study)
- [Import your material](#4-import-your-material)
- [Organize cases and attributes](#5-organize-cases-and-attributes)
- [Create and freeze a codebook](#6-create-and-freeze-a-codebook), including [AI and evidence proposals](#draft-and-refine-codes-with-proposals)
- [Code passages manually](#7-code-passages-manually), including [creating a code while reading](#create-a-code-while-reading)
- [Write memos and retrieve evidence](#8-write-memos-and-retrieve-evidence), including [themes](#build-themes) and [reflexivity](#keep-a-reflexive-record)
- [Compare codes in the matrix](#9-compare-codes-in-the-matrix)
- [Use the Analysis workbench](#10-use-the-analysis-workbench)
- [Continue in Python or R](#11-continue-in-python-or-r)
- [Generate and review AI suggestions](#12-generate-and-review-ai-suggestions)
- [Set up optional Jev processing](#13-set-up-optional-jev-processing)
- [Evaluate a classifier against reference labels](#14-evaluate-a-classifier-against-reference-labels)
- [Understand improvement experiments](#15-understand-improvement-experiments)
- [Export a project or reproducibility bundle](#16-export-a-project-or-reproducibility-bundle)
- [Understand the static demonstration](#17-understand-the-static-demonstration)
- [Back up your work and handle interruptions](#18-back-up-your-work-and-handle-interruptions)
- [Troubleshoot common problems](#19-troubleshoot-common-problems)
- [Understand how Qualia works](#20-understand-how-qualia-works)
- [Command and keyboard reference](#21-command-and-keyboard-reference)

## 1. Understand the basic concepts

| Term | Meaning in Qualia |
|---|---|
| Project | A separate local research workspace with its own material, codebook, settings and history. |
| Source | Imported text, such as an interview or a CSV text record. Source text is preserved; revised content becomes another source. |
| Segment | A passage within a source. The default import method splits text at blank lines. |
| Span | A selected part of a segment. You can code a span or the whole segment. |
| Case | Your unit of comparison: a participant, organization, site, interview or another explicitly chosen unit. A case links to sources. |
| Attribute | A named value on a case or source, such as `group=north` or `age=36`. Analysis uses case attributes. |
| Code | A researcher-defined label, with a definition and optional inclusion/exclusion rules and examples. |
| Frozen codebook | An immutable version of your code definitions. Coding decisions record which version they used. |
| Codebook proposal | A suggested new code or revision, from AI or from evidence in your own reviews. It changes nothing until you accept it into the draft codebook. |
| Memo kind | Analytic, reflexive, theme or method. Memos can link to a segment, code, case and source, and keep their earlier versions. |
| Theme | An interpreted pattern relevant to your research question. In Qualia it is a parent code with the codes that support it, plus a theme memo; it is more than a topic label or a frequent word. |
| Current assignment | A manual assignment or accepted suggestion that has not been removed for that exact code/span. |
| Suggestion | A proposed model code awaiting human review. It does not count as current coding. |
| Model-reported score | The number a classifier attaches to a suggestion (0–1). It is the model's own signal, not measured accuracy. |
| Suggestion threshold | Optional per-code minimum score for a code to become a suggestion at all (`code_thresholds`). Jev uses 0.5 unless you set one. |
| Review threshold | Suggestions scoring below it (`human_review_below`, default 0.70) are flagged **Below review threshold**. Every suggestion still needs your decision. |
| Provenance | The record of who did what, on which span, using which codebook and, when applicable, which model and prompt. |
| Benchmark | Separate examples with reference labels for measuring a classifier. It is not the same as your live coding workspace. |

Qualia provides several familiar NVivo-style workflows: text coding, hierarchical codes, cases and attributes, memos, coded-text retrieval, a code-by-case matrix, text/code queries, word frequency, co-occurrence, group comparisons and descriptive numeric analysis. It does not currently import proprietary NVivo project files, code audio/video, offer unrestricted statistical modeling, or provide simultaneous multi-user collaboration. Code hierarchy organizes definitions; it does not automatically roll child codes into parent counts.

## 2. Install and open Qualia

### Install on Windows (no terminal needed)

1. Download the latest `Qualia-<version>.zip` from the [Releases page](https://github.com/WilliamEbong/qualia/releases).
2. Right-click the downloaded zip, choose **Properties**, tick **Unblock** and select **OK**. This prevents Windows security prompts for each file.
3. Extract the zip to a folder you will keep, for example `Documents\Qualia`.
4. Open that folder and double-click **Install Qualia**.

A window explains each step: it installs the tools Qualia needs (uv, Python and, if missing, Git, for which Windows may ask permission), installs Qualia, adds the AnnoMI demonstration project, and creates a **Qualia** icon on your Desktop and in the Start menu. The first run needs internet access and takes a few minutes. Qualia then opens by itself. If a step fails, the window says what to do; fix it and double-click **Install Qualia** again. Re-running is always safe.

You do not need Claude, Codex, Jev or R for manual coding.

### Open and close Qualia

Double-click the **Qualia** icon. Qualia opens in its own window with no tabs or address bar, using Google Chrome if that is your default browser and Microsoft Edge otherwise. If neither is installed, it opens in your default browser.

To stop Qualia, close its window. Qualia notices that no window is open and shuts itself down within about three minutes; nothing keeps running in the background. Opening the icon again during that time simply reopens a window.

### Update or remove Qualia

- **Update:** download the newer zip, extract it to the same folder (replace the files) or a new one, and double-click **Install Qualia** again. Your research projects are stored separately and are kept.
- **Remove:** delete the Qualia folder and the two Qualia shortcuts. Your projects stay in your Qualia home folder (see below) until you delete them yourself.

### For developers: install from source

On any platform with Git, [uv](https://docs.astral.sh/uv/), Python 3.14 and Node 24:

```powershell
git clone https://github.com/WilliamEbong/qualia.git
Set-Location qualia
uv sync
npm --prefix web ci
npm --prefix web run build
uv run python scripts/fetch_demo.py
uv run qualia demo
```

The fetch script verifies a pinned checksum. The demo command is repeatable without duplicating the imported sources, segments or annotations. Its visible research workspace contains 8,017 utterances from 106 transcripts, with seven expert-label codes. A separate protected split stays outside the visible workspace. Dataset provenance and licensing qualifications are in [DATA-LICENSES.md](../DATA-LICENSES.md).

Start Qualia with either command:

```powershell
uv run qualia app
```

opens the app window and stops once it is closed, like the icon. Or:

```powershell
uv run qualia open
```

runs in the terminal with your default browser at `http://127.0.0.1:8765`; stop it with **Ctrl+C**. Refresh old browser tabs after restarting, because each launch has a new access token. If the port is occupied, use `uv run qualia open --port 8766`. A `QUALIA_PORT` setting in your environment or local `.env` overrides the command-line port, and `--no-browser` starts the server without opening a browser.

### Where your work is stored

The application folder contains software. Research workspaces live elsewhere, by default:

```text
%USERPROFILE%\Qualia\
  projects\your-study\    database, configuration, benchmarks and project Git history
  vault\your-study\       protected benchmark material and its integrity manifest
  recovery\your-study\    recovery evidence when an experiment is interrupted
```

`QUALIA_HOME` can select another location outside the application checkout. Set it before creating projects. Changing it later selects a different storage root; it does not move existing projects. Keep the same setting across CLI commands and server launches.

For a persistent custom location, open the application's ignored `.env` in a text editor, preserve its other lines, and add or update the setting once. For example:

```dotenv
QUALIA_HOME=C:\Research\QualiaData
```

Save as `.env`, not `.env.txt`, then restart Qualia. An already-set environment variable takes precedence over this file. Keep credentials in their existing local entries; do not copy their values into a guide, command or screenshot.

The vault is an application access boundary, not encrypted storage. Your operating-system access controls and backup arrangements still matter. The local application is not a hosted collaboration service.

## 3. Try a small practice study

This synthetic exercise produces easy-to-check results without using private research data or AI.

1. In **New project**, enter `practice-study` as the **Project identifier**, then select **Create local project**. Identifiers use lowercase letters, digits and hyphens.
2. Open Notepad, paste the CSV below, and save it as `practice.csv` using **All Files** and UTF-8 encoding. Keep it outside the application folder, for example in your Documents folder.
3. In **Workspace**, choose **Import source**. Select the file and choose **CSV with column mapping** as **File format**.
4. Keep the default text/case/speaker column names. Enter `group,age,wellbeing` under **Attribute columns**. Select **Import into project**.

```csv
text,case,speaker,group,age,wellbeing
"My sister gives me support when work feels stressful.",p01,Participant,north,24,4
"I feel pressure at work and take a short walk afterward.",p02,Participant,south,36,6
"Support from friends helps me manage pressure.",p03,Participant,north,48,8
```

**Expected result:** three sources, three segments and three linked cases. The CSV row names become source names. Each participant has the mapped case attributes.

5. In **Codebook**, create `Support`, defined as “Practical or emotional help from other people.” Select **Save draft code**.
6. Create `Pressure`, defined as “Experienced demands or stress.” Save it, then select **Freeze codebook**.
7. In **Workspace**, select the first source and assign **Support** to its whole segment. Assign **Pressure** to the second source. Assign both codes to the third source.
8. Open **Analysis**. With no filters, each code should appear on two of three segments and two of three cases: approximately 66.667%.
9. Under **Analysis criteria**, set **Group by case attribute** to `group`, select `age` and `wellbeing` under **Explicit numeric case attributes**, and select **Apply analysis criteria**.

**Expected result:** north contains two cases and south one. Age has mean 36, median 36 and sample SD 12. Wellbeing has mean 6 and sample SD 2. Pearson r is 1 for these three deliberately constructed pairs. This is a software exercise, not a research finding.

Use this project to practice removal, memos, filters and exports. Keep actual research in a separate project.

## 4. Import your material

### Text or Markdown

1. Select the correct **Local project**.
2. In **Workspace**, choose **Import source** or **Import transcript**.
3. Choose a `.txt` or `.md` file, or paste text into **Or paste source text**. Use UTF-8 files.
4. Set **File format** explicitly and optionally provide a **Source name**.
5. Leave **Source version** as **New source** for a new document.
6. Select **Import into project**, then inspect the segments before coding.

Blank-line paragraphs are the default segments. For intentional advanced changes, `config/segmentation.yaml` supports `paragraph`, `utterance` and `sentence`. Configuration files use JSON syntax despite their `.yaml` extension. Utterance mode splits lines and can recognize `Speaker: text`; sentence mode splits at whitespace after `.`, `!` or `?` and does not infer abbreviations. There is no segmentation settings screen. Existing imported sources are not resegmented by changing a configuration file.

### CSV mapping

Use one text record per row and a header row. In **CSV column mapping**, match the exact case-sensitive column names:

- **Text column:** required text content.
- **Case column:** optional case name; repeated names link records to the same case.
- **Speaker column:** optional speaker label.
- **Attribute columns:** comma-separated column names you explicitly want to import.

If a row has a case, its mapped attributes belong to that case. Without a case, they belong to the source and are not available for case-group or numeric analysis. A speaker label alone does not create a case. Repeated rows for one case update its named attributes; import case measurements consistently rather than treating each row as another numeric observation.

The full file validates before database insertion. A malformed row, missing mapped attribute column or invalid text rejects the import with a filename/row message.

### Reimporting and revisions

Identical source content is imported once, even if you select it again. A repeat can report **0 new sources**; it may still attach explicitly supplied case metadata. To import changed text as a revision, choose the existing source under **Source version**. Old source text and coding remain available; coding is not automatically transferred to a new text version.

CLI equivalent:

```powershell
uv run qualia import "C:\Research\interviews.csv" --project my-study --text-column response --case-column participant --speaker-column speaker --attribute-columns "region,age"
```

Use `--version-of SOURCE_ID` for an explicit revision. Replace example paths, project names and IDs with your own.

## 5. Organize cases and attributes

A source can link to more than one case. Each linked case receives that source's selected segments in case-based analyses. This is useful for some designs, but it does not separate participants inside a multi-speaker transcript automatically.

1. In **Workspace**, select **Create case**, or **Edit** beside an existing case.
2. Enter **Case name**.
3. Under **Add linked sources**, select the sources belonging to that case. Existing links are checked and disabled because they cannot be removed in this form.
4. Enter **Attributes, one name=value per line**, for example:

```text
region=north
age=36
wellbeing=6
```

5. Select **Save case**. Use **Filter by case** to inspect its linked sources.

**Editing is additive:** existing links remain attached; link removal is not currently supported. Submitted attribute values update their named attributes. Omitted attributes remain. To mark a value missing, submit an empty value such as `age=`. This does not delete the attribute key.

Choose units deliberately. Numeric analysis uses one observation per eligible case, not per segment or source. A source shared by several cases can contribute to several groups, so group totals and percentages are not necessarily additive or independent.

## 6. Create and freeze a codebook

1. Open **Codebook**.
2. Under **Create code**, enter a **Name** and **Definition**.
3. Optionally choose a **Parent code**, write **Include** and **Exclude** guidance, and add positive/negative examples, one per line.
4. Leave **Status** as **Active** and select **Save draft code**.
5. Repeat for the rest of your codebook.
6. Select **Freeze codebook** when the definitions are ready for use.

**Expected result:** an immutable version appears in the codebook history and in the **Frozen codebook** selector in Workspace. You need an active code and a frozen version before coding.

Later edits change the draft. Select **Edit [code name]**, save your changes, then freeze a new version. Existing decisions retain their original version and historical code name. The Analysis frequency table uses current display names and identifies the frozen versions contributing to its counts.

Archiving a draft code preserves historical references. Freeze a new version to exclude an archived code from that version's active coding choices. Selecting an older frozen version still exposes its historical active codes.

Your codebook belongs to you. AI classification and improvement experiments do not edit code definitions or frozen methodology.

### Draft and refine codes with proposals

Proposals help you write or sharpen the codebook. Each one is a suggested new code or a suggested revision, shown with its reasons, its evidence and where it came from. A proposal changes nothing on its own: you accept it into the draft codebook, usually after editing it, or reject it with a note. Freezing stays a separate decision.

There are three ways to ask, under **Codebook → Proposals → Ask for proposals**:

| Type | What it sends | What you get |
|---|---|---|
| **Find evidence in my reviews** | Nothing: it runs offline, with no AI and no network. | Revisions from your own decisions: rejected AI suggestions become candidate negative examples (with your review notes), a code with no current coding after 20 coded segments is flagged for archiving, and two codes that appear together on at least 80% of their segments (and at least 5) get a draft boundary line in **Exclude**. |
| **Draft new codes from passages** (inductive) | Up to 20 passages from one source, your current code names and an optional focus such as “experiences of waiting”. | New codes, each with a definition, include/exclude guidance and examples quoted from the passages. |
| **Refine codes from review evidence** | One or two codes, each with up to four coded and four rejected passages and your review notes. | A revised definition, guidance and examples for each code. |

Drafting and refining use Claude or Codex with your own subscription (or the offline `fake` backend for practice), under the same privacy and budget settings as classification ([section 12](#12-generate-and-review-ai-suggestions)). The project must allow external AI before anything is sent.

1. Enter your **Reviewer** name. Optionally write a **Decision note**.
2. Read a proposal: changed fields show **Current** and **Proposed** values, then the reason. Open **Supporting passages** to read the evidence in context, and **Proposal provenance** for the backend, model, CLI version, prompt hash and the frozen version it was based on.
3. Choose **Review and accept**. The code editor opens with the proposed values; edit anything, then choose **Accept into draft codebook**. Or choose **Reject**.
4. Freeze the codebook when the draft is ready. Accepted codes show where they came from, for example *created from model-proposed (claude) proposal #4 · accepted by ana*.

![A proposal to add rejected passages as negative examples, with its reason and review notes](../design-review/final/features/codebook-proposals.png)

Safeguards and limits:

- Every example in an AI proposal is checked against the passages that were sent. Qualia matches it ignoring spacing, punctuation and capitalization, then stores the passage's own wording, so examples are always verbatim. An example that matches no passage is removed, and the proposal says how many were removed. Malformed responses, unknown passages or codes, and duplicate names reject the whole response, which stores nothing.
- New names cannot repeat an existing code. Revisions can only target the codes you sent.
- Published studies find that AI-drafted codes can split ideas too finely, miss implicit (latent) meaning and blur boundaries between codes, so read each proposal against the data. Proposals are codebook assistance, not themes or findings. Many qualitative researchers consider generative AI incompatible with reflexive thematic analysis; choose a method that fits your study.
- Proposals and your decisions are kept permanently and included in exports, so you can disclose AI-assisted codebook development in your methods section.

The research behind this design is summarized in `specs/014-codebook-proposals/research.md`.

![A code card with its definition and, after tuning, the AI suggestion threshold](../design-review/final/features/codebook-threshold.png)

Use this view to inspect definitions before choosing a frozen version for coding.

## 7. Code passages manually

### Whole segments and selected spans

1. Open **Workspace** and select a source.
2. Under **Code this passage**, enter your **Human actor** name or research identifier.
3. Choose the intended **Frozen codebook** version.
4. Click a segment. With no selected text, the panel says **Whole segment selected**.
5. Click a code button. Wait until saving finishes before the next action.
6. To code only part of a passage, select its text, confirm the displayed **Selected span**, then click a code.

**Expected result:** a current code mark appears with its span. **Current assignments** shows the coded excerpt. **Provenance** records actor, action, time, frozen version and pipeline identity. Multiple codes can apply to the same passage.

Use **Use whole segment** or Escape to clear a text selection. Arrow keys move through the current source; keys 1–9 apply the corresponding displayed code, not a database code ID. Shortcuts do not operate while you are typing into a form.

![Workspace with sources, transcript segments, coded spans and numbered code shortcuts](../design-review/final/features/workspace-coding.png)

Work from left to right: choose the source, read/select the passage, then inspect its coding and provenance. Wait until code buttons are enabled after saving before pressing the next coding shortcut.

### Create a code while reading

When a new idea emerges from the data, you can name it without leaving the transcript:

1. Select the passage, or the exact words, that prompted the idea.
2. Open **New code from this passage** in the coding panel.
3. Type a **Code name**, perhaps in the participant's own words, and optionally a definition. Leave **Keep the selected text as a positive example** checked to store the words as an example.
4. Choose **Create, freeze and assign**.

**Expected result:** the code is created, a new frozen codebook version is made and selected, and the passage is coded with it. Freezing captures the whole draft codebook, so any other draft edits are included in that version; use the separate **Freeze codebook** button when you want deliberate versions.

### Correcting a decision

Select the segment, find the assignment under **Current assignments**, and choose **Remove assignment**. The current assignment disappears, but its original event and the removal remain in **Provenance**. You can then assign the appropriate code/span. This is an audit trail, not a destructive undo.

### Understanding span numbers

Offsets are relative to the segment and count Unicode code points. `0:5` includes positions 0 through 4, excluding position 5. The UI handles the conversion from browser selection offsets. For CLI work with emoji or combining characters, do not assume the displayed glyph count equals the required offset; UI selection is usually easier.

## 8. Write memos and retrieve evidence

### Memos

1. Open **Memos** and choose **New memo**.
2. Enter **Title**, choose a **Kind** and write the **Memo** text.
3. Optionally link it to a **segment**, **code**, **case** and **source**.
4. Select **Save memo**.

| Kind | Use it for |
|---|---|
| Analytic | Interpretations, questions and exceptions. |
| Reflexive | How your background, position and assumptions affect what you notice and how you interpret it. |
| Theme | A pattern you are building across codes (see below). |
| Method | Decisions about sampling, units, coding and analysis. |

Use **Show** to list one kind. **Edit memo** keeps the previous version: each card shows **Earlier versions** with the time each was replaced, and exports include them. Saving without changes adds no version.

![A reflexive memo linked to its source, with its earlier version kept](../design-review/final/features/memo-history.png)

### Build themes

A theme is an interpreted pattern relevant to your research question, not a topic label or the most frequent word. Qualia supports themes as a documented pattern rather than a separate object:

1. Create a parent code for the theme in **Codebook** and place the supporting codes under it.
2. Write a **Theme** memo linked to that parent code: what the pattern is, why it matters for the question, and where it does not hold.
3. Use **Retrieval** (by each supporting code), **Analysis → Co-occurrence** and the **Matrix** to check the evidence across cases.

Code hierarchy organizes definitions; counts are not rolled up from child codes to the parent.

### Keep a reflexive record

Write **Reflexive** memos as you go, link them to the source or case they concern, and revise them as your understanding changes; the history shows how your position shaped the analysis. Record study-level decisions (research question, sampling, unit of analysis) in the project's protected `METHODOLOGY.md` and in **Method** memos. If you used codebook proposals or AI suggestions, say so in your methods: the export lists every proposal, suggestion and your decision.

### Retrieval

1. Open **Retrieval**.
2. Select a **Code**, a **Case**, or both. Leave them at **All codes**/**All cases** for a broader view.
3. Read the matching coded excerpts and their frozen codebook versions.
4. Choose **Open in transcript** to inspect context.

Retrieval lists current coded spans. Several spans in one segment can produce several excerpt cards. Segment-frequency analyses and the matrix deduplicate those spans when counting presence.

## 9. Compare codes in the matrix

1. Ensure you have cases linked to sources and current coding assignments.
2. Open **Matrix**.
3. Read each code-by-case cell as the number of distinct currently coded segments carrying that code and linked to that case.
4. Select a cell to open the corresponding retrieval view.

Repeated spans of the same code on one segment count once in a cell. Multi-case source links contribute to each applicable case. An empty matrix can mean no case links, not necessarily no coding.

![Code-by-case matrix](../design-review/final/features/matrix.png)

Use a cell as a route back to the supporting coded excerpts, not as a standalone explanation of the pattern.

## 10. Use the Analysis workbench

Analysis reads visible workspace data. It does not write coding, call AI or read the protected benchmark vault. It describes the data and decisions selected by your criteria; it does not establish statistical significance or causation.

![Code frequency chart with its denominator](../design-review/final/features/analysis-frequencies.png)

Set the criteria first, read the denominators and methods, then use the evidence links or exports to inspect the result.

### Select and apply criteria

1. Open **Analysis**. The first report uses all visible segments.
2. Expand **Analysis criteria** if needed.
3. Choose **Analysis source** and/or **Analysis case** to narrow the scope.
4. Enter a **Literal text query** if useful. It is a case-insensitive substring search, not a regular expression; `.*` searches for those literal characters.
5. Expand **Code filter**, select codes, then choose **Any selected code** or **All selected codes** under **Match selected codes**. No code selection imposes no code filter.
6. Choose any grouping, numeric or word options described below.
7. Select **Apply analysis criteria**.

All filter types intersect. Selecting a code filters which segments enter the report; the frequency table still describes all current codes on those segments. **Applied criteria** records the effective choices. Entering Analysis, selecting **Refresh analysis**, or selecting **Apply analysis criteria** first reloads the workspace, then calculates the report using that fresh evidence snapshot. Entry and Refresh preserve the last applied criteria for that project; Apply uses your current form choices. Switching projects resets criteria to the defaults. Refresh does not apply unsaved form changes.

Wait for the fresh report after changing coding or attributes. If you made changes through a CLI command or another browser tab, select **Refresh analysis** to reload both the workspace evidence and the report while preserving your applied criteria. A full browser reload is not required for this update. Qualia does not continuously synchronize edits from other processes, so refresh before interpreting externally changed data.

Browser report downloads send the displayed report's input hash along with its applied criteria. The server recomputes the report and rejects the download if the underlying data/configuration has changed, with **Research data changed. Refresh analysis before downloading this report.** Refresh, inspect the new report, and download the related files again as a set. Previously downloaded files are not updated automatically.

### Code frequencies and group comparisons

Read **Code frequencies** as presence: each segment and linked case counts at most once per code. The displayed denominators are the selected segments and eligible linked cases, including those without the code. Uncoded selected segments remain in the segment denominator. Percentages with an empty denominator are displayed as zero.

Select a bar or count to open its **Source evidence**. Under **Coding evidence**, inspect event IDs, historical names, actors, spans and frozen versions. **Open transcript** returns to the source. Evidence pages show up to 25 segments; pagination and complete selected IDs remain available even though the API's embedded excerpt list is capped.

To compare groups, choose **Group by case attribute**, apply the criteria, then expand a group under **Case-group comparisons**. Missing values and conflicting values appear separately. Equal nonblank values collapse, surrounding whitespace is trimmed, and differing nonblank values conflict. Only case attributes are used. Group percentages use that group's own segment/case denominators.

### Co-occurrence

Choose one **Co-occurrence unit**:

- **Present in the same segment:** count a segment once if it carries both codes anywhere.
- **Positive-length span overlap:** count it once only if their coded spans actually overlap. Touching end/start boundaries do not overlap.

The heat table shows mode counts; selecting a cell opens contributing evidence. **Exact pair counts and segment-presence Jaccard** provides exact values. Jaccard is always the number of segments carrying both codes divided by the number carrying either code, regardless of overlap mode. Consequently, an overlap count can be zero while segment-presence Jaccard is positive. These are different quantities.

### Word frequency

Under **Word-frequency options**, set **Minimum word length**, **Top words** and **Explicit stopwords**, separated by spaces or commas. Apply the criteria.

**Words in selected text** distinguishes occurrences from distinct segments. For example, a word repeated five times in one segment has five occurrences and segment frequency one. Tokenization uses Unicode casefolded letters and internal straight/curly apostrophes. Digits and other punctuation delimit tokens. There are no hidden stopwords, stemming or automatic synonym groups. The word list is descriptive and is not a substitute for reading context.

### Numeric summaries and scatter plots

1. Under **Explicit numeric case attributes**, choose up to eight fields that you intend to treat as measurements.
2. Apply the criteria.
3. Inspect **Valid**, **Missing**, and **Invalid / conflicting** before interpreting mean, median, sample SD, minimum or maximum.
4. With two or more selected fields, choose a pair under **Scatter fields**.
5. Inspect **Paired cases**, **Pearson r**, **Exact paired case values**, and **All pairwise correlations**. Select a point or case row to inspect its selected source evidence.

Numeric parsing accepts finite decimal/scientific strings such as `24`, `-2.5` and `1.2e3`, with absolute magnitude at most `1e150`. Blank values are missing. `NaN`, `Infinity`, `1,000`, nonnumeric text and conflicting values are invalid. Categorical numbers and participant IDs are not automatically treated as continuous measurements; make that decision explicitly.

Sample SD uses the sample denominator, n−1, and requires at least two valid values. Pearson uses only cases valid on both fields. It requires at least three pairs and two nonconstant fields; otherwise it is **n/a**. A missing observation is not silently turned into zero. Shared sources and linked cases may violate assumptions needed for later inferential analyses; Qualia reports descriptive relationships, not p-values or causal conclusions.

### Save charts and provenance

The following illustration uses six invented cases, including one invalid age value, to show the numeric relationship workflow. It is separate from the AnnoMI demo and the small practice study above.

![Synthetic numeric relationship with paired-case count and Pearson correlation](../design-review/final/scatter-1280.png)

Use **Download frequency SVG** or **Download scatter SVG** for standalone charts with labels and criteria. Exact values remain in adjacent tables. Chart labels and SVGs can contain research metadata, so review them before sharing.

**Analysis methods and provenance** records the input hash, pipeline, contributing event IDs and frozen codebooks. Default analysis JSON omits words and source excerpts, but retains the report criteria and research metadata.

### Analysis limits

The engine accepts at most 20,000 input segments, 5,000 cases, 200 codes, 100,000 current coding rows, 50,000 attributes and 100,000 source-case links. Source/case filtering can reduce computation and result sizes, but does not bypass these whole-project input caps.

Additional limits bound text processing, case/attribute expansion, word/pair memberships, frequency outputs and span comparisons. If a limit is reached, the report fails explicitly rather than silently dropping contributions. Use a smaller source/case scope for a computation limit, or a smaller separately imported project for a whole-project limit. The precise limits are included in report methods.

## 11. Continue in Python or R

Use this workflow for deeper analysis outside Qualia. It does not install or execute an unrestricted code runner in the application.

1. Set the intended Analysis criteria, including numeric fields, and select **Apply analysis criteria**.
2. Select **Download case CSV**.
3. Select **Download analysis JSON** to retain criteria, input identity and the column dictionary.
4. Select **Download Python starter** and/or **Download R starter** from the same report. If a download reports changed research data, refresh the analysis, review it, and download all related files again so the set uses one input identity.
5. Keep those files together in a research output folder. Review them before running.

Downloads use these names:

```text
qualia-analysis.csv
qualia-analysis.json
qualia-analysis.py
qualia-analysis.R
```

CSV has one row per eligible case. `code_ID` columns count distinct selected segments for that case. Attribute columns use stable IDs rather than embedding arbitrary field names. The JSON dictionary and starter metadata explain them. Status columns distinguish present, missing and conflicting values. Spreadsheet formula-leading strings are escaped; explicit flags let the starter recover exactly the added escape character.

From the output folder, run a starter deliberately:

```powershell
python qualia-analysis.py qualia-analysis.csv
Rscript qualia-analysis.R qualia-analysis.csv
```

The Python starter requires Python 3.10+ and only its standard library. The R starter uses base R; R must be installed separately. The Python workflow has executable regression coverage. R source has been reviewed, but R was not installed in the verified environment, so its execution is not claimed here.

The starters reproduce selected numeric summaries, pairwise correlations and case-level code prevalence. They do not reconstruct source excerpts or every segment-level chart from a case table. Mismatched CSV columns cause a clear failure: re-download the CSV and script together instead of editing away the check.

**Privacy:** Analysis exports omit source text, but retain case names, attributes and query criteria. This is not anonymization. The workspace Export workflow has a different default, explained below.

## 12. Generate and review AI suggestions

### Know which backend you are using

| Backend | Current behavior |
|---|---|
| `rules` | Offline keyword baseline. Matches comma/newline-separated inclusion terms, or the code name when inclusion text is empty, as case-insensitive substrings. It does not interpret your full methodology. |
| `fake` | Offline deterministic demonstration. Proposes configured first/all/no codes with a synthetic rationale. It is not a trained model or a research-quality recommendation system. |
| `claude`, `codex` | Native classification with your own eligible subscription sign-in and a current CLI (Claude Code 2.1.284 or newer, Codex 0.160.0 or newer). External processing must be allowed for the project. Claude improvement uses restricted file tools; Codex improvement uses no-tools proposals and trusted application. |
| `jev` | Optional external classifier, installed but off by default. Requires a locally configured key, project opt-in and a deliberate backend choice. |

**What has actually been tested:** the [synthetic CLI preflight](research/preflight-ai.md), [adapter evidence](research/cli-classification.md) and [current build state](BUILD-STATE.md) distinguish standalone CLI calls, offline transport tests and actual normal-router smoke tests. The practical native limits are recorded in the [native usage decision](answers/01-native-usage.md). The [subscription documentation review](research/subscription-policy.md) explains native-login use without claiming provider approval of every integration.

### Set up your own device and subscription

1. Install Qualia on your own computer. Install the official [Codex CLI](https://github.com/openai/codex) or [Claude Code](https://code.claude.com/docs/en/setup) separately. Qualia works with current versions of both and requires at least Codex **0.160.0** and Claude Code **2.1.284**; newer versions, including automatic updates, are used as installed. Every suggestion and usage record keeps the CLI version that produced it, so a run can be reproduced from its logged version. Whatever the version, Qualia launches the CLI with no action tools in an empty temporary folder, validates the output and keeps the batch, size, time and output limits.
2. Run `codex` and choose **Sign in with ChatGPT**, or run `claude` and use your eligible Claude subscription account. These are your accounts; no shared developer account is supplied. No API key is required for these subscription paths. Qualia rejects Claude Console/API authentication and forces ChatGPT authentication for Codex.
3. Confirm your subscription permits the selected model. Keep paid extra usage disabled unless you independently choose it; Qualia does not change billing settings. A successful login does not guarantee remaining quota.
4. Start with a small synthetic study. Close or finish any active classification. Open that project's `config/routing.yaml` in your local research folder (default `%USERPROFILE%\Qualia\projects\my-study\config\routing.yaml`) in a text editor. The file uses JSON syntax. Preserve the other fields, change `"allow_external": false` to `true`, and consider `"daily_calls": 10` for your initial trial. Save it. This is your explicit permission to send the selected study text and codebook to the provider. Setting the value back to `false` prevents new external dispatches; it does not recall a request already sent.
5. Reopen or refresh Qualia, choose the project, and inspect **Review → Backend availability and privacy**. “Available” means the executable can be found; the minimum version, sign-in and provider response are checked during dispatch. Choose `claude` or `codex` and **Current source** for a small first request.

Each installation keeps its own projects, CLI login and optional Jev key. No subscription token or API key is shipped with Qualia. If you customize `QUALIA_HOME`, use that directory instead of the default path above.

### Understand the usage limits

Native classification batches contain at most five segments, each at most 4,000 characters. The default process deadline is 90 seconds, input is capped at 1 MiB and captured output at 256 KiB. Claude also uses its supported generation limit and a two-turn control. Codex has no verified provider generation-token cap; its byte/time limits are local controls. The configured output-token threshold is also checked after the response, which can reject an over-limit result but cannot undo provider usage.

For Claude/Codex, each recorded **call** and native egress record means one CLI invocation. The CLI may issue several internal provider requests, including retries or continuation. Qualia does not automatically retry a failed native invocation. Failed attempts still consume the local invocation budget; reported aggregate tokens are retained when available. Missing token telemetry must not be interpreted as proof of zero provider usage. These counters do not show your exact remaining subscription allowance. Jev calls are direct HTTP requests with separate accounting and billing.

### Generate a small batch

1. Freeze your codebook and select a source in **Workspace**.
2. Open **Review**.
3. Choose **Backend**. Use `rules` for a local keyword baseline, `fake` only to practice, or your configured native/Jev classifier after completing its setup.
4. Choose **Current source** under **Scope**. The large AnnoMI demo exceeds the default 2,000-segment run limit when all project segments are selected.
5. Leave **Model override (optional)** empty unless you have a verified reason to set it.
6. Select **Run classification**, then inspect the result and pending suggestions.

Classification uses the project's **latest frozen codebook** and budget/privacy policy; the Workspace selector for manual coding does not select an older classification codebook. An empty result can mean no matching rules, not a failure. Cache reuse may reduce new calls; it does not make a suggestion a human decision. Large or unsupported segments can be rejected explicitly rather than silently shortened.

### Review carefully

![A suggestion card with its model-reported score, review reason, passage and accept/reject actions](../design-review/final/features/review-suggestion.png)

The example comes from the fake backend; use the rationale, excerpt and provenance together before making a decision.

1. Enter your **Reviewer** identity.
2. Select a suggestion, read its excerpt and rationale, and use **Open segment** for context.
3. Inspect **Suggestion provenance** and any calibration caption.
4. Optionally enter a **Review note**.
5. Choose **Accept** or **Reject**, or use `a`/`r` while the suggestion is selected and you are not typing in a field.

Each suggestion's caption says why it is waiting. For example, *Below review threshold (current threshold 0.70) · segment 12* means the model-reported score was under your project's review threshold when the suggestion was made. The value shown is today's setting. Within each reason group, the least certain suggestions (lowest model-reported score) come first, so your attention goes where the AI is least sure.

Acceptance creates a current coding decision with the original model identity and human reviewer. Rejection does not create a current assignment. Both decisions append review evidence; the original suggestion remains in history. A suggestion can appear under several review reasons, but reviewing it resolves that suggestion once.

Numbers labeled **model-reported** are not measured accuracy. Rules and fake scores are deterministic fixture values. A validation ECE caption appears only when backend, model, frozen codebook, pipeline and prompt identities match a scored validation run. An unavailable ECE is not evidence of perfect calibration.

To inspect availability without starting classification:

```powershell
uv run qualia availability --project my-study
```

## 13. Set up optional Jev processing

Jev is TypeSafe AI's "System One" decision model. Instead of writing text, it answers one yes/no question per code for each passage with a probability. That makes it fast and inexpensive, and its probabilities suit Qualia's [threshold tuning](#tune-per-code-suggestion-thresholds-without-ai). Jev is optional, off by default, and billed by TypeSafe separately from any Claude or ChatGPT subscription.

### Step 1 · Create an account and check spending

1. Sign in to the [TypeSafe console](https://console.typesafe.ai/) in your own browser.
2. Check your available credits and the purchase amount before paying. An account alone does not prove you have usable credit.
3. Leave automatic credit refills off unless you deliberately want recurring charges.

The published rate for Jev 1.13 is $0.042 per million input tokens, with free output tokens. As a guide, one full evaluation of the demo's 1,258 validation segments used about 2.5 million input tokens (roughly $0.10), and the complete threshold-tuning experiment cost about $0.35. Check TypeSafe's current terms before paying.

### Step 2 · Create a key

In the console's **API Keys** area, create a key named something like `Qualia local`, so you can recognise and revoke it later. Copy it into your password manager straight away; consoles often show a key only once. Never paste the key into chat, screenshots, issues, frontend settings or a shell command.

### Step 3 · Save the key in Qualia's local `.env`

From the Qualia application folder:

```powershell
notepad .env
```

Allow Notepad to create the file if asked, and keep any existing lines. Add or replace one line:

```dotenv
TYPESAFE_API_KEY=PASTE_YOUR_ACTUAL_KEY_HERE
```

Replace the placeholder with your key and save. If you use **Save As**, choose **All Files** and the name `.env`, not `.env.txt`. Confirm Git will never commit it:

```powershell
git check-ignore .env
```

The expected output is `.env`. Never put the real key in `.env.example`.

### Step 4 · Check readiness (no network request)

```powershell
uv run qualia jev check --project my-study
```

`key_configured: true` means a key is present. It does not prove the key works or that you have credit. `allow_external` and `jev_enabled` stay `false` until you opt a project in.

### Step 5 · Run a tiny synthetic first test

Use a throwaway project with invented text before sending any research material:

```powershell
uv run qualia init jev-check
uv run qualia codebook add Possibility --definition "Language describing a possible positive change." --project jev-check
uv run qualia codebook freeze --project jev-check
$samplePath = Join-Path $env:TEMP 'qualia-jev-smoke.txt'
Set-Content -LiteralPath $samplePath -Value 'I could try a different approach tomorrow.' -Encoding utf8
uv run qualia import $samplePath --project jev-check
uv run qualia jev enable --project jev-check
uv run qualia classify --project jev-check --backend jev --model jev-1.13.0
uv run qualia jev disable --project jev-check
```

Success means a validated answer with the returned model ID and token usage recorded, and the key never printed. If it fails, Qualia reports a sanitized reason:

| Status | Meaning |
|---|---|
| `authentication` (401/403) | Missing, mistyped or revoked key |
| `invalid_input` (422) | The request was rejected as invalid |
| `rate_limit` (429) / `transient` (529) | Try again later |
| Billing errors | Check your credit balance in the console |

### Step 6 · Use Jev in your project

1. Opt the project in: `uv run qualia jev enable --project my-study`. This allows external processing for that project only and keeps its budgets, including the default $1.00 per day Jev spending cap and 300 calls per day. `jev disable` turns it off again.
2. Choose `jev` as the backend in **Review** (classification), **Evaluation** or **Experiments → Tune thresholds**.
3. Qualia sends each segment with your frozen code definitions and asks one question per code. Large batches split automatically to fit Jev's request limit. A code becomes a suggestion when its probability reaches 0.5, or the code's tuned threshold.
4. Run **Tune thresholds** once you have dev and validation benchmarks. On the demo, this raised validation macro F1 from 0.523 to 0.567 (0.572 on confirmation).

A full tuning experiment on a large benchmark can exceed the default 300 daily calls. The demo needed about 420. If so, raise `daily_calls` in that project's `config/routing.yaml` deliberately for the run, then set it back.

### Privacy and data

Sending text to Jev is a research-data disclosure decision. Review participant consent, your data-handling rules and TypeSafe's terms. TypeSafe hosts in the US. Its customer agreement says customer data is not used to change model weights without consent, but ordinary accounts do not get zero data retention; TypeSafe offers that to enterprise customers through sales ([legal](https://docs.typesafe.ai/legal), [privacy policy](https://typesafe.ai/legal/privacy-policy)). Prefer synthetic or de-identified material unless your approvals cover it. Every request appears in the project's egress log and usage ledger. Local budgets limit requests but do not change billing settings with TypeSafe.

Jev can also take load off Claude or Codex: set it as the cheap tier and escalate only uncertain segments to a stronger model. Savings depend on your escalation rate, so measure them with **Evaluation**. Technical background and the wire contract are in [Jev setup notes](JEV-SETUP.md) and [Jev research](research/jev.md).

## 14. Evaluate a classifier against reference labels

**Analysis** describes your current research coding and attributes. **Evaluation** measures classifier predictions against separately supplied reference labels. Evaluation never turns its predictions into research coding assignments.

### Use the demo validation benchmark

1. Select the locally installed `demo` project.
2. Open **Evaluation**.
3. Under **Evaluate validation split**, select an available **Evaluation backend**.
4. Select **Run validation evaluation**.
5. Inspect the **Recorded validation run**, aggregate metrics, **Per-code performance**, and **Evaluation provenance and metric definitions**.

The demo validation split contains 1,258 utterances. Privacy and call budgets still apply. Successful evaluation requires complete coverage; the UI does not invent partial metrics when a run fails.

Read macro/micro F1, exact code-set match, partial match and per-code support together. They answer different questions. The displayed alpha basis distinguishes human-coder agreement from reference-versus-prediction agreement; the latter is not human intercoder reliability. **n/a** means undefined or unavailable.

### Read the results in plain language

Each metric in the table has a one-line explanation under its name. The most useful ones:

| Term | What it tells you |
|---|---|
| Precision | Of the codes the AI suggested, how many matched the reference. |
| Recall | Of the reference codes, how many the AI found. |
| F1 | One number balancing precision and recall. Macro F1 averages it over every code, so rare codes count equally. |
| Range in brackets | `0.82 (0.61–0.94)` is a 95% Wilson interval. A wide range means the code had few examples, so treat its number with caution. |
| Cohen kappa / Nominal alpha | Agreement beyond chance. Qualia adds a word: kappa uses Landis & Koch (slight, fair, moderate, substantial, almost perfect); alpha uses Krippendorff (reliable at 0.800 or more, tentative at 0.667 or more, otherwise insufficient). |
| Validation ECE | How far model-reported scores are from how often those suggestions were actually right. 0 means they match. |

Below the metrics, a sentence turns the scores into a workload: for example, *reviewing suggestions with a model-reported score below 0.64 (35% of them) leaves the rest at 90% precision or better on this validation set*, followed by your current review threshold. If no score cutoff reaches 90%, Qualia says every suggestion needs review. These figures describe this validation set, not guaranteed future accuracy.

![Validation metrics with plain-language explanations and the review-workload sentence](../design-review/final/features/evaluation-metrics.png)

![Per-code precision and recall with 95% ranges](../design-review/final/features/evaluation-per-code.png)

Open **Evaluation provenance and metric definitions** for the exact definitions and a **Calibration by score band** table showing, for each model-reported score band, how many suggestions fell there and how often they were correct.

![Calibration by score band](../design-review/final/features/evaluation-calibration.png)

### Import your own benchmark

This is an advanced workflow. Prepare UTF-8 JSONL, one record per line, bound to a frozen codebook. For example:

```json
{"segment_id":"validation-001","text":"A synthetic example passage.","codes":[1],"transcript_id":"interview-001"}
```

Code IDs must exist in the selected frozen codebook. Segment IDs must be unique; transcripts cannot overlap splits. Optional `coders` arrays can contain coder code-ID lists or missing ratings. Choose gold labels through your research process rather than generating them from the classifier you are evaluating.

```powershell
uv run qualia benchmark import "C:\Research\validation.jsonl" --project my-study --split validation --version 1
uv run qualia evaluate --project my-study --backend rules --output "C:\Research\evaluation-reports"
```

Replace the example version with your actual frozen version. Reimporting identical bytes is a no-op; replacing an existing split with changed content is rejected. CLI evaluation writes JSON and Markdown reports to the output directory. Without `--output`, they go in the workspace's `reports` folder.

### Protected evaluation

Protected examples are held separately so normal analysis and improvement do not inspect them. Only deliberate advanced CLI evaluation uses them:

```powershell
uv run qualia evaluate --project my-study --protected --backend rules --output "C:\Research\protected-evaluation-reports"
```

Use `--protected` without `--split protected`. A protected benchmark must already exist with a valid manifest. Normal UI views do not expose its records. Protected predictions stay in the vault; ordinary storage retains aggregate evaluation evidence. Keep output reports under your research-data controls as well.

## 15. Understand improvement experiments

An experiment proposes a change to implementation configuration/prompts, measures it on validation data, and records **KEEP** or **REVERT**. It does not authorize changing research code definitions, benchmark labels, methodology or protected test data.

Use `fake` to practice offline. Claude and Codex improvement are available with a current CLI (at or above the minimum versions in [section 12](#12-generate-and-review-ai-suggestions)) and your own subscription. These experiments improve project prompts/configuration; they do not retrain the underlying model. Specify fake explicitly for this demonstration:

```powershell
uv run qualia improve --project demo --agent fake --budget 1
uv run qualia history --project demo
```

**Prerequisites:** a prepared validation benchmark, sufficient remaining call budget, and a clean project Git baseline. Check that you have not left uncommitted configuration or report files in the research workspace. Do not delete research files or use destructive Git commands to make an error disappear; save and review the intended changes first. Writing evaluation exports outside the workspace helps keep its experiment baseline clean.

For a prepared study with external processing enabled, choose one operator from PowerShell:

```powershell
uv run qualia improve --project my-study --agent claude --budget 1
```

Or use Codex:

```powershell
uv run qualia improve --project my-study --agent codex --budget 1
uv run qualia history --project my-study
```

1. Prepare and import the validation benchmark described in section 14, then save the intended configuration as a clean project Git baseline.
2. Confirm the project's external-processing permission and remaining local invocation budget. Claude's operator uses Opus; Codex's uses `gpt-6-astra`. Evaluation uses the project's configured classifier, or your explicit `--backend` and `--model` choices. For example, append `--backend codex --model gpt-6-luna` to evaluate using Luna while Astra proposes changes.
3. Run one experiment. Claude has restricted access to permitted implementation files. Codex receives a bounded copy of allowed implementation text and has no file, shell, browser or other action tools. Qualia records the complete supplied input hash, invocation and reported usage, applies validated proposals and runs trusted tests and validation. You do not approve every proposed edit; Qualia's measured policy decides automatically.
4. Open **Experiments** to inspect the hypothesis, changed files, metrics and KEEP/REVERT reason. REVERT is a valid outcome, not an instruction to bypass the policy.

Each native classification batch contains at most five segments. A 1,258-segment validation split needs 252 invocations per pass; baseline plus candidate already exceeds the default 300 daily limit. Use an appropriately small validation workflow or deliberately configure a suitable budget; Qualia does not raise limits automatically. The live smoke test used one invented sentence and a four-invocation cap. Opus completed its allowed prompt edit, but Haiku macro-F1 remained 1.0→1.0, so the policy correctly reverted it. This is integration evidence, not improved research accuracy.

The Codex live experiment also completed with the normal pipeline: Astra proposed a replacement for `config/prompts/classify.txt`, Luna evaluated it, and macro-F1 stayed 1.0→1.0. Qualia recorded REVERT, restored the original prompt and retained all three invocations. Both experiments preserved methodology, frozen codebooks and coding events.

### How the Codex proposal workflow works

1. Qualia checks the clean baseline, locks the project, evaluates the current classifier, and captures permitted files. Only existing `.txt`/`.md` files under `config/prompts/` and the two mutable configuration files are supplied. Hidden files, protected methodology/codebook names, database/credential/recovery files and links are excluded or rejected. Do not place sensitive material in implementation prompts; their permitted contents are sent to your provider.
2. Qualia checks that the installed official CLI meets the minimum version and is signed in with ChatGPT, and records the version. Astra receives the task and bounded file snapshot in an empty temporary directory with no action tools. It returns a hypothesis and replacement text with original-content hashes.
3. Qualia validates every replacement before writing: exact permitted path, unchanged original identity/hash, valid configuration, unchanged privacy/budget bounds and size limits. A malformed, stale or forbidden proposal is rejected. Codex cannot create/delete/rename files or execute commands through this workflow.
4. Qualia applies valid changes, runs trusted tests, evaluates the candidate and requires a fresh confirming evaluation for a qualifying gain. It commits/tags KEEP or restores REVERT, then records the report and provenance. Reported usage is retained on rejected and failed attempts.

The supplied context is limited to 64 files, 64 KiB per file and 128 KiB for the complete dispatch. A proposal permits at most 16 replacements, 64 KiB each and 128 KiB combined. Execution retains the 90-second deadline and 256 KiB captured-output ceiling; the configured output-token threshold is checked afterward. These are local limits, not a provider generation-token guarantee or an exact subscription quota display. Oversized context fails explicitly; shorten or reorganize the intended prompt files before retrying.

If Codex reports `subscription_auth_required`, run `codex login` and choose ChatGPT, then check `codex login status`. If it reports `unsupported_version`, the installed CLI is older than the minimum (Codex 0.160.0): update it. If it reports `unsupported_flag`, a newer CLI no longer accepts the named option; update Qualia or report the flag. `proposal_rejected` means the proposal failed validation; the existing configuration is restored by the experiment. A pending recovery journal requires the recovery workflow below. The older direct file-editing Codex route remains disabled; no broader Windows permissions or repeat elevated setup are needed for proposals.

The fake operator makes a scripted change to fake classification behavior. A gain verifies the measured experiment workflow; it is not model training or proof of better qualitative judgment. Repeating it after the change is already present may correctly produce REVERT.

### Tune per-code suggestion thresholds without AI

Some codes need a lower bar to be found; others need a higher bar to avoid noise. The `thresholds` agent learns one minimum model-reported score per code from your **dev** benchmark, then lets Qualia's normal policy decide on the **validation** benchmark.

![The Tune suggestion thresholds form](../design-review/final/features/experiments-tune-form.png)

**In the app:** open **Experiments**, choose the **Classifier to tune** under **Tune suggestion thresholds**, and select **Tune thresholds**. The page stays busy while it works (seconds for offline backends, several minutes for external ones), then selects the new attempt so you can read its KEEP or REVERT decision, the thresholds it tried and the measurements. If something prevents a run, such as a missing dev benchmark, the exact reason appears instead.

**From a terminal**, the same experiment is:

```powershell
uv run qualia improve --project my-study --agent thresholds --budget 1
```

1. Import both a `dev` and a `validation` benchmark (section 14). Without a dev split the command stops before changing anything.
2. Qualia classifies a fixed sample of up to 400 dev segments with your configured classifier (or `--backend`/`--model`). It tries cutoffs from 0.05 to 0.95 for each code and keeps the one with the best F1, preferring values near 0.5 on ties. Codes with no dev examples keep their current setting.
3. It writes the result to `code_thresholds` in `config/routing.yaml` and states each change in the hypothesis, for example *Change talk default -> 0.35*.
4. Validation, tests and a confirming run decide KEEP or REVERT exactly as for other agents. A REVERT means the new cutoffs did not measurably help.

No AI operator, subscription or extra cost is involved beyond the classifier calls themselves. Thresholds work best with backends that score every code, such as Jev; keyword rules and the fake backend use constant scores, so they rarely benefit. On the demo with Jev (2026-10-04), the agent fitted thresholds from 0.20 (reflection, change) to 0.70 (question) on 400 of 6,759 dev segments. Validation macro F1 rose from 0.523 to 0.567 and 0.572 on the fresh confirmation, exact code-set match from 0.365 to 0.405, and calibration error fell from 0.050 to 0.038, so Qualia kept it (experiment 2). The run took 13 minutes and cost about $0.35 in Jev usage. With the rules backend, by contrast, the agent finds no useful change and correctly records REVERT. ![The kept Jev tuning experiment with its thresholds and measurements](../design-review/final/features/experiments-tuning-keep.png)

Kept thresholds appear in **Codebook** as *AI suggests at score ≥ 0.35*. Dev data is fitting data; Qualia never uses the protected split.

In **Experiments**, choose an attempt and read **Operator hypothesis**, **Measured validation results**, **Changed files** and **Experiment provenance**. Compare baseline, candidate and fresh confirmation. A candidate gain alone is insufficient: trusted policy also checks constraints and tests. Accepted changes receive a local commit/tag; rejected attempts retain their report and measurements.

The fake demonstration previously increased macro F1 while reducing exact code-set match. This illustrates why one improved metric is not a blanket quality claim. Inspect the complete comparison and decide whether the methodology is appropriate for your study.

![The fake demonstration's KEEP decision with baseline, candidate and confirmation measurements](../design-review/final/features/experiments-fake-keep.png)

Read the recorded decision alongside the full metric table. In this example, the displayed macro F1 rises from 0.011 to 0.242 while exact code-set match falls to zero; the screenshot demonstrates the audit workflow, not trained-model quality.

An interrupted operation can leave a pending recovery journal. Stop and use the recovery guidance below; do not bypass the lock or manually declare the experiment complete.

## 16. Export a project or reproducibility bundle

1. Select **Export** in the navigation.
2. Choose **JSON** or **CSV** under **Format**.
3. Leave **Include source text and excerpts** unchecked for the default redacted export.
4. Check **Reproducibility bundle** if you need experiment, evaluation, usage and egress evidence alongside research provenance.
5. Select **Download export** and review the resulting file before sharing it.

| Export | Included / excluded |
|---|---|
| Workspace export, default | Retains structured identities, coding history and provenance; excludes source text and free-text content, and redacts attribute values. Names and identifiers can still be sensitive. |
| Workspace export with text | Includes research text and textual definitions/notes. Treat it as research material. Evaluation prediction payloads and protected benchmark contents remain excluded. |
| Proposals and memo history | Every export includes codebook proposals, your decisions and earlier memo versions. Without text, their definitions, examples, excerpts, rationales and notes are removed. |
| Reproducibility bundle | Adds experiment/evaluation/usage/egress records and configuration hashes. It does not package raw prompt files, credentials or vault contents. |
| Analysis JSON/CSV/starters | Excludes source transcripts, but retains case metadata, selected query criteria and explicit attribute values for analysis. |
| Static demo export | Contains the approved public snapshot and its attribution, including that snapshot's public excerpts. |

A no-text frozen-codebook snapshot retains its original hash and is marked redacted; the hash identifies the original version, not the shortened copy. Include text when you intentionally need textual code definitions for reproduction. Even a text-inclusive bundle is not a full workspace backup or an automatically restorable project; there is no general bundle-import command.

CLI example:

```powershell
uv run qualia export --project my-study --bundle reproducibility --output "C:\Research\study-bundle.json"
```

Use `--include-text` only when you intentionally want the more sensitive export. General exports support `--output`; Analysis CLI prints its selected format and currently has no `--output` option. Browser Analysis downloads avoid PowerShell 5.1 redirection encoding pitfalls.

## 17. Understand the static demonstration

The static demonstration is an approved public-data snapshot, separate from your local research workspaces. Its subset contains 24 utterances from two dev transcripts with attribution. It is not a live view of your projects, private experiments or protected vault.

You can navigate sources, inspect saved coding/provenance, retrieve evidence, view the matrix, explore its fixed Analysis report and download its precomputed exports. Analysis filters are disabled because the report scope is fixed. Creating projects, importing, coding, reviewing, classifying, evaluating and codebook proposals are unavailable. The adapter serves the snapshot locally in the browser without API requests.

Do not confuse the smaller static snapshot with the editable local `demo` project. The static snapshot is published separately through GitHub Pages; building it locally does not publish anything.

## 18. Back up your work and handle interruptions

### Make a complete manual backup

There is no `qualia backup` or `qualia restore` command. The application's internal SQLite backup facility supports trusted operations, but it is not a general user-facing backup tool.

For a straightforward complete backup:

1. Finish any running import, evaluation or experiment.
2. Close Qualia's window and wait about three minutes for it to shut down (or press Ctrl+C if you started it with `uv run qualia open`). Make sure no other Qualia command is still running.
3. Locate the actual `QUALIA_HOME` folder. By default it is `%USERPROFILE%\Qualia` (for example `C:\Users\you\Qualia`).
4. Copy the **entire folder** to a new dated backup location using File Explorer or your approved backup software. Include `projects`, `vault`, any `recovery` folder, hidden project `.git` directories and all database sidecar files that are present. Do not copy just `project.db` while the app is running.
5. Check that the backup contains the expected project folders and files. Keep the original untouched until a recovery copy has been checked.
6. Protect the backup as research data. Your application-folder `.env` is separate; keep any key in your password manager or approved secret backup rather than distributing it with a study export.

Git history does not back up the research database or vault. JSON/CSV exports are useful evidence copies but are not a substitute for this full-folder backup.

To inspect a backup, keep all running instances stopped, work from a separate copy, and select that copy as `QUALIA_HOME` for a new launch. Do not overwrite a live workspace. Preserve the original while checking that projects, sources, coding and expected history appear. Application/schema upgrades can modify a restored copy on opening; keep the untouched backup too.

### Interrupted experiments and recovery

Messages such as **active or interrupted operation**, **pending recovery**, or **interrupted operation requiring recovery** intentionally block normal writes. They may accompany:

```text
projects\your-study\.qualia-operation.lock
recovery\your-study\pending.json
```

1. Check whether an operation is still running; do not start a second one.
2. If it has stopped, preserve the whole workspace and recovery directory before seeking help.
3. Report the exact sanitized error and project identifier. Do not post credentials, transcripts or vault contents.
4. Have the recovery journal, snapshot integrity and Git/database state inspected together before restoring or finalizing anything.

There is no one-command recovery workflow. Do not delete the journal, lock, database sidecars or snapshot to bypass the error. A recovery failure must remain visible rather than being reported as a consistent completed experiment.

## 19. Troubleshoot common problems

| Symptom | Check and next action |
|---|---|
| `uv`, `node`, `npm` or `git` is not recognized | Install/repair that prerequisite, then open a new PowerShell window. Run commands from the application folder. |
| Window shows a connection error | Qualia shut down after its window was closed or the computer slept for a long time. Close the window and open the Qualia icon again. With `qualia open`, keep its terminal running and check the port or `QUALIA_PORT`. |
| Requests fail after restarting | Refresh the page so it receives the current per-launch token. Do not copy tokens into URLs or browser storage. |
| Project missing | Check **Local project**, `uv run qualia list`, and that server/CLI use the same `QUALIA_HOME`. Changing the setting does not move data. |
| Invalid project identifier | Use lowercase letters/digits separated by hyphens. Windows reserved names are rejected. |
| Import rejected | Check UTF-8 encoding, selected format, exact CSV headers/mappings, nonblank text and the reported row. No partial import is committed. |
| Repeat import reports zero sources | Identical content is deduplicated. Use revised text and explicit source lineage when appropriate. |
| Codes unavailable in Workspace | Save active draft codes and freeze a version; choose that frozen version. |
| Old code name remains on a passage | Its decision retains the historical frozen name. New draft names do not rewrite old provenance. |
| Matrix/group comparison is empty | Link sources to cases and supply case attributes; source attributes are not inherited into case analyses. |
| Removing a case link/attribute seems ineffective | Links are additive. Omitted attributes remain; submit `name=` to mark missing. Link removal is unsupported. |
| Numeric field is invalid or n/a | Inspect missing/conflicting values, decimal formatting, sample size and constant fields. Select measurements explicitly. |
| Analysis export says research data changed | The displayed input hash no longer matches current data/configuration. Select **Refresh analysis** to reload the workspace evidence and report, review the result, then download the complete CSV/JSON/starter set again. This also brings in edits from another CLI/tab. |
| Analysis exceeds a budget | Narrow source/case scope, or use a smaller project when an input-table cap is exceeded. Counts are never silently truncated. |
| Static controls are disabled | You are viewing the fixed public snapshot. Use the local app for editing or new analysis criteria. |
| AI unavailable | Read **Backend availability and privacy** or run `availability`. Both improvement operators are implemented; check that the CLI meets the minimum version (an `unsupported_flag` error names an option a newer CLI dropped), your subscription sign-in and project external-processing setting. Codex uses the verified proposal workflow. |
| `subscription_auth_required` | Sign in through the official Claude CLI with your Claude subscription, or use `codex login` and choose ChatGPT. Qualia's improvement operators reject other authentication modes. No token should be pasted into Qualia. |
| Experiment says operator failed | Qualia records REVERT and retains available usage. Check native login and that the CLI meets the minimum version, then inspect permitted prompt/configuration size and validity before retrying. Do not bypass a pending recovery journal. |
| `quota` | Your provider reported a usage/rate limit. Check your own subscription allowance and retry later; Qualia will not enable paid overages or automatically retry the invocation. |
| Classification run too large | Choose **Current source** or pass explicit `--segments`; default whole-run limit is 2,000 segments. |
| No rules suggestions | Inclusion terms/name did not match. Rules perform literal keyword matching, not semantic coding. |
| A suggestion appears in several groups | It has several review reasons. Reviewing its ID resolves the same suggestion across groups. |
| No ECE caption | No scored validation run matches the suggestion's full identity. Do not interpret missing calibration as accuracy. |
| Jev key present but requests fail | `jev check` does not validate billing/authentication. Follow the setup guide and share only sanitized error status. |
| Experiment refuses dirty Git state | Review intended workspace changes. Keep reports outside the workspace or deliberately save them; do not discard research to clear the error. |
| R command unavailable | Install R separately if needed, or use the Python starter. R execution was not verified in the installed environment. |
| Pending recovery or lock | Follow the preservation steps above; do not delete the detector files. |

## 20. Understand how Qualia works

```mermaid
flowchart TD
    UI[Local browser interface] --> API[Local token-protected server]
    CLI[Qualia command line] --> Store[Store: database writer]
    API --> Store
    Store --> DB[Project SQLite database]
    API --> Analysis[Read-only analysis engine]
    Analysis --> Reports[Tables, charts and exports]
    API --> Router[AI router: privacy, budget and cache gates]
    Router --> Offline[Rules or fake: local]
    Router --> External[Explicitly enabled external classifier]
    Router --> Suggestions[Suggestions awaiting review]
    Suggestions --> Human[Human accept or reject]
    Human --> Store
    Benchmark[Validation reference labels] --> Eval[Classifier evaluation]
    Eval --> Policy[Measured KEEP or REVERT policy]
    Policy --> History[Experiment report and local Git history]
    Vault[Separate protected vault] --> Explicit[Explicit protected evaluation only]
```

The browser connects to a server bound to `127.0.0.1`. The server validates requests and carries a token in browser memory. A single Store layer writes the database; coding decisions, review feedback, evaluation/experiment evidence, usage records and frozen codebooks are protected as immutable history. Draft codes, cases, attributes and memos remain editable through their supported workflows.

Classification records the frozen codebook, model/prompt identity and spans. Every external attempt must pass privacy and budget admission before dispatch. Analysis uses the current visible snapshot and returns contributing IDs and hashes. Evaluation uses separately bound benchmarks. Improvement tests a permitted implementation change and relies on trusted measurements, never the operator's claim of success.

The boundaries make research decisions easier to inspect; they do not replace your interpretation, consent process or study design. Advanced inferential modeling, media coding, proprietary project conversion and collaborative editing remain future capabilities.

## 21. Command and keyboard reference

Run these from the application folder. Most project commands default to `demo`; include `--project my-study` to avoid working in the wrong project. IDs below are placeholders taken from your own UI/provenance, not guaranteed values.

| Task | Command pattern |
|---|---|
| Help | `uv run qualia --help` or `uv run qualia COMMAND --help` |
| Create/list projects | `uv run qualia init my-study` / `uv run qualia list` |
| Open local app | Qualia icon, `uv run qualia app` (own window, stops when closed) or `uv run qualia open` (terminal) |
| Import text | `uv run qualia import "C:\Research\interview.txt" --project my-study` |
| Add/freeze/list codes | `uv run qualia codebook add "Support" --definition "Help from others" --project my-study`; then `codebook freeze` / `codebook list` with the same project option |
| Save a draft code record | `uv run qualia codebook save "C:\Research\code.json" --project my-study --code-id CODE_ID` (with `--code-id`, only the fields in the file change) |
| Codebook proposals | `uv run qualia codebook propose --mode evidence --project my-study`; `--mode draft --backend claude --segments "12,13" --focus "waiting"`; `--mode refine --backend codex --codes "3"` |
| Review proposals | `uv run qualia codebook proposals --project my-study` (add `--all` for decided ones); `uv run qualia codebook decide PROPOSAL_ID accept --actor researcher --project my-study` (or `reject --note "..."`; `--values edits.json` to edit before accepting) |
| Code a whole segment | `uv run qualia code SEGMENT_ID CODE_ID --project my-study --actor researcher` |
| Code/remove a span | Add `--start START --end END`; add `--remove` for a removal of that code/span |
| Create a memo | `uv run qualia memo "Title" "Memo text" --project my-study --kind reflexive --source SOURCE_ID` (also `--segment`, `--code`, `--case`; with `--memo-id` only the options given change) |
| Create/link a case | `uv run qualia case "Participant 1" --project my-study --source SOURCE_ID` |
| Retrieve by code/case | `uv run qualia retrieve --project my-study --code CODE_ID --case CASE_ID` |
| Code-by-case counts | `uv run qualia matrix --project my-study` |
| Read-only analysis | `uv run qualia analyze --project my-study --group-by group --numeric age --numeric wellbeing` |
| Text/code query | `uv run qualia analyze --project my-study --query support --code CODE_ID --code-match any` |
| Backend readiness | `uv run qualia availability --project my-study` |
| Small offline classification | `uv run qualia classify --project my-study --backend rules --segments "12,13"` |
| Human review | `uv run qualia review SUGGESTION_ID accept --project my-study --actor researcher`; use `reject` to reject |
| Validation evaluation | `uv run qualia evaluate --project my-study --backend rules --output "C:\Research\reports"` |
| Fake experiment/history | `uv run qualia improve --project demo --agent fake --budget 1` / `uv run qualia history --project demo` |
| Tune suggestion thresholds (no AI) | `uv run qualia improve --project my-study --agent thresholds --budget 1` (or **Experiments → Tune thresholds**) |
| AI-proposed improvement | `uv run qualia improve --project my-study --agent claude --budget 1` (or `--agent codex`) |
| Jev readiness / opt in / opt out | `uv run qualia jev check --project my-study` / `jev enable` / `jev disable` with the same project option |
| Bundle export | `uv run qualia export --project my-study --bundle reproducibility --output "C:\Research\bundle.json"` |

For Analysis, repeat `--code`, `--numeric` or `--stopword` for multiple selections. `--source-id`, `--case-id`, `--cooccurrence segment|overlap` and `--format json|csv|python|r` are available. Classification's `--segments` instead takes a comma-separated string. Do not paste literal placeholder names such as `SEGMENT_ID` into a real command.

| Keyboard action | Where it works |
|---|---|
| ↑ / ↓ | Move between segments in Workspace. |
| 1–9 | Apply the corresponding displayed frozen code in Workspace. |
| Escape | Clear the current span selection in Workspace. |
| a / r | Accept/reject the selected suggestion in Workspace or Review. |
| Enter / Space | Activate a focused analysis chart bar or scatter point. |

Typing in an input field does not trigger coding/review shortcuts. Saving and read-only states disable mutations. You can always use the visible buttons instead.

Related references: [Jev setup](JEV-SETUP.md), [dataset provenance](../DATA-LICENSES.md), [project README](../README.md), and [current build status](BUILD-STATE.md).
