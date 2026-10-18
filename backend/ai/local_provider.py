"""Optional CPU DistilBERT adapter. Normal API startup never downloads weights."""

import json
import re
from pathlib import Path
from threading import Lock

from backend.ai.schemas import AIAnalysisResult, EvidenceItem

MODEL_ID = "dima806/phishing-email-detection"
MODEL_REVISION = "310a5602280486e01dd60e37230980cfcc327b41"
MODEL_LICENSE = "apache-2.0"
MODEL_SOURCE = f"https://huggingface.co/{MODEL_ID}/tree/{MODEL_REVISION}"
DEFAULT_CACHE = Path(__file__).resolve().parents[2] / "models"
# Exact metadata from this revision. SAVE EMAIL is the author's spelling.
EXPECTED_LABELS = {0: "SAVE EMAIL", 1: "PHISHING EMAIL"}
MAX_TOKENS = 512
STRIDE = 64


def rule_indicators(text: str) -> tuple[list[str], list[EvidenceItem]]:
    """Text rules explain observed indicators, not neural attention or causality."""
    patterns = (
        (r"\b(?:password|credentials|one.time (?:code|password)|otp)\b", "Sensitive information"),
        (r"\b(?:urgent|immediately|within \d+ hours?|suspend\w*|closed today)\b", "Urgency"),
        (r"\b(?:wire transfer|gift cards?|bank details|payment details)\b", "Payment request"),
        (r"https?://[^\s<>\"]+", "Link present"),
    )
    tactics, evidence = [], []
    for pattern, name in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            tactics.append(f"Rule indicator: {name.lower()}")
            evidence.append(EvidenceItem(
                text=match.group(0),
                reason=f"{name} appears in the text; this rule alone does not establish phishing.",
            ))
    return tactics, evidence


class LocalProvider:
    def __init__(self, *, cache_dir: Path = DEFAULT_CACHE) -> None:
        self.cache_dir = Path(cache_dir)
        self.model = None
        self.tokenizer = None
        self._load_lock = Lock()

    def _load(self) -> None:
        with self._load_lock:
            if self.model is not None:
                return
            try:
                import torch
                from transformers import (
                    AutoModelForSequenceClassification,
                    AutoTokenizer,
                )

                options = {
                    "revision": MODEL_REVISION, "cache_dir": str(self.cache_dir),
                    "local_files_only": True, "trust_remote_code": False,
                }
                # The repository supplies a cased vocabulary without tokenizer_config.json.
                tokenizer = AutoTokenizer.from_pretrained(
                    MODEL_ID, do_lower_case=False, **options,
                )
                model = AutoModelForSequenceClassification.from_pretrained(
                    MODEL_ID, use_safetensors=True, **options,
                )
                if model.config.model_type != "distilbert" or model.config.id2label != EXPECTED_LABELS:
                    raise RuntimeError("The local checkpoint has unexpected architecture or labels.")
                torch.set_num_threads(4)
                model.to("cpu").eval()
                self.tokenizer, self.model = tokenizer, model
            except (ImportError, OSError) as exc:
                raise RuntimeError(
                    "Local AI is unavailable. Install backend/requirements-ai.txt and run "
                    "python scripts/ai_smoke.py --mode local --download-model."
                ) from exc

    def analyze(self, email_text: str) -> AIAnalysisResult:
        self._load()
        import torch

        email = json.loads(email_text)
        # Plain subject/body follows the checkpoint's input domain; sender is unverified metadata.
        text = "\n\n".join(v for v in (email.get("subject"), email["body"]) if v)
        inputs = self.tokenizer(
            text, return_tensors="pt", padding=True, truncation=True,
            max_length=MAX_TOKENS, stride=STRIDE, return_overflowing_tokens=True,
        )
        inputs.pop("overflow_to_sample_mapping", None)
        count = inputs["input_ids"].shape[0]
        scores = []
        with torch.inference_mode():
            for start in range(0, count, 4):
                batch = {key: value[start:start + 4] for key, value in inputs.items()}
                probabilities = torch.softmax(self.model(**batch).logits, dim=-1)
                scores.extend(probabilities[:, 1].tolist())
        # Analyze every overlapping window, including a malicious request near the end.
        phishing_score = max(scores)
        is_phishing = phishing_score >= 0.5
        tactics, evidence = rule_indicators(text)
        return AIAnalysisResult(
            classification="phishing" if is_phishing else "legitimate",
            confidence=phishing_score if is_phishing else 1 - phishing_score,
            tactics=tactics, evidence=evidence,
            recommendations=[
                "Verify sensitive requests through a separately opened, trusted channel.",
                "This text assessment does not authenticate the sender or scan links and attachments.",
            ],
            model=MODEL_ID, model_revision=MODEL_REVISION, explanation_source="rules",
            input_truncated=False, windows_processed=count,
        )


def download_model(cache_dir: Path = DEFAULT_CACHE) -> str:
    """Explicit preparation step, separate from production inference and ordinary CI."""
    from huggingface_hub import snapshot_download

    return snapshot_download(
        MODEL_ID, revision=MODEL_REVISION, cache_dir=str(cache_dir),
        allow_patterns=["config.json", "vocab.txt", "model.safetensors", "README.md"],
    )
