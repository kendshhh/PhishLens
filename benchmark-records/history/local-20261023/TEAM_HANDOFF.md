# AI benchmark handoff — October 23, 2026

Latest evidence: output/benchmarks/local-20261023/. Open visuals/three-local-comparison.pdf or visuals/05-three-local-results.png; Graph.csv contains the same-cohort statistics.

Three local models completed the same 500-email screen (394 source-negative, 106 source-positive):
- DistilBERT strict: 0 false alarms, 27.4% recall.
- Llama 3.2 3B: 120 false alarms, 80.2% recall.
- Phi-4 Mini 3.8B: 76 false alarms, 50.9% recall.

No model is validated for the requested ≤0.1% false-alarm ceiling. The screen's DistilBERT upper 95% bound is 0.932%; its earlier 5,000-email test upper bound is 0.256%. Llama/Phi were ruled out by the predeclared screening rule. The results apply to the recorded prompts, windows and batching configuration.

OmniRoute 3.8.52 was used with a single local connection; no paid APIs. Native JSON enforcement fixes and earlier failed/diagnostic runs remain in the history. Compact prompts reduced reported tokens by 3.7% /3.2%, while each model changed 2/16 validation predictions. All saved weights, per-run recoverable snapshots, source hashes and route headers are retained. Task runtimes were stopped after measurement.

Backend/full-stack: this binary experiment groups spam/fraud/phishing as source-positive. It does not validate the production three-class/evidence contract or database persistence. The benchmark-only gateway is installed in the original Codex workspace, with configuration and exact sources archived here. See the older kaggle-free-20261022/TEAM_HANDOFF.md for the contract snapshot and project_refs.json for freshly observed Git references; no checkout or model deployment was performed.
