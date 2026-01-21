import streamlit as st
from ui_utils import get_json, post_json, wait_for_backend

st.header("Lab Notebook")

if not wait_for_backend():
    st.warning("Backend not reachable.")
    st.stop()

session_id = st.text_input("Session ID", value=st.session_state.get("session_id", ""))

if st.button("Load entries"):
    st.session_state["entries"] = get_json(f"/notebook/{session_id}")

entries = st.session_state.get("entries", [])
if not entries:
    st.caption("No entries loaded yet.")
    st.stop()

for e in entries:
    with st.container(border=True):
        st.write(f"**Entry #{e.get('id')}** • status: `{e.get('verification_status')}`")
        st.write("**Query:**", e.get("query_text", ""))
        st.write("**Answer:**", e.get("answer_text", ""))

        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            status = st.selectbox(
                "Set status",
                options=["pending", "verified", "rejected"],
                index=["pending", "verified", "rejected"].index(e.get("verification_status", "pending")),
                key=f"status_{e.get('id')}",
            )
        with col2:
            notes = st.text_input("Notes", value=e.get("user_notes") or "", key=f"notes_{e.get('id')}")
        with col3:
            if st.button("Apply", key=f"apply_{e.get('id')}"):
                post_json("/verify", {"entry_id": e["id"], "status": status, "notes": notes})
                st.success("Updated.")
