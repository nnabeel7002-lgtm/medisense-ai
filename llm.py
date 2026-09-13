"""
llm.py — Generates the final grounded answer from retrieved chunks.
Owner: Nabeeha
"""
import os
import anthropic
import safety  # for SYSTEM_PROMPT

def _get_api_key():
    # Works locally (.env) and on Streamlit Cloud (secrets) without code changes
    key = os.getenv("ANTHROPIC_API_KEY")
    if key:
        return key
    try:
        import streamlit as st
        return st.secrets["ANTHROPIC_API_KEY"]
    except Exception:
        return None

client = anthropic.Anthropic(api_key=_get_api_key())

def generate_answer(query: str, chunks: list[str]) -> str:
    """Given retrieved chunks and the user's question, generate a grounded answer."""
    context = "\n\n".join(chunks)
    try:
        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=400,
            system=safety.SYSTEM_PROMPT,
            messages=[{
                "role": "user",
                "content": f"Context:\n{context}\n\nUser question: {query}"
            }]
        )
        return message.content[0].text
    except Exception as e:
        # Never let an API failure crash the app — fail safe, not loud
        return "Sorry, I couldn't generate a response right now. Here's the raw retrieved information:\n\n" + context
