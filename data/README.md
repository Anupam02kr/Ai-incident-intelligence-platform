# Data sources

This folder holds raw log samples used to build and test the log
normaliser, Drain3 template mining, and (later) the classifier.

## HDFS (data/raw/hdfs/)

- Source: Loghub — https://github.com/logpai/loghub (HDFS_v1)
- Files used: `HDFS_2k.log`, `HDFS_2k.log_structured.csv`, `HDFS_templates.csv`
- Generated in a private cloud environment using benchmark workloads,
  manually labeled for anomalies (label file is in the full dataset,
  not the 2k sample used here).
- License: research/academic use. See the Loghub repo for the current
  terms before using this outside a student project.

## OpenSSH (data/raw/openssh/)

- Source: Loghub — https://github.com/logpai/loghub (OpenSSH)
- Files used: `OpenSSH_2k.log`, `OpenSSH_2k.log_structured.csv`, `OpenSSH_2k.log_templates.csv`
- Real SSH daemon logs, unlabeled.
- License: same as above — research/academic use per Loghub's terms.

## Citation

If referencing this data in the README, report, or demo, cite the
Loghub paper:

Zhu, J., He, S., He, P., Liu, J., Lyu, M.R. "Loghub: A Large Collection
of System Log Datasets for AI-driven Log Analytics." ISSRE 2023.

## Notes

- Raw log files are gitignored — this repo only tracks this README,
  not the actual `.log`/`.csv` data. Re-download from the links above
  if setting this up on a new machine.
- 2k-line samples are enough for building and testing the normaliser
  and Drain3. The full HDFS dataset (with `anomaly_label.csv`) is
  needed later for classifier evaluation — request it via the form
  linked from the HDFS_v1 page in the Loghub repo.
