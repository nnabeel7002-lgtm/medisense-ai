"""
safety.py — Safety, Guardrails & Interaction Checking Engine
Owner: Afsheen Riaz (Product & Safety Lead)

Fulfills:
 - PRD Section 9 (Clinical Safety, Guardrails & Triage Engine)
 - PRD Section 10 (Regulatory, Ethics & Liability Framework)
 - PRD Section 18 (Tab 4: Multi-Drug Interaction Checker)
 - PRD Section 19 (Deterministic Fallback & Testing Matrix TC-03, TC-04, TC-05)

CONTRACT (Strict Interface):
    classify_risk(text: str) -> "low" | "moderate" | "emergency"
    check_interaction(drug_a: str, drug_b: str) -> dict
"""

import re

# --- 1. Persistent Disclaimers & Messages -----------------------------------

DISCLAIMER_HEADER = (
    "⚠️ DISCLAIMER: Educational & Informational Tool Only. "
    "Not a substitute for professional clinical advice, diagnosis, or treatment."
)

EMERGENCY_MESSAGE = (
    "🚨 MEDICAL EMERGENCY DETECTED 🚨\n\n"
    "This query contains indicators of a potential severe medical reaction, poisoning, or emergency. "
    "Please contact emergency medical services (e.g., 911 / local emergency number) or "
    "Poison Control immediately, or proceed to the nearest emergency department.\n\n"
    "MediSense AI is an educational assistant and CANNOT manage acute medical emergencies."
)

# Deterministic Guardrail System Prompt (PRD Section 19)
SYSTEM_PROMPT = """You are a medical information assistant.
You must ONLY answer using the provided Context block.
If the requested drug or query is not explicitly present in the Context,
state exactly: "The requested information is not available in the verified dataset."
DO NOT use internal training knowledge to infer or extrapolate answers."""

# --- 2. Risk Classification Engine -------------------------------------------

EMERGENCY_KEYWORDS = [
    "overdose", "took too many", "took 20", "took 10", "took 50", "took a lot",
    "by mistake", "can't breathe", "cannot breathe", "difficulty breathing",
    "unconscious", "passed out", "chest pain", "severe allergic", "anaphylaxis",
    "swelling of face", "swelling of throat", "swelling of lips", "poisoning",
    "seizure", "convulsions", "foaming at mouth", "blue lips", "cyanosis",
    "bleeding profusely", "suicide", "self harm", "unresponsive"
]

MODERATE_KEYWORDS = [
    "feel sick", "nausea", "dizzy", "dizziness", "rash", "mild reaction",
    "not feeling well", "side effect", "headache", "vomiting", "stomach pain",
    "diarrhea", "fever", "cramps", "drowsiness", "itching"
]

def classify_risk(text: str) -> str:
    """
    Classify user query into 'low', 'moderate', or 'emergency' risk levels.
    Evaluates exact and substring matches for medical red flags.
    
    Returns:
        "emergency" | "moderate" | "low"
    """
    if not text or not text.strip():
        return "low"

    lowered = text.lower()

    # High-Risk / Emergency Trigger Gate
    for kw in EMERGENCY_KEYWORDS:
        if kw in lowered:
            return "emergency"

    # Moderate Risk Trigger
    for kw in MODERATE_KEYWORDS:
        if kw in lowered:
            return "moderate"

    return "low"


# --- 3. Multi-Drug Interaction Checker Engine ------------------------------

# Curated interaction database mapped across the 20-medicine reference set
INTERACTIONS = {
    frozenset(["ibuprofen", "aspirin"]): {
        "interacts": True,
        "severity": "moderate",
        "explanation": (
            "Combining Ibuprofen and Aspirin increases the risk of gastrointestinal "
            "ulceration and stomach bleeding. Ibuprofen may also interfere with the "
            "cardioprotective effect of low-dose Aspirin."
        )
    },
    
    frozenset(["diclofenac", "ibuprofen"]): {
        "interacts": True,
        "severity": "severe",
        "explanation": (
            "Combining multiple Non-Steroidal Anti-Inflammatory Drugs (NSAIDs) increases "
            "the risk of severe renal impairment, severe stomach ulceration, and GI bleeding."
        )
    },
    frozenset(["amlodipine", "losartan"]): {
        "interacts": True,
        "severity": "mild",
        "explanation": (
            "Amlodipine and Losartan are frequently co-prescribed for hypertension. "
            "However, combined use requires blood pressure monitoring to prevent hypotension."
        )
    }
   
    
}


def check_interaction(drug_a: str, drug_b: str) -> dict:
    """
    Look up known drug-drug interactions between two medicine names.
    
    Returns:
        dict: {
            "interacts": bool,
            "severity": "none" | "mild" | "moderate" | "severe",
            "explanation": str
        }
    """
    if not drug_a or not drug_b:
        return {
            "interacts": False,
            "severity": "none",
            "explanation": "Invalid drug inputs provided."
        }

    key = frozenset([drug_a.strip().lower(), drug_b.strip().lower()])
    result = INTERACTIONS.get(key)
    
    if result:
        return result

    return {
        "interacts": False,
        "severity": "none",
        "explanation": f"No interaction listed in the verified dataset between '{drug_a.title()}' and '{drug_b.title()}'."
    }


# --- Self-Test & Validation Output (Phase 1 Checklist) ----------------------

if __name__ == "__main__":
    print("=== Running Safety Module Sanity Checks ===")
    
    # Test TC-04 Emergency Case
    assert classify_risk("I took 20 tablets of Tylenol by mistake") == "emergency"
    assert classify_risk("My child is struggling and can't breathe") == "emergency"
    print("✅ Emergency detection tests passed (TC-04).")

    # Test TC-05 Moderate Case
    assert classify_risk("I feel dizzy and have a mild rash") == "moderate"
    print("✅ Moderate risk tests passed (TC-05).")

    # Test Low Risk Case
    assert classify_risk("What is the main use of Paracetamol?") == "low"
    print("✅ Low risk tests passed.")

    # Test Interaction Checker (Tab 4)
    res = check_interaction("Ibuprofen", "Aspirin")
    assert res["interacts"] is True
    assert res["severity"] == "moderate"
    print("✅ Interaction check tests passed (Ibuprofen + Aspirin).")

    print("\nModule safety.py is verified and ready for hand-off to Nabeeha!")
