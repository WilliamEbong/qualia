# Export evidence, continue in Python or R and make a backup

Guide sections: 11, 16, 18
Target length: 4 min
Starting state: practice-study after coded

Recording note: Use the unchanged section 3 snapshot; cards show external actions, with no claim that R is installed or has been run.

1. Select `practice-study` in `Local project`, then select `Analysis`. — "Set the intended analysis scope before downloading related files."
2. Under `Analysis criteria`, keep `All sources` in `Analysis source` and `All cases` in `Analysis case`. — "The exported case table follows the report's selected evidence."
3. Select `age` and `wellbeing` under `Explicit numeric case attributes`; select `Apply analysis criteria`. — "Choose the measurements you want to continue analyzing."
4. Inspect `Applied criteria`, then select `Download case CSV`. — "The CSV has one row per eligible case."
5. Select `Download analysis JSON`. — "The companion JSON retains criteria, input identity and the column dictionary."
6. Select `Download Python starter`. — "The Python starter uses Python 3.10 or newer and its standard library."
7. Select `Download R starter`. — "The R starter uses base R, which must be installed separately."
8. [card] Show `Keep qualia-analysis.csv, qualia-analysis.json, qualia-analysis.py and qualia-analysis.R together`. — "Keep the files from one report together in a research output folder."
9. [card] Show `Review the downloaded data and starter files before running them`. — "Analysis exports retain case metadata and query criteria, so they are not anonymous."
10. [card] From the output folder, show `python qualia-analysis.py qualia-analysis.csv`. — "Run the Python starter deliberately outside Qualia."
11. [card] Show `With R installed: Rscript qualia-analysis.R qualia-analysis.csv`. — "The guide does not claim verified R execution in its tested environment."
12. [card] Show `Starters reproduce numeric summaries, correlations and case-level code prevalence`. — "A case table cannot reconstruct every segment-level chart or source excerpt."
13. Return to `Analysis` and select `Refresh analysis`. — "If research data changes, refresh and download the related files again as a set."
14. Select `Export` in the navigation. — "Workspace exports have different privacy defaults from Analysis downloads."
15. Set `Format` to `JSON`. — "JSON keeps structured research identities and provenance together."
16. [zoom] Leave `Include source text and excerpts` unchecked. — "The default export removes source text and free-text content."
17. Check `Reproducibility bundle`. — "A bundle adds experiment, evaluation, usage and egress evidence."
18. Select `Download export`. — "Names and identifiers can still be sensitive in a redacted export."
19. [card] Show `Review the downloaded bundle before sharing it`. — "Exports include proposal decisions and earlier memo versions."
20. Select `Export` again, set `Format` to `CSV`, keep text excluded and select `Download export`. — "Choose the export format that fits the next stage of your work."
21. [card] Show `An export is evidence, not a full workspace backup; there is no general bundle import`. — "Even a text-inclusive bundle is not an automatically restorable project."
22. [card] Show `Finish running imports, evaluations and experiments before backing up`. — "A complete manual backup begins with all operations finished."
23. [card] Show `Close Qualia and wait about three minutes; confirm no Qualia command is running`. — "Stop the application before copying the research workspace."
24. [card] Show `Locate the actual QUALIA_HOME folder; default: %USERPROFILE%\Qualia`. — "Use the actual research location if you selected a custom home folder."
25. [card] Show `Copy the entire home folder to a new dated backup location`. — "Include projects, vault, recovery, hidden project .git folders and database sidecars."
26. [card] Show `Check the copied project folders and files; keep the original untouched`. — "Do not copy only project.db while the app is running."
27. [card] Show `Protect the backup as research data; inspect a separate copy with all instances stopped`. — "Git history and JSON or CSV exports do not replace a full-folder backup."
28. [card] Show `For inspection, select a separate copy as QUALIA_HOME and preserve the untouched backup`. — "Opening a restored copy can upgrade its database, so retain the original backup."
29. [card] Show `Pending recovery: preserve the workspace and recovery directory, then seek help`. — "Do not delete recovery journals, locks or sidecars to bypass an interruption."
