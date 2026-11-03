"""Server-owned replay of the frozen browser classifier for explicit saved reports.

No training, downloaded model, cloud inference or database access. The body alone
is scored, matching highlighted-text inference. Subject/sender are not evidence
of authentication. Browser explanations are richer; saved evidence below contains
only exact word-feature quotes verified against the original body.
"""

import hashlib
import json
import math
import re
from collections import Counter
from functools import lru_cache
from pathlib import Path

from backend.ai.schemas import AIAnalysisResult, EvidenceItem

ASSETS = Path(__file__).resolve().parents[2] / "extension" / "ai"
MODEL_SHA256 = "a2f13c256dd46c3267263f8de8f4f822206c5b0ceda96658713e2523a7f9559c"
SLOPE = 1.6158795082744162
INTERCEPT = 2.0617153419475205
WORD = re.compile(r"\w{2,}")
HTML = re.compile(r"<(?:html|body|div|p|a|table|span|br|head|style|script|h[1-6]|img)\b", re.IGNORECASE)


@lru_cache(maxsize=1)
def load_artifact():
    raw = (ASSETS / "tfidf_v12a.json").read_bytes()
    if hashlib.sha256(raw).hexdigest() != MODEL_SHA256:
        raise RuntimeError("TF-IDF artifact integrity check failed")
    contract = json.loads((ASSETS / "contract.json").read_text(encoding="utf-8"))
    if (contract["model_sha256"] != MODEL_SHA256 or contract["alert_mode"] != "raw_margin"
            or contract["alert_threshold"] != 0 or contract["mapping"] != {
                "kind": "margin_sigmoid", "slope": SLOPE, "intercept": INTERCEPT}):
        raise RuntimeError("TF-IDF decision contract integrity check failed")
    return json.loads(raw)


def prepare_plain(text: str) -> tuple[str, bool]:
    # JS public interface bounds UTF-16 code units, then truncates Unicode points.
    if not isinstance(text, str) or len(text.encode("utf-16-le")) // 2 > 30_000 or HTML.search(text):
        raise RuntimeError("Provide visible plain text of at most 30000 characters")
    cleaned = re.sub(r"\b[A-Z0-9._%+\-]+@([A-Z0-9.\-]+\.[A-Z]{2,})\b", r"[EMAIL]@\1",
                     text, flags=re.IGNORECASE | re.ASCII)
    cleaned = re.sub(r"(?<![\w/])(?:\+?\d[ ()\-.]*){9,15}(?!\w)", "[PHONE]", cleaned)
    cleaned = re.sub(r"(?<!\w)\d{6,}(?!\w)", "[NUMBER]", cleaned)
    cleaned = " ".join(cleaned.split())
    truncated = len(cleaned) > 2300
    return (cleaned[:2000] + cleaned[-300:] if truncated else cleaned), truncated


def sigmoid(value: float) -> float:
    if value >= 0:
        return 1 / (1 + math.exp(-value))
    exp_value = math.exp(value)
    return exp_value / (1 + exp_value)


def score_text(body: str, *, prepared: bool = False) -> dict:
    # Private parity fixtures already contain benchmark-prepared text. Production
    # callers always use the default and prepare visible input exactly once.
    text, truncated = (body, False) if prepared else prepare_plain(body)
    if not text:
        raise RuntimeError("No usable selected text")
    artifact = load_artifact()
    margin = artifact["intercept"]
    parts = []
    nonzero = 0
    lower = text.lower()
    for block in artifact["blocks"]:
        vocab = block["vocabulary"]
        counts = Counter()

        def add(feature, vocab=vocab, counts=counts):
            if feature in vocab:
                counts[feature] += 1

        if block["analyzer"] == "word":
            words = WORD.findall(lower)
            for index, word in enumerate(words):
                add(word)
                if index:
                    add(words[index - 1] + " " + word)
        elif block["analyzer"] == "char_wb":
            for word in lower.split():
                padded = " " + word + " "
                for n in range(block["ngram_range"][0], block["ngram_range"][1] + 1):
                    offset = 0
                    add(padded[:n])
                    while offset + n < len(padded):
                        offset += 1
                        add(padded[offset:offset + n])
                    if offset == 0:
                        break
        else:
            raise RuntimeError("Unsupported model analyzer")
        values = [(feature, (1 + math.log(count)) * block["idf"][vocab[feature]])
                  for feature, count in counts.items()]
        nonzero += len(values)
        norm = math.sqrt(sum(value * value for _, value in values))
        for feature, value in values:
            contribution = value / norm * block["coefficient"][vocab[feature]]
            margin += contribution
            if block["analyzer"] == "word":
                parts.append((feature, contribution))
    if not math.isfinite(margin) or not nonzero:
        raise RuntimeError("No usable model features")
    score = sigmoid(SLOPE * margin + INTERCEPT)
    return {"raw_margin": margin, "score": score, "alert": margin >= 0,
            "threshold_score": sigmoid(INTERCEPT), "text": text,
            "input_truncated": truncated, "word_parts": parts}


class TfidfProvider:
    def __init__(self):
        try:
            load_artifact()
        except (OSError, ValueError, KeyError) as exc:
            raise RuntimeError("TF-IDF artifact unavailable") from exc

    def analyze(self, email_text: str) -> AIAnalysisResult:
        body = json.loads(email_text)["body"]
        result = score_text(body)
        text = result["text"]
        words = list(WORD.finditer(text.lower()))
        evidence = []
        for feature, contribution in sorted(result["word_parts"], key=lambda p: -abs(p[1])):
            for index, word in enumerate(words):
                start, end = None, None
                if word[0] == feature:
                    start, end = word.span()
                elif index and words[index - 1][0] + " " + word[0] == feature:
                    start, end = words[index - 1].start(), word.end()
                if start is not None:
                    quote = text[start:end]
                    # Unicode lowercase expansion can shift indices: never invent evidence.
                    if quote in body and " ".join(quote.lower().split()) == feature:
                        direction = "toward" if contribution >= 0 else "away from"
                        evidence.append(EvidenceItem(text=quote, reason=(
                            f"This learned word feature shifts the linear model {direction} phishing "
                            f"(margin contribution {contribution:+.4f}). It is a partial statistical "
                            "association, not proof of deception or authenticity.")))
                    break
            if len(evidence) == 3:
                break
        assessment = ("The classifier flags this text for review." if result["alert"] else
                      "The text is below the alert threshold. This does not establish authenticity.")
        return AIAnalysisResult(
            classification="phishing" if result["alert"] else "legitimate",
            confidence=None, model="word_plus_char_wb_C1p0", model_revision=MODEL_SHA256,
            explanation_source="rules", input_truncated=result["input_truncated"],
            windows_processed=1, tactics=[assessment], evidence=evidence,
            recommendations=[
                "Verify unexpected sensitive requests through a website or contact method you already know.",
                "Do not share passwords, security codes or payment details in response to an unverified message.",
                "Text screening cannot authenticate the sender, unseen link targets or attachments."],
            phishing_score=result["score"], raw_margin=result["raw_margin"],
            alert_threshold_score=result["threshold_score"], model_alert=result["alert"],
            assessment=assessment,
        )
