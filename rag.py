import csv
import os
from difflib import get_close_matches

# Path to the medicine dataset
CSV_PATH = os.path.join(
    os.path.dirname(__file__),
    "data",
    "medicines.csv"
)

# Trusted reference sources
SOURCES = [
    "https://medlineplus.gov/",
    "https://dailymed.nlm.nih.gov/dailymed/"
]


def _load_medicines():
    """Load medicine information from medicines.csv."""
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
                "medicine_name": row.get(
                    "medicine_name", ""
                ).strip(),

                "drug_type": row.get(
                    "drug_type", ""
                ).strip(),

                "main_use": row.get(
                    "main_use", ""
                ).strip(),

                "common_forms": row.get(
                    "common_forms", ""
                ).strip(),

                "safety_note": row.get(
                    "safety_note", ""
                ).strip(),

                "source_reference": row.get(
                    "source_reference", ""
                ).strip()
            })

    return medicines


# Load the medicine dataset
_MEDICINES = _load_medicines()


# List of medicine names
_NAMES = [
    medicine["medicine_name"]
    for medicine in _MEDICINES
    if medicine.get("medicine_name")
]


def get_medicine_names():
    """Return all available medicine names."""
    return [
        medicine["medicine_name"]
        for medicine in _MEDICINES
        if medicine.get("medicine_name")
    ]


def _fuzzy_lookup(query):
    """
    Find a medicine from the user's query.

    Supports:
    - Exact medicine names
    - Medicine names inside questions
    - Minor spelling mistakes
    """

    if not query:
        return None

    query = str(query).strip()
    query_lower = query.lower()

    # First: check whether a medicine name
    # appears directly inside the query.
    for medicine in _MEDICINES:
        name = medicine["medicine_name"].strip()

        if name and name.lower() in query_lower:
            return medicine

    # Second: fuzzy matching for spelling mistakes.
    lower_names = [
        name.lower()
        for name in _NAMES
    ]

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
    """
    Retrieve basic medicine information.

    Returns:
        {
            "chunks": [...],
            "sources": [...]
        }
    """

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
