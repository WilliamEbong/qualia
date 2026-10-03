# Data provenance and permissions

Qualia software is MIT licensed. Dataset rights are separate.

The optional AnnoMI demo uses `AnnoMI-simple.csv` from the authors' repository,
pinned to commit `42936645ec3857a9c84ab296a36a3c34b779ef49`.
Raw-byte SHA-256: `b178db3b0b9858a0fa4ed670dabeccd63e975ba67e141d7ae16f2e8214f78e61`.

The authors' [2023 Data Availability Statement](https://www.mdpi.com/1999-5903/15/3/110)
states that AnnoMI is available under a Public Domain License. The pinned repository has no
LICENSE file; this is the documented basis, not an assertion of a particular SPDX dedication.
No video, audio, or images from the underlying recordings are redistributed.

Please cite Wu et al., [2022](https://doi.org/10.1109/ICASSP43922.2022.9746035) and
[2023](https://doi.org/10.3390/fi15030110). The seven label domains come from the
[pinned README](https://github.com/uccollab/AnnoMI/blob/42936645ec3857a9c84ab296a36a3c34b779ef49/README.md).
Concise code definitions paraphrase the authors' paper. No invented inclusion/exclusion examples
are represented as upstream definitions. Imported labels identify the dataset's expert annotations;
the simple file does not supply individual annotator identities.

The original data remains in ignored local storage. Dev and validation transcripts enter the demo
workspace; protected transcripts exist only in its sibling vault. Splits are Qualia's deterministic
quality-stratified transcript split, not an upstream split. Source videos overlap across some splits;
transcript isolation does not establish video independence or absence from model training.
See [research evidence](docs/research/demo-data.md) for counts, exact rounding and limitations.

The pre-authorized Zenodo fallback is not used: the pinned AnnoMI source is reachable.
Any public static snapshot requires the separate Phase 8 license and protected-data check.
