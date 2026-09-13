"""
build_index.py — Owner: Rameen

WHAT THIS DOES:
Reads data/enriched_medicines.json (from fetch_openfda.py — or falls back to
data/medicines.csv alone if that file doesn't exist yet), splits each
medicine into small labeled chunks (uses / side effects / warnings /
contraindications), embeds them, and saves everything to a ChromaDB folder
on disk (./chroma_db). This is the ONE-TIME build step.

At demo time, rag.py just LOADS ./chroma_db — it never rebuilds live.

HOW TO RUN:
    python build_index.py

Re-run this any time your source data changes.
"""

import csv
import json
import os
import shutil

import chromadb

BASE_DIR = os.path.dirname(__file__)
CSV_PATH = os.path.join(BASE_DIR, "data", "medicines.csv")
ENRICHED_PATH = os.path.join(BASE_DIR, "data", "enriched_medicines.json")
CHROMA_PATH = os.path.join(BASE_DIR, "chroma_db")
COLLECTION_NAME = "medicines"


def _load_source_data():
    if os.path.exists(ENRICHED_PATH):
        with open(ENRICHED_PATH, encoding="utf-8") as f:
            return json.load(f)
    # fallback: just the seed CSV, no OpenFDA extras yet
    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _chunk_medicine(med: dict) -> list[dict]:
    """
    Turn one medicine's record into several small, labeled chunks.
    Each chunk = one field, so retrieval can pull the ONE relevant piece
    instead of dumping the whole record for every query.
    """
    name = med["medicine_name"]
    chunks = []

    def add(field_label, text):
        text = (text or "").strip()
        if text:
            chunks.append({
                "text": f"{name} — {field_label}: {text}",
                "medicine_name": name,
                "field": field_label,
                "source": med.get("source_reference", "MedlinePlus / DailyMed / FDA"),
            })

    add("Drug type", med.get("drug_type"))
    add("Main use", med.get("main_use") or med.get("openfda_purpose"))
    add("Common forms", med.get("common_forms"))
    add("Safety note", med.get("safety_note"))
    add("Warnings", med.get("openfda_warnings"))
    add("Contraindications", med.get("openfda_contraindications"))
    add("Side effects", med.get("openfda_side_effects"))

    return chunks


def build_index():
    source_data = _load_source_data()

    all_chunks = []
    for med in source_data:
        all_chunks.extend(_chunk_medicine(med))

    print(f"Built {len(all_chunks)} chunks from {len(source_data)} medicines.")

    # Fresh build every time — wipe any old index first
    if os.path.exists(CHROMA_PATH):
        shutil.rmtree(CHROMA_PATH)

    client = chromadb.PersistentClient(path=CHROMA_PATH)
    # default embedding function = all-MiniLM-L6-v2, runs locally, no API key needed
    collection = client.create_collection(name=COLLECTION_NAME)

    collection.add(
        ids=[str(i) for i in range(len(all_chunks))],
        documents=[c["text"] for c in all_chunks],
        metadatas=[
            {"medicine_name": c["medicine_name"], "field": c["field"], "source": c["source"]}
            for c in all_chunks
        ],
    )

    print(f"Saved persistent ChromaDB store to: {CHROMA_PATH}")
    print("This folder is what gets committed/shipped — no live rebuilding at demo time.")


if __name__ == "__main__":
    build_index()
