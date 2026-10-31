"""Build real auxiliary product artifacts; never read held-out/final mail.

Run with the existing scientific dependencies plus LightGBM. No new benchmark,
test-set scoring, AI labels, synthetic mail or threshold change to v12a.
"""
import argparse
from collections import Counter
from datetime import datetime, UTC
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, allow_nan=False, separators=(",", ":")) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--science", type=Path, required=True)
    parser.add_argument("--lightgbm", type=Path, default=ROOT / ".runtime/lightgbm")
    args = parser.parse_args()
    sys.path[:0] = [str(args.science), str(args.lightgbm)]
    import numpy as np
    from scipy import sparse
    import sklearn
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import Ridge, LogisticRegression
    from sklearn.kernel_ridge import KernelRidge
    import lightgbm as lgb

    base = args.data_root.resolve()
    manifest = json.loads((base / "data/manifest.json").read_text(encoding="utf-8"))
    if not manifest.get("training_permitted") or manifest.get("synthetic_primary_rows") != 0:
        raise RuntimeError("Existing data admission does not permit nonsynthetic training")
    roles = {}
    provenance = {}
    for role in ("train_development", "calibration", "threshold"):
        item = manifest["outputs"][role]
        path = (base / item["path"]).resolve()
        if not path.is_relative_to(base) or digest(path) != item["sha256"]:
            raise RuntimeError("Role path/hash changed")
        rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]
        if any(row["label"] not in (0, 1) or not row.get("_group") for row in rows):
            raise RuntimeError("Invalid labels/groups")
        roles[role] = rows
        provenance[role] = {"sha256": item["sha256"], "rows": len(rows),
                            "labels": dict(Counter(r["label"] for r in rows))}
    for i, left in enumerate(roles):
        for right in list(roles)[i + 1:]:
            if ({r["_group"] for r in roles[left]} & {r["_group"] for r in roles[right]} or
                    {r["text"] for r in roles[left]} & {r["text"] for r in roles[right]}):
                raise RuntimeError("Role leakage detected; training stopped")
    if sum(r["label"] == 0 for r in roles["threshold"]) < 1000:
        raise RuntimeError("At least 1000 legitimate threshold records are required")
    artifact_path = ROOT / "extension/ai/tfidf_v12a.json"
    basis_sha = digest(artifact_path)
    if basis_sha != "a2f13c256dd46c3267263f8de8f4f822206c5b0ceda96658713e2523a7f9559c":
        raise RuntimeError("Primary model changed")
    artifact = json.loads(artifact_path.read_text())
    vectors = []
    for block in artifact["blocks"]:
        vectorizer = TfidfVectorizer(analyzer=block["analyzer"], ngram_range=tuple(block["ngram_range"]),
                                    vocabulary=block["vocabulary"], sublinear_tf=True, dtype=np.float64)
        vectorizer.idf_ = np.asarray(block["idf"], dtype=np.float64)
        vectors.append(vectorizer)
    matrices = {role: sparse.hstack([v.transform([r["text"] for r in rows]) for v in vectors], format="csr")
                for role, rows in roles.items()}
    labels = {role: np.asarray([r["label"] for r in rows]) for role, rows in roles.items()}
    rows = roles["train_development"]
    class_mass = Counter(r["label"] for r in rows)
    source_families, family_rows = {}, Counter()
    for row in rows:
        key = row["label"], row["source"]
        source_families.setdefault(key, set()).add(row["_group"])
        family_rows[key + (row["_group"],)] += 1
    sources = Counter(label for label, _ in source_families)
    weights = np.asarray([class_mass[r["label"]] / sources[r["label"]] /
                          len(source_families[r["label"], r["source"]]) /
                          family_rows[r["label"], r["source"], r["_group"]] for r in rows])
    weights /= weights.mean()

    # Numerical software fixture only. This is not synthetic email or accuracy data.
    fixture = np.random.default_rng(42).normal(size=(12, 5))
    target = np.arange(12) % 2
    weighted = np.linspace(.5, 1.5, 12)
    primal = Ridge(alpha=1, fit_intercept=False, solver="lsqr", tol=1e-12).fit(fixture, target, sample_weight=weighted)
    dual = KernelRidge(alpha=1, kernel="linear").fit(fixture, target, sample_weight=weighted)
    equivalence = float(np.max(np.abs(primal.predict(fixture) - dual.predict(fixture))))
    if equivalence > 1e-10:
        raise RuntimeError("Primal fit does not match linear-kernel KRR")

    x = matrices["train_development"]
    krr = Ridge(alpha=1, fit_intercept=False, solver="lsqr", tol=1e-8, max_iter=10000)
    krr.fit(x, labels["train_development"], sample_weight=weights)
    if krr.n_iter_ is not None and int(np.max(krr.n_iter_)) >= 10000:
        raise RuntimeError("KRR solver reached its iteration limit")
    print("Fitted linear-kernel KRR on admitted training data", flush=True)
    gbm = lgb.LGBMClassifier(objective="binary", n_estimators=100, max_depth=3, num_leaves=7,
                            learning_rate=.05, min_child_samples=30, random_state=42,
                            n_jobs=1, verbosity=-1, deterministic=True, force_col_wise=True)
    gbm.fit(x, labels["train_development"], sample_weight=weights)
    if list(gbm.classes_) != [0, 1]:
        raise RuntimeError("LightGBM positive label mapping is not phishing=1")
    print("Fitted genuine LightGBM classifier", flush=True)
    out = ROOT / "extension/ai/reevaluators"
    records = {}
    for name, model in (("krr", krr), ("lightgbm", gbm)):
        def predict(matrix):
            return model.predict(matrix, raw_score=True) if name == "lightgbm" else model.predict(matrix)
        cal = np.asarray(predict(matrices["calibration"])).ravel()
        mapper = LogisticRegression(C=1e6, solver="lbfgs", max_iter=1000, random_state=42)
        mapper.fit(cal.reshape(-1, 1), labels["calibration"])
        slope, intercept = float(mapper.coef_[0, 0]), float(mapper.intercept_[0])
        if slope <= 0 or mapper.n_iter_.max() >= 1000:
            raise RuntimeError("Non-monotonic or unconverged score mapping")
        threshold_scores = np.asarray(predict(matrices["threshold"])).ravel()
        negatives = np.sort(threshold_scores[labels["threshold"] == 0])[::-1]
        cutoff = float(np.nextafter(negatives[int(np.floor(.02 * len(negatives)))], np.inf))
        if np.mean(negatives >= cutoff) > .02 + 1e-12:
            raise RuntimeError("Threshold violates frozen validation FPR ceiling")
        exported = {"kind": name, "model_id": name + "_live_review_20261029", "classes": [0, 1],
                    "positive_label": "phishing", "basis_sha256": basis_sha,
                    "feature_count": 30000, "cutoff": cutoff,
                    "mapping": {"kind": "margin_sigmoid", "slope": slope, "intercept": intercept}}
        if name == "krr":
            exported.update(kernel="linear", alpha=1, fit_intercept=False,
                            coefficients=krr.coef_.tolist(), intercept=0)
        else:
            dumped = gbm.booster_.dump_model()
            if dumped["average_output"] or not dumped["objective"].startswith("binary sigmoid:1"):
                raise RuntimeError("Unsupported LightGBM score convention")
            exported.update(trees=[t["tree_structure"] for t in dumped["tree_info"]], objective="binary_sigmoid_1")
        write(out / (name + ".json"), exported)
        records[name] = {"file": name + ".json", "sha256": digest(out / (name + ".json")),
                         "bytes": (out / (name + ".json")).stat().st_size}
    write(out / "manifest.json", {"schema_version": 1, "seed": 42, "basis_sha256": basis_sha,
                                   "models": records, "release": "unanimity_and_supported_judge"})
    record = {"purpose": "product_artifact_build_not_new_benchmark", "at_utc": datetime.now(UTC).isoformat(),
              "seed": 42, "basis_sha256": basis_sha, "roles_read": provenance,
              "final_or_reserved_records_opened": 0, "synthetic_emails": 0,
              "krr_primal_dual_max_difference": equivalence,
              "versions": {"numpy": np.__version__, "sklearn": sklearn.__version__, "lightgbm": lgb.__version__},
              "artifacts": records}
    write(ROOT / "implementation/live_review/results/build_record.json", record)
    # Small, already-exposed development rows only. Keep text outside Git.
    checks = roles["calibration"][:12]
    fixture_matrix = matrices["calibration"][:12]
    write(ROOT / ".runtime/live-review-parity.private.json", {
        "rows": [{"text": r["text"], "krr": float(a), "lightgbm": float(b)}
                 for r, a, b in zip(checks, krr.predict(fixture_matrix), gbm.predict(fixture_matrix, raw_score=True))]})
    print(json.dumps({"built": records, "held_out_records_opened": 0}), flush=True)


if __name__ == "__main__":
    main()
