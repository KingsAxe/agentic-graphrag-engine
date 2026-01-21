import streamlit as st
from ui_utils import get_json, post_json, wait_for_backend

st.header("Settings")

if not wait_for_backend():
    st.warning("Backend not reachable.")
    st.stop()

# If your FastAPI already exposes /settings GET/POST, this works immediately.
# If not, tell me and I’ll paste the tiny FastAPI addition.

try:
    current = get_json("/settings")
except Exception as e:
    st.error("Your backend does not expose /settings yet.")
    st.code(str(e))
    st.stop()

llm_models_dir = st.text_input("LLM models directory", value=current.get("llm_models_dir", ""))
default_llm_model = st.text_input("Default model filename (optional)", value=current.get("default_llm_model", "") or "")

if st.button("Save", type="primary", disabled=not llm_models_dir.strip()):
    post_json("/settings", {"llm_models_dir": llm_models_dir, "default_llm_model": default_llm_model or None})
    st.success("Saved.")
