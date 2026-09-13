"""
app.py — Main Streamlit application (Owner: Nabeeha)

This is YOUR file only — nobody else should edit this, to avoid merge conflicts.
It imports the stub modules and wires them into the UI. As Rameen/Afsheen/Faiza
upgrade their internals, you change NOTHING here — the function contracts stay
the same.

Run locally with:
    streamlit run app.py
"""

import streamlit as st
import rag
import safety
import ocr
from dotenv import load_dotenv
load_dotenv()

st.set_page_config(page_title="MediSense AI", layout="wide")

# --- Persistent Safety Header (always visible, every tab) --------------
st.warning(
    "⚠ DISCLAIMER: Educational & Informational Tool Only. "
    "Not a Substitute for Clinical Advice."
)

st.title("MediSense AI")

tab1, tab2, tab3, tab4 = st.tabs(
    ["🔍 Search & Info Card", "📷 Identify by Image", "💬 Chat Assistant", "⚠️ Interaction Checker"]
)

# =========================================================================
# TAB 1 — Medicine Name Search
# =========================================================================
with tab1:
    st.subheader("Search for a medicine by name")
    query = st.text_input("Enter a medicine name", key="search_query")

    if query:
        result = rag.retrieve_info(query)
        if not result["chunks"]:
            st.error("The requested information is not available in the verified dataset.")
        else:
            for chunk in result["chunks"]:
                st.info(chunk)
            st.caption("Sources: " + ", ".join(name for name, _ in result["sources"]))

# =========================================================================
# TAB 2 — Identify by Image
# =========================================================================
with tab2:
    st.subheader("Upload a photo of medicine packaging")
    uploaded_file = st.file_uploader("Choose an image", type=["jpg", "jpeg", "png"])

    if uploaded_file is not None:
        st.image(uploaded_file, width=250)
        result = ocr.identify_from_image(uploaded_file)

        if ocr.is_low_confidence(result):
            st.warning(
                "Identification is uncertain. Please verify using the physical "
                "packaging, a pharmacist, or try the manual Search tab instead."
            )
        else:
            st.success(f"Identified: **{result['medicine_name']}** "
                       f"(confidence: {result['confidence']:.0%})")
            info = rag.retrieve_info(result["medicine_name"])
            for chunk in info["chunks"]:
                st.info(chunk)

# =========================================================================
# TAB 3 — Grounded Chat Assistant
# =========================================================================
with tab3:
    st.subheader("Ask a question about a medicine")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    user_input = st.chat_input("Ask a question...")

    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.write(user_input)

        # --- SAFETY GATE: always check risk BEFORE generating an answer ---
        risk = safety.classify_risk(user_input)

        if risk == "emergency":
            response = safety.EMERGENCY_MESSAGE
        else:
            result = rag.retrieve_info(user_input)
            if not result["chunks"]:
                response = "The requested information is not available in the verified dataset."
            else:
                # TODO: replace this with a real LLM call using safety.SYSTEM_PROMPT
                # + result["chunks"] as context. For now, show retrieved chunks directly.
                response = "\n\n".join(result["chunks"])
                response += "\n\nSources: " + ", ".join(name for name, _ in result["sources"])
                if risk == "moderate":
                    response += "\n\n*If symptoms persist or worsen, please consult a healthcare professional.*"

        st.session_state.messages.append({"role": "assistant", "content": response})
        with st.chat_message("assistant"):
            st.write(response)

# =========================================================================
# TAB 4 — Multi-Drug Interaction Checker
# =========================================================================
with tab4:
    st.subheader("Check interactions between two medicines")

    medicine_names = rag.get_medicine_names()
    col1, col2 = st.columns(2)
    with col1:
        drug_a = st.selectbox("First medicine", medicine_names, key="drug_a")
    with col2:
        drug_b = st.selectbox("Second medicine", medicine_names, key="drug_b")

    if st.button("Check Interaction"):
        if drug_a == drug_b:
            st.warning("Please select two different medicines.")
        else:
            result = safety.check_interaction(drug_a, drug_b)
            severity_colors = {
                "none": "🟢", "mild": "🟡", "moderate": "🟠", "severe": "🔴"
            }
            badge = severity_colors.get(result["severity"], "⚪")
            st.write(f"{badge} **Severity: {result['severity'].capitalize()}**")
            st.write(result["explanation"])
