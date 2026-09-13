import csv
import os
from difflib import get_close_matches

CSV_PATH = os.path.join(
    os.path.dirname(__file__),
    "data",
    "medicines.csv"
)

SOURCES = [
    "https://medlineplus.gov/",
    "https://dailymed.nlm.nih.gov/dailymed/"
]


def _load_medicines():
    medicines = []

    if not os.path.exists(CSV_PATH):
        raise FileNotFoundError(
            f"Medicine dataset not found at: {CSV_PATH}"
        )

    with open(
        CSV_PATH,
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as f:
        reader = csv.DictReader(f)

        for row in reader:
            medicines.append({
                "medicine_name": row.get("medicine_name", "").strip(),
                "drug_type": row.get("drug_type", "").strip(),
                "main_use": row.get("main_use", "").strip(),
                "common_forms": row.get("common_forms", "").strip(),
                "safety_note": row.get("safety_note", "").strip(),
                "source_reference": row.get(
                    "source_reference", ""
                ).strip()
            })

    return medicines


# Load medicines and expose them for app.py
_MEDICINES = _load_medicines()

_NAMES = [
    medicine["medicine_name"]
    for medicine in _MEDICINES
    if medicine["medicine_name"]
]


def _fuzzy_lookup(query):
    if not query:
        return None

    query = str(query).strip()
    query_lower = query.lower()

    # Exact medicine name inside the user's question
    for medicine in _MEDICINES:
        name = medicine["medicine_name"].strip()

        if name and name.lower() in query_lower:
            return medicine

    # Fuzzy matching
    lower_names = [name.lower() for name in _NAMES]

    matches = get_close_matches(
        query_lower,
        lower_names,
        n=1,
        cutoff=0.4
    )

    if not matches:
        return None

    matched_name = matches[0]

    for medicine in _MEDICINES:
        if medicine["medicine_name"].lower() == matched_name:
            return medicine

    return None


def retrieve_info(query):
    medicine = _fuzzy_lookup(query)

    if not medicine:
        return {
            "chunks": [],
            "sources": []
        }

    chunk = (
        f"Medicine: {medicine['medicine_name']}\n"
        f"Drug Type: {medicine['drug_type']}\n"
        f"Main Use: {medicine['main_use']}\n"
        f"Common Forms: {medicine['common_forms']}\n"
        f"Safety Note: {medicine['safety_note']}"
    )

    return {
        "chunks": [chunk],
        "sources": SOURCES
    }
