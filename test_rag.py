"""
test_rag.py — Sanity checks for rag.py's retrieval boundary.

Confirms known medicines are found and unknown/similar-sounding
medicines are correctly rejected, not fuzzy-matched to the wrong drug.

Run with:
    python test_rag.py
"""

from rag import retrieve_info


def check(query, should_be_found):
    result = retrieve_info(query)
    found = bool(result["chunks"])
    status = "PASS" if found == should_be_found else "FAIL"
    print(f"[{status}] '{query}' -> found={found} (expected={should_be_found})")
    if found:
        print("    ->", result["chunks"][0][:100], "...")


if __name__ == "__main__":
    print("=== RAG Retrieval Boundary Tests ===\n")

    check("Metformin", True)          # in the 20-medicine set — must be found
    check("Diclofenac", True)         # in the 20-medicine set — must be found
    check("Aceclofenac", False)       # similar name to Diclofenac, NOT in the set
    check("Mecobalamin", False)       # real drug, NOT in the set at all

    print("\nIf any FAIL, adjust MAX_DISTANCE in rag.py and re-run.")
