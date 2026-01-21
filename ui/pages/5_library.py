import streamlit as st
from ui_utils import get_json, wait_for_backend

st.header("Library")

if not wait_for_backend():
    st.warning("Backend not reachable. Start FastAPI first.")
    st.stop()

payload = get_json("/library")
docs = payload.get("documents", [])

if not docs:
    st.info("No documents found in the vault yet. Ingest a PDF first.")
    st.stop()

for d in docs:
    with st.container(border=True):
        st.subheader(d.get("filename", "Unknown"))
        st.caption(
            f"Chunks: {d.get('chunks','—')} • "
            f"Pages: {d.get('max_page','—')} • "
            f"Available: {'✅' if d.get('available') else '❌'}"
        )
        preview = d.get("preview", "")
        if preview:
            st.write(preview)
        st.code(d.get("stored_path", ""), language="text")
