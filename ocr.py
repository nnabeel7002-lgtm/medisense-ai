"""
ocr.py — Image-based medicine identification (Owner: Faiza)

CONTRACT (do not change without telling the whole team):
    identify_from_image(image) -> {
        "medicine_name": str | None,
        "confidence": float   # 0.0 - 1.0
    }

CURRENT STATE: uses the OCR.space cloud API for text extraction (works on
Pydroid 3 / Android — no local Tesseract binary needed), then fuzzy-matches
extracted text against the known medicine list.

SETUP:
    pip install requests
    Get a free API key at https://ocr.space/ocrapi (free tier, no card needed)
    Replace OCR_SPACE_API_KEY below with your own key before demo day —
    the shared "helloworld" test key is rate-limited across everyone using it.

TODO (Faiza):
    1. Test against real, imperfect photos (blurry, angled, poor lighting) —
       not just clean screenshots of text. TC-06 depends on this being honest
       about low confidence, not falsely confident.
    2. Tune the confidence threshold below (LOW_CONFIDENCE_THRESHOLD) based on
       real test results.
    3. This requires internet access at OCR time — don't test in airplane mode.
"""

import csv
import os
from difflib import get_close_matches

import requests

CSV_PATH = os.path.join(os.path.dirname(__file__), "data", "medicines.csv")
LOW_CONFIDENCE_THRESHOLD = 0.5

OCR_SPACE_API_KEY = "K87159261788957"  


def _load_medicine_names():
    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        return [row["medicine_name"] for row in csv.DictReader(f)]


_MEDICINE_NAMES = _load_medicine_names()


def _extract_text(image) -> str:
    """
    Run OCR via the OCR.space cloud API. `image` can be a file path (str)
    or an already-open file-like object (e.g. Streamlit's uploaded_file).
    """
    if isinstance(image, str):
        file_obj = open(image, "rb")
        should_close = True
    else:
        file_obj = image
        should_close = False

    try:
        response = requests.post(
            "https://api.ocr.space/parse/image",
            files={"filename": file_obj},
            data={"apikey": OCR_SPACE_API_KEY, "language": "eng"},
            timeout=15,
        )
        result = response.json()
        return result["ParsedResults"][0]["ParsedText"]
    except (requests.RequestException, KeyError, IndexError, ValueError):
        return ""
    finally:
        if should_close:
            file_obj.close()


def identify_from_image(image) -> dict:
    """
    Extract text from an uploaded image and match it against the known
    medicine list. Returns None/0.0 confidence if nothing usable is found —
    NEVER guess a name just to return something.
    """
    raw_text = _extract_text(image)

    if not raw_text.strip():
        return {"medicine_name": None, "confidence": 0.0}

    words = raw_text.split()
    best_match = None
    best_score = 0.0

    for word in words:
        matches = get_close_matches(word.lower(), [n.lower() for n in _MEDICINE_NAMES], n=1, cutoff=0.6)
        if matches:
            # crude confidence: exact-ish match length ratio
            score = len(matches[0]) / max(len(word), 1)
            score = min(score, 1.0)
            if score > best_score:
                best_score = score
                best_match = matches[0]

    if best_match is None:
        return {"medicine_name": None, "confidence": 0.0}

    for name in _MEDICINE_NAMES:
        if name.lower() == best_match:
            return {"medicine_name": name, "confidence": round(best_score, 2)}

    return {"medicine_name": None, "confidence": 0.0}


def is_low_confidence(result: dict) -> bool:
    """Helper for the UI layer to decide whether to show the uncertainty flag."""
    return result["confidence"] < LOW_CONFIDENCE_THRESHOLD or result["medicine_name"] is None


if __name__ == "__main__":
    # quick manual test — replace with a real image path to test locally
    print(identify_from_image("sample_package.jpeg"))
    print("Loaded", len(_MEDICINE_NAMES), "reference medicine names for matching.")
