"""Local zero-shot image classification with Hugging Face CLIP."""

from __future__ import annotations

import io
import os
from pathlib import Path
from threading import Lock

from PIL import Image, UnidentifiedImageError


class ClassificationError(RuntimeError):
    """A safe, user-displayable classification failure."""


MODEL_ID = os.environ.get("HF_IMAGE_MODEL", "openai/clip-vit-base-patch32")
CATEGORY_PROMPTS = {
    "street_light": "a broken street light that is not working on a public street at night",
    "illegal_dumping": "a pile of illegally dumped rubbish and trash bags on a roadside",
    "electronic_waste": "a broken laptop computer with a cracked screen that has been thrown away",
    "other": "a normal photo of a landscape, pets, or food, with no damaged infrastructure, litter, or electronic waste",
}
CATEGORY_LABELS = {
    "street_light": "Possible damaged or non-working streetlight",
    "illegal_dumping": "Possible rubbish dumped in a public place",
    "electronic_waste": "Possible discarded electrical or electronic equipment",
    "other": "Other issue or unclear photo",
}

_MODEL = None
_PROCESSOR = None
_MODEL_LOCK = Lock()
_INFERENCE_LOCK = Lock()


def _load_model():
    global _MODEL, _PROCESSOR
    if _MODEL is None or _PROCESSOR is None:
        with _MODEL_LOCK:
            if _MODEL is None or _PROCESSOR is None:
                try:
                    from huggingface_hub.constants import HF_HUB_CACHE
                    from transformers import CLIPConfig, CLIPModel, CLIPProcessor

                    cache_name = f"models--{MODEL_ID.replace('/', '--')}"
                    snapshots = Path(HF_HUB_CACHE) / cache_name / "snapshots"
                    cached_weights = sorted(snapshots.glob("*/model.safetensors"))
                    cached_processors = sorted(snapshots.glob("*/preprocessor_config.json"))

                    if cached_processors:
                        processor_path = max(cached_processors, key=lambda path: path.stat().st_mtime).parent
                        _PROCESSOR = CLIPProcessor.from_pretrained(
                            str(processor_path), local_files_only=True
                        )
                    else:
                        processor_path = None
                        _PROCESSOR = CLIPProcessor.from_pretrained(MODEL_ID)

                    # Transformers 4.x may query the Hub on each cold start to
                    # discover its converted safetensors PR, even after caching
                    # the weights. Load an already-cached checkpoint by path so
                    # subsequent startups work without network access.
                    if cached_weights:
                        weight_path = max(cached_weights, key=lambda path: path.stat().st_mtime)
                        config_source = str(processor_path) if processor_path else MODEL_ID
                        config = CLIPConfig.from_pretrained(config_source, local_files_only=True)
                        _MODEL = CLIPModel.from_pretrained(
                            str(weight_path.parent),
                            config=config,
                            use_safetensors=True,
                            local_files_only=True,
                        )
                    else:
                        _MODEL = CLIPModel.from_pretrained(MODEL_ID, use_safetensors=True)
                    _MODEL.eval()
                except Exception:
                    _MODEL = None
                    _PROCESSOR = None
                    raise
    return _MODEL, _PROCESSOR


def classify_image(image: bytes, media_type: str, description: str = "") -> dict:
    """Find the closest supported image-text match using the local CLIP model."""
    try:
        with Image.open(io.BytesIO(image)) as opened_image:
            photo = opened_image.convert("RGB")
    except (UnidentifiedImageError, OSError):
        raise ClassificationError("The selected image could not be decoded. Choose another photo.") from None

    try:
        from torch import inference_mode
        model, processor = _load_model()
    except Exception:
        raise ClassificationError(
            f"The local Hugging Face model '{MODEL_ID}' could not be loaded. Check the internet connection for its first download, then restart the backend."
        ) from None

    try:
        note = " ".join(description.split())[:200]
        def score_prompts(prompts: list[str]) -> list[float]:
            inputs = dict(processor.tokenizer(prompts, return_tensors="pt", padding=True))
            inputs.update(processor.image_processor(photo, return_tensors="pt"))
            with _INFERENCE_LOCK, inference_mode():
                return model(**inputs).logits_per_image.softmax(dim=1)[0].tolist()

        category_keys = list(CATEGORY_PROMPTS)
        probabilities = score_prompts(list(CATEGORY_PROMPTS.values()))
        best_index = max(range(len(probabilities)), key=probabilities.__getitem__)
        ranked = sorted(probabilities, reverse=True)
        clear_match = probabilities[best_index] >= 0.35 and probabilities[best_index] - ranked[1] >= 0.08

        # Let notes help when the photo alone is ambiguous, but do not allow a
        # short or conflicting note to overturn a clear visual match.
        if note and (not clear_match or category_keys[best_index] == "other"):
            noted_scores = score_prompts([
                f"{prompt}. The reporter notes: {note}"
                for prompt in CATEGORY_PROMPTS.values()
            ])
            noted_best = max(range(len(noted_scores)), key=noted_scores.__getitem__)
            noted_ranked = sorted(noted_scores, reverse=True)
            if noted_best != category_keys.index("other") and noted_scores[noted_best] >= 0.35 and noted_scores[noted_best] - noted_ranked[1] >= 0.08:
                probabilities = noted_scores
    except Exception:
        raise ClassificationError("Local image analysis failed. Check the image and restart the backend.") from None

    best_index = max(range(len(probabilities)), key=probabilities.__getitem__)
    ranked = sorted(probabilities, reverse=True)
    top_score = float(probabilities[best_index])
    clear_match = top_score >= 0.35 and (len(ranked) == 1 or top_score - ranked[1] >= 0.08)
    category = category_keys[best_index] if clear_match else "other"
    matched_label = CATEGORY_LABELS[category_keys[best_index]]
    return {
        "category": category,
        "label": CATEGORY_LABELS[category],
        "confidence": top_score,
        "visible_evidence": f"Best local image-text match: {matched_label.lower()} (relative score {top_score:.2f}).",
        "needs_more_information": not clear_match or category == "other",
    }
