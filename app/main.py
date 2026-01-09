import streamlit as st
from core.model_manager import ModelManager
from core.ingestor import DocumentIngestor
from core.rag_chain import RAGEngine
from database.connection import get_vector_store, get_indexed_files

import os
from dotenv import load_dotenv, find_dotenv

# --- PAGE CONFIG ---
st.set_page_config(page_title="Local Knowledge Engine", layout="wide")

# Custom CSS for that "Clean Gray" look
st.markdown("""
    <style>
    .stChatFloatingInputContainer { background-color: #FFFFFF; }
    .stChatMessage { border-radius: 10px; border: 1px solid #E0E0E0; margin-bottom: 10px; }
    [data-testid="stSidebar"] { border-right: 1px solid #E0E0E0; }
    </style>
""", unsafe_allow_html=True)

# --- INITIALIZATION ---
load_dotenv(find_dotenv())
DB_URL = os.getenv("DATABASE_URL")
EMBEDDING_PATH = os.getenv("EMBEDDING_MODEL_PATH")
MODEL_DIR = "./models/llm"

# Debugging: This will print exactly what Python sees in your terminal
print(f"DEBUG: Current Directory: {os.getcwd()}")
print(f"DEBUG: Looking for .env at: {find_dotenv()}")
print(f"DEBUG: Found EMBEDDING_MODEL_PATH: {EMBEDDING_PATH}")

if EMBEDDING_PATH is None:
    st.error("❌ CRITICAL: EMBEDDING_MODEL_PATH not found in .env file.")
    st.stop() # Stops Streamlit from running with a None value

ingestor = DocumentIngestor(EMBEDDING_PATH)

model_manager = ModelManager(MODEL_DIR)
ingestor = DocumentIngestor(EMBEDDING_PATH)
vector_store = get_vector_store(DB_URL, EMBEDDING_PATH)

# --- SIDEBAR: Settings & Upload ---
with st.sidebar:
    st.title("⚙️ System Control")
    
    # 1. Model Selection (The "Flexible" Part)
    available_models = model_manager.list_available_models()
    selected_model_file = st.selectbox("Select LLM Brain", available_models)
    
    st.divider()
    
    # 2. Document Upload (The "Knowledge" Part)
    st.subheader("Add to Knowledge Base")
    uploaded_file = st.file_uploader("Upload PDF", type="pdf")
    if uploaded_file:
        with st.spinner("Analyzing and indexing..."):
            # Save temp file
            temp_path = f"./data/{uploaded_file.name}"
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            # Process & Embed
            chunks = ingestor.process_pdf(temp_path)
            vector_store.add_documents(chunks)
            st.success("Knowledge base updated!")

    st.sidebar.title("📚 Knowledge Base")
    # Fetch files currently in Postgres
    indexed_files = get_indexed_files(DB_URL)

    if indexed_files:
        st.sidebar.write("### Documents in Memory:")
        for f in indexed_files:
            # Clean up the path to just show the filename
            filename = os.path.basename(f)
            st.sidebar.success(f"📄 {filename}")
    else:
        st.sidebar.info("No documents in memory yet.")
        

# --- MAIN CHAT INTERFACE ---
st.title("💬 Local RAG Chat")
st.caption("Private, Persistent, and Context-Aware Knowledge Assistant")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Display history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# # Chat Input
# if prompt := st.chat_input("Ask about your documents..."):
#     st.session_state.messages.append({"role": "user", "content": prompt})
#     with st.chat_message("user"):
#         st.markdown(prompt)

#     # --- RAG Logic ---
#     with st.chat_message("assistant"):
#         llm = model_manager.load_model(selected_model_file)
#         engine = RAGEngine(llm, vector_store, DB_URL)
#         chain = engine.create_chain(session_id="local_user_1")
        
#         # The chain now looks for "input" as the primary user message
#         response = chain.invoke({"input": prompt})
#         # response = chain.invoke({"question": prompt})
#         answer = response["answer"]
        
#         st.markdown(answer)
        
#         # Traceability Section
#         with st.expander("View Sources"):
#             for doc in response["source_documents"]:
#                 st.write(f"- {doc.metadata['source']} (Page {doc.metadata.get('page', 'N/A')})")
        
#         st.session_state.messages.append({"role": "assistant", "content": answer})

# Chat Input
if prompt := st.chat_input("Ask about your documents..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # --- RAG Logic ---
    with st.chat_message("assistant"):
        # 1. Setup Engine and Chain
        llm = model_manager.load_model(selected_model_file)
        engine = RAGEngine(llm, vector_store, DB_URL)
        
        # Consistent session_id allows memory to persist across app restarts
        current_session = "local_user_1" 
        chain = engine.create_chain(session_id=current_session)
        
        # 2. Retrieve History from Postgres
        history_manager = engine.get_chat_history(current_session)
        existing_history = history_manager.messages

        # 3. Invoke Chain with all required variables
        # This solves the KeyError: 'chat_history'
        response = chain.invoke({
            "input": prompt,
            "chat_history": existing_history
        })
        
        answer = response["answer"]
        st.markdown(answer)

        # 4. Save the interaction to Database Memory
        history_manager.add_user_message(prompt)
        history_manager.add_ai_message(answer)
        
        # 5. Traceability Section
        # Note: new chains return sources in the "context" key
        if "context" in response:
            with st.expander("View Sources"):
                for doc in response["context"]:
                    source_name = doc.metadata.get('source', 'Unknown')
                    page_num = doc.metadata.get('page', 'N/A')
                    st.write(f"- {source_name} (Page {page_num})")
        
        st.session_state.messages.append({"role": "assistant", "content": answer})