import streamlit as st
from ui_utils import post_file, wait_for_backend

st.header("Ingest PDF")

if not wait_for_backend():
    st.warning("Backend not reachable.")
    st.stop()

pdf = st.file_uploader("Upload a PDF", type=["pdf"])
if pdf is not None:
    if st.button("Ingest", type="primary"):
        with st.spinner("Ingesting and embedding…"):
            res = post_file("/ingest", pdf.read(), pdf.name)
        st.success(f"✅ Ingested: {res.get('filename')}")
