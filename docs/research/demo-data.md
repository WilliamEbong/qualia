# Demo dataset research: AnnoMI

Verified 2026-10-03 (America/Denver). Research only: all downloaded data stayed under the OS temporary directory. No data was written to `demo/data/`, no application code was changed, and no commit was made by this research lane.

## Pinned source and byte checksums

Official repository: [uccollab/AnnoMI](https://github.com/uccollab/AnnoMI). `git ls-remote ... HEAD` and a temporary clone both resolved to:

```text
42936645ec3857a9c84ab296a36a3c34b779ef49
2023-03-14T11:05:28Z
Updated dataset versions.
```

Use **AnnoMI-simple.csv** for the V1 seeded demo: one row per utterance, seven high-level labels. It avoids arbitrarily resolving multiple annotator judgments. The full file is useful for later raw inter-annotator analysis and must not be imported as 13,551 distinct utterances.

| Artifact at that commit | Bytes | SHA-256 |
|---|---:|---|
| `AnnoMI-simple.csv` | 2386609 | `b178db3b0b9858a0fa4ed670dabeccd63e975ba67e141d7ae16f2e8214f78e61` |
| `AnnoMI-full.csv` | 3795371 | `3b60fec5e9d83cbb18ade0e412fb9afaef3b81724748a5d715f844bdd7432c9f` |
| `README.md` | — | `45fd4a9e30e3cf0f727f120159a8042eefc0dacdf1c4fe576859a4bfd815948c` |

Pinned raw download URL for the future fetch script:

```text
https://raw.githubusercontent.com/uccollab/AnnoMI/42936645ec3857a9c84ab296a36a3c34b779ef49/AnnoMI-simple.csv
```

The simple file's checksum was independently identical between a clone with `core.autocrlf=false` and a direct raw HTTPS download using Node's standard HTTPS client. Hash raw bytes **before** decoding or newline conversion. The other hashes came from the same no-conversion clone. Source links: [pinned simple CSV](https://raw.githubusercontent.com/uccollab/AnnoMI/42936645ec3857a9c84ab296a36a3c34b779ef49/AnnoMI-simple.csv), [pinned full CSV](https://raw.githubusercontent.com/uccollab/AnnoMI/42936645ec3857a9c84ab296a36a3c34b779ef49/AnnoMI-full.csv), [pinned README](https://github.com/uccollab/AnnoMI/blob/42936645ec3857a9c84ab296a36a3c34b779ef49/README.md).

Transport note: PowerShell `Invoke-WebRequest` failed with TLS authentication and Windows `curl.exe` failed with `SEC_E_NO_CREDENTIALS`. Git HTTPS and Node HTTPS succeeded without disabling certificate verification. This was a local transport problem, not an unreachable AnnoMI pin; the fallback dataset was not needed.

## Counts measured from the pinned CSVs

Both files contain 133 transcripts and 9,699 unique `(transcript_id, utterance_id)` pairs. Simple has 9,699 rows; full has 13,551 rows because some utterances have multiple annotators. Full annotator IDs run from `0` through `9`. There are 119 distinct video URLs, 110 high-quality transcripts, and 23 low-quality transcripts. Simple contains 8,839 high-quality utterances and 860 low-quality utterances.

| Role | Simple-file label | Rows |
|---|---|---:|
| therapist | reflection | 1296 |
| therapist | question | 1386 |
| therapist | therapist_input | 614 |
| therapist | other | 1586 |
| client | change | 1174 |
| client | neutral | 3102 |
| client | sustain | 541 |

These are computed from the pinned bytes, not copied from a secondary paper whose label counts may differ. Keep the minority labels in metric reports and show per-code support.

## Columns and import mapping

Exact simple CSV header order:

```text
transcript_id,mi_quality,video_title,video_url,topic,utterance_id,interlocutor,timestamp,utterance_text,main_therapist_behaviour,client_talk_type
```

`transcript_id` identifies a conversation, not chronology. Sort utterances numerically by `utterance_id` within each transcript. Treat transcript IDs as stable keys and preserve `utterance_id` in provenance. Map each conversation to a case; `mi_quality` is a case attribute with `high`/`low` values, describing demonstrated MI quality. Speaker comes from `interlocutor`; text comes from `utterance_text`. Keep title, URL, topic, and timestamp as metadata. [Upstream field descriptions](https://github.com/uccollab/AnnoMI/blob/42936645ec3857a9c84ab296a36a3c34b779ef49/README.md)

For the future demo importer:

- Create utterance-aligned segments, not a sentence resegmentation that breaks label alignment.
- Read CSV with a real parser; quoted commas/newlines must survive unchanged. Preserve `n/a` as an explicit non-applicable field, never a code or inferred negative.
- Assign each therapist row its `main_therapist_behaviour`, each client row its `client_talk_type`. Record the imported label as a human annotation with dataset/source identity, not as a new owner judgment or a named annotator that simple does not supply.
- Derive stable source/segment IDs from the pinned corpus identity plus transcript/utterance ID. A second `qualia demo` must add no duplicates.
- Keep gold labels out of model input. Role, text, and chosen conversational context may be input; label columns must remain evaluation targets.

Full retains the simple fields but uses a different column order and additionally contains `annotator_id`, `therapist_input_exists`, `therapist_input_subtype`, `reflection_exists`, `reflection_subtype`, `question_exists`, and `question_subtype`. It allows therapist-input subtypes `information/advice/negotiation/options`, reflection `simple/complex`, and question `open/closed`. A future full importer must key judgment rows by annotator as well as utterance. [Full-file field descriptions](https://github.com/uccollab/AnnoMI/blob/42936645ec3857a9c84ab296a36a3c34b779ef49/README.md)

## Codebook meanings and limits

The README defines field domains and label names, but does not contain a complete inclusion/exclusion/examples codebook. Do not present invented detailed rules as the authors' codebook. The following concise meanings are paraphrases supported by the authors' expanded paper; the role restriction is also present in the CSV/README:

| Code | Meaning for the initial demo definition |
|---|---|
| reflection | Therapist expresses understanding of what the client has said. |
| question | Therapist asks an inquiry to obtain information or explore the client's perspective. |
| therapist_input | Therapist offers information, advice, or other input. |
| other | Therapist utterance outside the listed main behaviors. |
| change | Client language favoring positive behavior change. |
| sustain | Client language favoring continuation of the status quo. |
| neutral | Client language expressing neither change nor sustain. |

Source: [Wu et al., 2023, annotation and corpus analysis](https://www.mdpi.com/1999-5903/15/3/110). Freeze these as an explicitly attributed demo codebook. If fuller inclusion/exclusion examples are later authored, label them as Qualia's operationalization and require the methodology workflow; never silently change frozen versions. No therapeutic effectiveness claim follows from this demo.

## Split strategy for the implementation lane

The contract requires transcript-level 60/20/20 dev/validation/protected splits. Recommended deterministic implementation: within each `mi_quality` stratum, rank unique transcript IDs by SHA-256 of the UTF-8 string `qualia-annomi-v1:<transcript_id>` (normalize IDs to decimal strings); break any digest tie by numeric transcript ID. Allocate the following counts in that rank order:

| Stratum | Dev | Validation | Protected |
|---|---:|---:|---:|
| high (110) | 66 | 22 | 22 |
| low (23) | 14 | 4 | 5 |
| total (133) | 80 | 26 | 27 |

This is a proposed reproducible rounding/stratification choice for the main lane to record, not an upstream split and not an already-generated manifest. It approximates 60/20/20 while keeping both qualities in each set. Put all utterances from a transcript in one split and persist the resulting IDs and corpus hash once; never recompute a new split after an experiment.

Leakage checks: assert pairwise-disjoint transcript IDs and complete coverage. Because 133 conversations come from 119 videos, also report video URL overlap between splits; transcript isolation alone does not guarantee source-video independence. A stricter video-group split would be a separately documented methodology choice. Public content may also have appeared in model training. Protected data prevents optimization access; it does not prove absence of pretraining exposure.

Store protected examples only under `QUALIA_HOME/vault/<slug>/`, covered by the manifest. Neither the improvement operator nor public snapshot receives protected text or labels. Dev/validation benchmark records likewise live in the project workspace, never in the application repository.

## Licensing evidence

The pinned repository root contains exactly `AnnoMI-full.csv`, `AnnoMI-simple.csv`, and `README.md`; there is **no LICENSE file**. The original authors' 2023 paper's Data Availability Statement explicitly identifies AnnoMI as available under a **Public Domain License**. This verifies the documentary basis stated in the build brief; it does not identify a particular SPDX dedication such as CC0. Avoid asserting “CC0-1.0” unless a primary source supplies it. [Paper, Data Availability Statement](https://www.mdpi.com/1999-5903/15/3/110)

The paper also reports obtaining permission to create and release the transcript dataset. Do not infer permission to redistribute the underlying videos, images, or audio. The eventual `DATA-LICENSES.md` should separate Qualia's MIT software license, this dataset's author-stated public-domain status, and the paper's own publication license. Cite Wu et al. (2022), DOI `10.1109/ICASSP43922.2022.9746035`, and Wu et al. (2023), DOI `10.3390/fi15030110`, as upstream requests. Recheck the primary licensing evidence before the public snapshot ships.

The native web fetch of MDPI returned HTTP 429; a targeted Firecrawl JSON extraction successfully recovered the primary Data Availability Statement. No third-party repository's claimed license was used as the authority.

## Pre-authorized fallback: Zenodo 15698094

[Record 15698094](https://zenodo.org/records/15698094) is available: *Code-aware LLM prompting in deductive qualitative analysis: codebook, dataset, prompts, qualitative coding, and agreement report*, version v1, published June 19, 2025. Its rights metadata identifies **CC BY 4.0**, verified by targeted extraction when native fetch omitted the license text.

The record describes 35 multimedia learning designs containing 758 activities and a 13-code, three-framework codebook. The workbook `Codebook, datset & coding.xlsx` contains codebook and coding sheets; the Human sheet represents agreement between two experts, not necessarily their independent raw labels. Listed workbook checksum is MD5 `f88fce82c62e1819c7c7f2e44dc3394d`. Its contents were not downloaded or independently parsed here, so no SHA-256, sheet-column contract, or ready importer is claimed. Do not run the bundled prompting Python scripts. An XLSX-to-CSV preparation step would be needed without adding XLSX import to V1. [Record and file listing](https://zenodo.org/records/15698094)

AnnoMI is reachable and its exact pin is verified, so no fallback activation is justified now.
