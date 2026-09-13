"""
rag.py — Data & RAG Engine (Owner: Rameen)

CONTRACT (do not change without telling the whole team):
    retrieve_info(query: str) -> {
        "chunks": [str, ...],      # the actual retrieved text pieces
        "sources": [str, ...],     # matching source reference per chunk
    }

CURRENT STATE: loads the pre-built ChromaDB store from ./chroma_db
(built once by build_index.py — this file NEVER rebuilds the index itself,
it only reads it). If a query matches nothing meaningful, it returns empty
lists — Afsheen's safety.py / the fallback prompt handles what happens next,
not this file.
"""

import os
import chromadb

BASE_DIR = os.path.dirname(__file__)
CHROMA_PATH = os.path.join(BASE_DIR, "chroma_db")
COLLECTION_NAME = "medicines"

# how many chunks to pull per query — tune this if answers feel thin or noisy
N_RESULTS = 4
# below this distance, a match is too weak to trust — tune based on real testing
MAX_DISTANCE = 1.5

_client = None
_collection = None


def _get_collection():
    global _client, _collection
    if _collection is None:
        if not os.path.exists(CHROMA_PATH):
            # Self-healing: chroma_db is never pushed to GitHub (too large),
            # so on a fresh clone or a fresh Streamlit Cloud deploy it won't
            # exist yet. Build it once here instead of crashing — this takes
            # ~1-2 minutes the FIRST time only (downloads the embedding model).
            print("No chroma_db found — building it now (first run only)...")
            from build_index import build_index
            build_index()
        _client = chromadb.PersistentClient(path=CHROMA_PATH)
        _collection = _client.get_collection(name=COLLECTION_NAME)
    return _collection


def retrieve_info(query: str) -> dict:
    """
    Retrieve the most relevant chunks for a user query.
    Returns {"chunks": [], "sources": []} if nothing good enough is found —
    this is what feeds safety.py's "Record Not Found" fallback logic.
    """
    if not query or not query.strip():
        return {"chunks": [], "sources": []}

    collection = _get_collection()
    results = collection.query(query_texts=[query], n_results=N_RESULTS)

    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    chunks, sources = [], []
    for doc, meta, dist in zip(documents, metadatas, distances):
        if dist is not None and dist > MAX_DISTANCE:
            continue  # too weak a match — don't hand it to the LLM as "real" info
        chunks.append(doc)
        sources.append(meta.get("source", "MedlinePlus / DailyMed / FDA"))

    return {"chunks": chunks, "sources": sources}


if __name__ == "__main__":
    # quick manual test — run this after build_index.py to sanity check
    for test_query in ["What is Paracetamol used for?", "Ibuprofen side effects", "Amoxicillin allergy warning"]:
        result = retrieve_info(test_query)
        print("\nQuery:", test_query)
        for c, s in zip(result["chunks"], result["sources"]):
            print(" -", c, f"[{s}]")
