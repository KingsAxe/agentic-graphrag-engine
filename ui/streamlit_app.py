import streamlit as st
from ui_utils import wait_for_backend, set_api_base, api_base

st.set_page_config(
    page_title="Sovereign Research Engine",
    page_icon="🧠",
    layout="wide",
)

# Top bar
col1, col2, col3 = st.columns([2, 2, 1])
with col1:
    st.title("Sovereign Research Engine")
    st.caption("Local • Audited • Epistemic integrity")

with col2:
    st.text_input("API Base URL", value=api_base(), key="api_base_input")
    if st.button("Use API URL"):
        set_api_base(st.session_state["api_base_input"])

with col3:
    ok = wait_for_backend()
    st.metric("Backend", "Ready ✅" if ok else "Not reachable ❌")

st.divider()

st.info("Use the left sidebar to navigate: Workbench → Ingest → Notebook → Settings.")
