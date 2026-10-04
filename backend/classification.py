"""Closed-set photo classification using the OpenAI Responses API."""

from __future__ import annotations

import base64
import json
import os


class ClassificationError(RuntimeError):
    """A safe, user-displayable classification failure."""


SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "category": {
            "type": "string",
            "enum": ["street_light", "illegal_dumping", "electronic_waste", "other"],
        },
        "label": {"type": "string"},
        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
        "visible_evidence": {"type": "string"},
        "needs_more_information": {"type": "boolean"},
    },
    "required": [
        "category",
        "label",
        "confidence",
        "visible_evidence",
        "needs_more_information",
    ],
}


def classify_image(image: bytes, media_type: str, description: str = "") -> dict:
    """Return structured classification; never choose a service or authority."""
    if not os.environ.get("OPENAI_API_KEY"):
        raise ClassificationError(
            "OPENAI_API_KEY is not configured. Add it to the project .env file and restart the backend."
        )

    try:
        from openai import OpenAI, OpenAIError
    except ImportError:
        raise ClassificationError("The OpenAI SDK is missing. Install backend/requirements.txt and restart.") from None

    try:
        client = OpenAI()
        data_url = f"data:{media_type};base64,{base64.b64encode(image).decode('ascii')}"
        user_content = [
            {
                "type": "input_text",
                "text": (
                    "Classify the main civic issue visible in this photo. Choose exactly one category: "
                    "street_light for a damaged or non-working public streetlight; illegal_dumping for "
                    "rubbish abandoned in a public place; electronic_waste for discarded electrical "
                    "or electronic equipment; other if none clearly fits. Use only visible evidence. "
                    "Do not infer location, authority, cause, or a reporting service. If uncertain, use other "
                    "and set needs_more_information to true."
                    + (f" Citizen note: {description.strip()}" if description.strip() else "")
                ),
            },
            {"type": "input_image", "image_url": data_url, "detail": "auto"},
        ]
        response = client.responses.create(
            model=os.environ.get("OPENAI_MODEL", "gpt-6-luna"),
            input=[{"role": "user", "content": user_content}],
            text={
                "format": {
                    "type": "json_schema",
                    "name": "issue_classification",
                    "strict": True,
                    "schema": SCHEMA,
                }
            },
            max_output_tokens=180,
        )
        if not response.output_text:
            raise ClassificationError("The model did not return a classification. Try another photo.")
        result = json.loads(response.output_text)
        if result.get("category") not in {"street_light", "illegal_dumping", "electronic_waste", "other"}:
            raise ClassificationError("The model returned an unsupported issue category.")
        return result
    except ClassificationError:
        raise
    except OpenAIError:
        # Keep credentials and provider request details out of responses and logs.
        raise ClassificationError("Image analysis failed. Check API billing and key access, then try again.") from None
    except (ValueError, TypeError):
        raise ClassificationError("Image analysis returned an unreadable result. Try again.") from None
    except Exception:
        raise ClassificationError("Image analysis is temporarily unavailable. Try again shortly.") from None
