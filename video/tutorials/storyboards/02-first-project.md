# Make your first practice project

Guide sections: 3
Target length: 4 min
Starting state: empty workspace

1. Expand `New project`. — "Use synthetic material to learn the workflow before starting real research."
2. Enter `practice-study` in `Project identifier`. — "Project identifiers use lowercase letters, digits and hyphens."
3. Select `Create local project`. — "A project keeps its own material, codebook, settings and history."
4. [card] In Notepad, save the following as `practice.csv` with `All Files` and UTF-8 encoding. — "Keep the practice CSV outside the application folder."

   ```csv
   text,case,speaker,group,age,wellbeing
   "My sister gives me support when work feels stressful.",p01,Participant,north,24,4
   "I feel pressure at work and take a short walk afterward.",p02,Participant,south,36,6
   "Support from friends helps me manage pressure.",p03,Participant,north,48,8
   ```

5. Select `Workspace`, then `Import source`. — "Import the three synthetic responses into this project."
6. Select `File`; [card] show `Choose practice.csv in the file picker`. — "Choose the UTF-8 file you just saved."
7. Set `File format` to `CSV with column mapping` and expand `CSV column mapping`. — "Column mapping connects each response to its case and attributes."
8. Keep `Text column` as `text`, `Case column` as `case` and `Speaker column` as `speaker`. — "Column names must match the CSV headers exactly."
9. Enter `group,age,wellbeing` in `Attribute columns`; select `Import into project`. — "The mapped measurements belong to each participant case."
10. Inspect `Sources` and `Cases`; select each source to see its single segment. — "The expected result is three sources, three segments and three linked cases."
11. Select `Codebook`; under `Create code`, enter `Support` in `Name`. — "Start with a code for help from other people."
12. Enter `Practical or emotional help from other people.` in `Definition`; select `Save draft code`. — "Saving a draft records your definition before you freeze it."
13. Under `Create code`, enter `Pressure` in `Name` and `Experienced demands or stress.` in `Definition`. — "The second code describes experienced demands or stress."
14. Select `Save draft code`, then `Freeze codebook`. — "A frozen version makes these definitions available for coding."
15. Select `Workspace`; enter `researcher` in `Human actor` and choose the new `Frozen codebook`. — "Each coding decision records its actor and frozen codebook version."
16. Select the source containing the sister response; click its segment, then `Support`. — "Assign Support to the whole first response."
17. Wait for saving to finish; select the source containing the short walk response, then `Pressure`. — "Assign Pressure to the whole second response."
18. Select the source containing the friends response; click `Support`, wait, then click `Pressure`. — "Both codes can apply to the same passage."
19. Select `Analysis` and read `Code frequencies` with no filters applied. — "Each code appears on two of three segments and two of three cases."
20. [zoom] Inspect `Segment %` and `Case %` for both codes. — "Both percentages should be approximately 66.667 percent."
21. Under `Analysis criteria`, set `Group by case attribute` to `group`. — "The practice cases belong to north and south groups."
22. Select `age` and `wellbeing` under `Explicit numeric case attributes`. — "Choose deliberately which attributes represent measurements."
23. Select `Apply analysis criteria`; expand the groups in `Case-group comparisons`. — "North contains two cases and south contains one."
24. Inspect `Numeric case attributes`: age mean and median 36, sample SD 12; wellbeing mean 6, sample SD 2. — "The constructed measurements give results that are easy to check."
25. Inspect `Numeric relationships` for the age and wellbeing pair, with `Pearson r` equal to 1. — "This is a software exercise, not a research finding."
