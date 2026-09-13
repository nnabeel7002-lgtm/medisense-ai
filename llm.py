"""
llm.py — Generates the final grounded answer from retrieved chunks.
Owner: Nabeeha
Using: Groq API (fast inference, OpenAI-compatible)
"""
import os
from groq import Groq
import safety  # for SYSTEM_PROMPT

def _get_api_key():
    # Works locally (.env) and on Streamlit Cloud (secrets) without code changes
    key = os.getenv("GROQ_API_KEY")
    if key:
        return key
    try:
        import streamlit as st
        return st.secrets["GROQ_API_KEY"]
    except Exception:
        return None

client = Groq(api_key=_get_api_key())

def generate_answer(query: str, chunks: list[str]) -> str:
    """Given retrieved chunks and the user's question, generate a grounded answer."""
    context = "\n\n".join(chunks)
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",  # fast + capable, good default on Groq
            max_tokens=400,
            messages=[
                {"role": "system", "content": safety.SYSTEM_PROMPT},
                {"role": "user", "content": f"Context:\n{context}\n\nUser question: {query}"}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        # Never let an API failure crash the app — fail safe, not loud
        return "Sorry, I couldn't generate a response right now. Here's the raw retrieved information:\n\n" + context
