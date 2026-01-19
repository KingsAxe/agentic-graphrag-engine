import streamlit as st
import os
from core.model_manager import ModelManager
from core.ingestor import DocumentIngestor
from core.rag_chain import RAGEngine
from database.connection import get_vector_store, get_indexed_files
from database.research_manager import ResearchManager


# --- Page Configuration ---
st.set_page_config(page_title="Sovereign Research Engine", layout="wide")
st.title("🔬 Sovereign Research Engine")

# --- Initialize Managers ---
# These should ideally be cached to prevent reloading on every click
model_manager = ModelManager()
DB_URL = os.getenv("DATABASE_URL", "postgresql://user:pass@localhost:5432/vectors")
EMBED_PATH = os.getenv("EMBEDDING_MODEL_PATH", "models/embeddings/bge-small-en-v1.5")
res_manager = ResearchManager(DB_URL)

# --- Session State Initialization ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "session_id" not in st.session_state:
    st.session_state.session_id = "researcher_alpha_01"


tab1, tab2 = st.tabs(["Research Chat", "📓 Lab Notebook"])

with tab2:
    st.header("Crystallized Knowledge")
    verified_data = res_manager.get_session_entries(st.session_state.session_id)
    for entry in verified_data:
        status_color = "🟢" if entry['verification_status'] == 'verified' else "⚪"
        with st.expander(f"{status_color} {entry['query_text'][:50]}..."):
            st.write(f"**Answer:** {entry['answer_text']}")
            st.json(entry['citations'])
            

# --- Sidebar: Research Controls ---
with st.sidebar:
    st.header("⚙️ Research Parameters")
    
    # 1. Model Selection
    available_models = [f for f in os.listdir("models/llms") if f.endswith(".gguf")]
    selected_model = st.selectbox("Select Inference Model", available_models)
    
    # 2. Retrieval Mode (Phase 2)
    retrieval_mode = st.radio(
        "Retrieval Strategy",
        ["precision", "exploratory"],
        help="Precision: Hybrid Keyword/Vector search. Exploratory: Multi-query expansion."
    )
    
    st.divider()
    
    # 3. Knowledge Base Status
    st.subheader("📚 Indexed Documents")
    indexed_files = get_indexed_files(DB_URL)
    if indexed_files:
        for f in indexed_files:
            fname = os.path.basename(f)
            st.caption(f"✅ {fname}")
    else:
        st.info("No documents indexed.")

    # 4. Upload New Evidence
    uploaded_file = st.file_uploader("Ingest Research PDF", type="pdf")
    if uploaded_file:
        with st.spinner("Analyzing and Vectorizing..."):
            ingestor = DocumentIngestor(DB_URL, EMBED_PATH)
            # Save temp file
            temp_path = f"data/raw/{uploaded_file.name}"
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            success = ingestor.ingest(temp_path)
            if success:
                st.success("Document integrated into Knowledge Base.")
                st.rerun()

# --- Main Chat UI ---

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "audit" in message:
            with st.expander("Audit Trail"):
                st.json(message["audit"])

# User Input
if prompt := st.chat_input("Enter research query..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # --- Generation Logic ---
    with st.chat_message("assistant"):
        with st.spinner("Synthesizing evidence..."):
            # 1. Init Engine
            llm = model_manager.load_model(selected_model)
            vector_store = get_vector_store(DB_URL, EMBED_PATH)
            engine = RAGEngine(llm, vector_store, DB_URL)
            
            # 2. Get History & Create Chain
            history_manager = engine.get_chat_history(st.session_state.session_id)
            chain = engine.create_chain(mode=retrieval_mode)
            
            # 3. Invoke Structured Chain
            # Note: We pass the history explicitly to fulfill the prompt variables
            response = chain.invoke({
                "input": prompt, 
                "chat_history": history_manager.messages
            })
            
            # 4. Display Result
            st.markdown(response.answer)
            
            # Phase 1: Epistemic Transparency UI
            belief = response.belief_report
            with st.expander("🛡️ Epistemic Audit Report"):
                col1, col2 = st.columns(2)
                col1.metric("Confidence Score", f"{int(belief.epistemic_score * 100)}%")
                col2.write(f"**Evidence Quality:** {belief.evidence_quality}")
                st.write(f"**Internal Reasoning:** {belief.reasoning_process}")
                if belief.hallucination_risk.lower() != "none":
                    st.warning(f"**Identified Risks:** {belief.hallucination_risk}")
            
            if response.citations:
                st.caption(f"**Sources:** {', '.join(response.citations)}")

            # --- Verification UI ---
            entry_id = res_manager.save_entry(st.session_state.session_id, prompt, response)

            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ Verify & Crystallize", key=f"v_{entry_id}"):
                    res_manager.verify_entry(entry_id, "verified")
                    st.success("Added to Lab Notebook")
            with col2:
                if st.button("❌ Reject / Hallucination", key=f"r_{entry_id}"):
                    res_manager.verify_entry(entry_id, "rejected")
                    st.warning("Entry marked as invalid.")


            # 5. Persistence
            history_manager.add_user_message(prompt)
            history_manager.add_ai_message(response.answer)
            
            # Store in session state including the audit for UI persistence
            st.session_state.messages.append({
                "role": "assistant", 
                "content": response.answer,
                "audit": belief.dict(),
                "citations": response.citations
            })