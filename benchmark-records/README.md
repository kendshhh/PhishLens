# Preserved benchmark evidence

Open **index.html** in a browser. This folder is an indexed snapshot of public
summaries, metrics, CSVs, charts, frozen configurations and run records.
`manifest.json` identifies every copied file, original path, size and SHA-256.
The files were copied without changing their historical claims or failures.

Read `tfidf_false_alarm_v12a/summary.md` for the selected integration candidate.
The eight scoped checks passed; original full OOD/adversarial qualification is
still incomplete. Earlier neural models were not retested on that final cohort.

The earlier Gemini/Phi/Llama-3B experiments remain separate from the later
three-model study, compact-classifier study and TF-IDF improvement study.

The complete original working records, private predictions, source email and
review cards remain at `D:\Phishlens\PhishLens\benchmarks` and
`D:\Phishlens\PhishLens\output\benchmarks`. Nothing there was deleted or moved.
This archive deliberately excludes raw mail, private fixtures, review messages,
large model downloads, runtime dependencies and credentials. Some historical
relative links point to those excluded files; consult the recorded original path
for a local/private review. These files are not part of the extension package.

Recreate the allowlisted snapshot, using the original checkout as source:

```powershell
python scripts/archive_benchmark_records.py --source D:\Phishlens\PhishLens
```

The command refuses to replace a snapshot file with different bytes. Verify all
archived evidence with `npm run phishlens -- records-check`.
