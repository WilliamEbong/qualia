# Import text, Markdown and mapped CSV

Guide sections: 4
Target length: 3–4 min
Starting state: practice-study after created

1. Select `practice-study` in `Local project`, then select `Workspace`. — "Check the project before importing research material."
2. Select `Import source`. — "The import form accepts text, Markdown and mapped CSV."
3. Set `File format` to `Plain text` and enter `practice-note` in `Source name`. — "A source name helps you identify the imported document."
4. Paste the following into `Or paste source text`. — "Blank-line paragraphs become separate segments by default."

   ```text
   My sister gives me support when work feels stressful.

   I feel pressure at work and take a short walk afterward.
   ```

5. Leave `Source version` at `New source`; select `Import into project`. — "A new document starts a new source."
6. Select the imported source under `Sources` and inspect both segments. — "Inspect the segmentation before you begin coding."
7. Select `Import transcript`; set `File format` to `Markdown` and `Source name` to `practice-markdown`. — "Choose the file format explicitly for each import."
8. Paste `Support from friends helps me manage pressure.` into `Or paste source text`; select `Import into project`. — "You can paste source text instead of choosing a file."
9. [card] Save the following UTF-8 file as `practice.csv` outside the application folder. — "CSV imports use a header row and one text record per row."

   ```csv
   text,case,speaker,group,age,wellbeing
   "My sister gives me support when work feels stressful.",p01,Participant,north,24,4
   "I feel pressure at work and take a short walk afterward.",p02,Participant,south,36,6
   "Support from friends helps me manage pressure.",p03,Participant,north,48,8
   ```

10. Select `Import source`, then `File`; [card] show `Choose practice.csv in the file picker`. — "Use UTF-8 files so the imported text is read correctly."
11. Set `File format` to `CSV with column mapping`; expand `CSV column mapping`. — "The mapping uses exact, case-sensitive column names."
12. Keep `Text column` as `text`, `Case column` as `case` and `Speaker column` as `speaker`. — "A speaker label alone does not create a case."
13. Enter `group,age,wellbeing` in `Attribute columns`; select `Import into project`. — "Mapped attributes belong to the case when the row supplies one."
14. Inspect `Cases` and the import notice without promising a fixed new-source count. — "Identical text is stored once, even when it is imported again."
15. Select `Import source`; paste the original two-paragraph note and select `Import into project`. — "A repeated import can report zero new sources."
16. Select `Import source`; enter `practice-note-revised` in `Source name`. — "Use explicit source lineage when importing revised text."
17. Choose `New version of practice-note` in `Source version`. — "The revision points back to its earlier source."
18. Paste `My sister gives me support when work feels stressful today.` into `Or paste source text`. — "Changed text creates an immutable new source."
19. Select `Import into project`, then inspect the original and revised sources under `Sources`. — "Old text and coding remain available, but coding does not transfer automatically."
