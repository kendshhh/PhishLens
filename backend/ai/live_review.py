"""Replay auxiliary classifiers and validate browser-reported review metadata.

The server does not claim to have rerun the browser's LLM. Client audit metadata
is explicitly attributed; authoritative stored classification remains server-owned.
"""
import hashlib
import json
import math
from collections import Counter
from functools import lru_cache

from backend.ai.tfidf_provider import (
    ASSETS,
    MODEL_SHA256,
    WORD,
    load_artifact,
    prepare_plain,
    sigmoid,
)

JUDGE_ID = "onnx-community/Llama-3.2-1B-Instruct-ONNX"
JUDGE_REVISION = "14007543b6dc92de88daf96a9aa85d2f95ace6ef"


@lru_cache(maxsize=1)
def load_live_models():
    root = ASSETS / "reevaluators"
    manifest = json.loads((root / "manifest.json").read_text())
    if manifest["basis_sha256"] != MODEL_SHA256:
        raise ValueError("Wrong reevaluation basis")
    models = {}
    for name in ("krr", "lightgbm"):
        item = manifest["models"][name]
        if item["file"] != name + ".json":
            raise ValueError("Invalid model path")
        raw = (root / item["file"]).read_bytes()
        if hashlib.sha256(raw).hexdigest() != item["sha256"] or len(raw) != item["bytes"]:
            raise ValueError("Reevaluation integrity failed")
        model = json.loads(raw)
        if model["basis_sha256"] != MODEL_SHA256 or model["classes"] != [0, 1]:
            raise ValueError("Wrong reevaluation labels")
        models[name] = (model, item["sha256"])
    return models


def feature_vector(text):
    output = {}; offset = 0
    for block in load_artifact()["blocks"]:
        counts = Counter(); vocabulary = block["vocabulary"]
        def add(feature, vocabulary=vocabulary, counts=counts):
            if feature in vocabulary:
                counts[vocabulary[feature]] += 1
        lower = text.lower()
        if block["analyzer"] == "word":
            words = WORD.findall(lower)
            for index, word in enumerate(words):
                add(word)
                if index:
                    add(words[index - 1] + " " + word)
        else:
            for word in lower.split():
                padded = " " + word + " "
                for n in range(3, 6):
                    position = 0; add(padded[:n])
                    while position + n < len(padded):
                        position += 1; add(padded[position:position + n])
                    if position == 0:
                        break
        values = [(i, (1 + math.log(count)) * block["idf"][i]) for i, count in counts.items()]
        norm = math.sqrt(sum(v * v for _, v in values))
        output.update((offset + i, value / norm) for i, value in values)
        offset += len(block["idf"])
    return output


def auxiliary_checks(body):
    text, _ = prepare_plain(body); vector = feature_vector(text)
    results = []
    for kind, (model, sha) in load_live_models().items():
        if kind == "krr":
            raw = sum(value * model["coefficients"][i] for i, value in vector.items())
        else:
            raw = 0
            for tree in model["trees"]:
                node = tree
                while "split_index" in node:
                    if node["decision_type"] != "<=":
                        raise ValueError("Unsupported tree convention")
                    node = node["left_child"] if vector.get(node["split_feature"], 0) <= node["threshold"] else node["right_child"]
                raw += node["leaf_value"]
        mapping = model["mapping"]
        score = sigmoid(mapping["slope"] * raw + mapping["intercept"])
        results.append({"kind": kind, "model_id": model["model_id"], "sha256": sha,
                        "raw_margin": raw, "score": score, "cutoff": model["cutoff"],
                        "threshold_score": sigmoid(mapping["slope"] * model["cutoff"] + mapping["intercept"]),
                        "alert": raw >= model["cutoff"], "valid": True})
    return results


def review_request_sha(review):
    if review is None:
        return None
    return hashlib.sha256(json.dumps(review.model_dump(mode="json", exclude_none=True),
                                     sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def validate_local_review(review, primary, body):
    if primary.model_revision != MODEL_SHA256:
        raise ValueError("Full local review requires the matching primary provider")
    prepared, _ = prepare_plain(body)
    if review.primary_alert != primary.model_alert:
        raise ValueError("Review changed the server-owned primary finding")
    judge = review.judge
    if judge.valid:
        if judge.model_id != JUDGE_ID or judge.model_revision != JUDGE_REVISION or not judge.quote or judge.quote not in prepared:
            raise ValueError("Unsupported judge identity or quote")
        if judge.audit == "supported":
            expected = "request_needs_verification" if primary.model_alert else "protective_or_routine_context"
            if judge.reason_code != expected or judge.missing_context:
                raise ValueError("Judge rubric mismatch")
        elif judge.reason_code in {"request_needs_verification", "protective_or_routine_context"}:
            raise ValueError("Unsupported judge reason")
    actual = [{"kind": "tfidf", "model_id": primary.model, "sha256": primary.model_revision,
               "raw_margin": primary.raw_margin, "score": primary.phishing_score,
               "threshold_score": primary.alert_threshold_score, "cutoff": 0,
               "alert": primary.model_alert, "valid": True}, *auxiliary_checks(body)]
    if review.reevaluators:
        if sorted(e.kind for e in review.reevaluators) != ["krr", "lightgbm", "tfidf"]:
            raise ValueError("Missing or duplicate reevaluators")
        for posted in review.reevaluators:
            expected = next(e for e in actual if e["kind"] == posted.kind)
            if posted.model_id != expected["model_id"] or posted.sha256 != expected["sha256"] or not posted.valid or posted.alert != expected["alert"]:
                raise ValueError("Reevaluation identity/decision mismatch")
            for field in ("raw_margin", "score", "threshold_score", "cutoff"):
                if not math.isclose(getattr(posted, field), expected[field], rel_tol=0, abs_tol=1e-8):
                    raise ValueError("Browser/server reevaluation mismatch")
    released = bool(review.reevaluators) and judge.valid and judge.audit == "supported" and not judge.missing_context and all(e["alert"] == primary.model_alert for e in actual)
    if (review.status == "released") != released:
        raise ValueError("Review release status is unsupported")
    return {**review.model_dump(mode="json", exclude_none=True),
            "origin": "browser_reported_LLM_audit_not_server_LLM_inference",
            "server_replayed_classifiers": actual, "server_quote_checked": judge.valid}
