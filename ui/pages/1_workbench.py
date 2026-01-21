import uuid
import streamlit as st
from ui_utils import get_json, post_json, wait_for_backend

st.header("Workbench")

if "session_id" not in st.session_state:
    st.session_state["session_id"] = str(uuid.uuid4())

left, right = st.columns([2, 1], vertical_alignment="top")

with right:
    st.subheader("Session")
    st.text_input("session_id", key="session_id")
    st.caption("Tip: keep a session per topic/project.")

    st.subheader("Model + Mode")
    backend_ok = wait_for_backend()
    if not backend_ok:
        st.warning("Backend not reachable. Start FastAPI: uvicorn app.api:app --host 127.0.0.1 --port 8000")
        st.stop()

    models_payload = get_json("/models")
    models = models_payload.get("models", [])
    default_model = models_payload.get("default", "")

    model_name = st.selectbox(
        "Model",
        options=["(default)"] + models,
        index=(1 if default_model in models else 0),
    )
    mode = st.selectbox("Mode", options=["precision", "exploratory"], index=0)

with left:
    st.subheader("Ask")
    prompt = st.text_area("Your question", height=140, placeholder="Ask something grounded in your PDFs…")

    run = st.button("Run", type="primary", disabled=not prompt.strip())
    if run:
        payload = {
            "input_text": prompt,
            "session_id": st.session_state["session_id"],
            "mode": mode,
        }
        # Optional: only send model_name if user chose a specific one
        if model_name != "(default)":
            payload["model_name"] = model_name

        with st.spinner("Thinking…"):
            out = post_json("/query", payload)

        data = out.get("data", {})
        st.session_state["last_entry_id"] = out.get("entry_id", None)
        st.session_state["last_response"] = data

    data = st.session_state.get("last_response")
    if data:
        st.subheader("Answer")
        st.write(data.get("answer", ""))

        st.divider()

        st.subheader("Belief Report")
        br = data.get("belief_report", {}) or {}
        c1, c2, c3 = st.columns(3)
        c1.metric("Epistemic Score", br.get("epistemic_score", "—"))
        c2.write(f"**Evidence Quality:** {br.get('evidence_quality','—')}")
        c3.write(f"**Hallucination Risk:** {br.get('hallucination_risk','—')}")

        with st.expander("Reasoning Process"):
            st.write(br.get("reasoning_process", ""))

        st.subheader("Citations")
        citations = data.get("citations", []) or []
        if citations:
            for c in citations:
                st.code(c, language="text")
        else:
            st.caption("No citations returned.")
