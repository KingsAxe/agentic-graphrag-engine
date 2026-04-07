from typing import List, Any
from pydantic import BaseModel, Field

from typing import List, Any
from pydantic import BaseModel, Field

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnableLambda
from langchain_community.retrievers import BM25Retriever

from langchain_postgres import PostgresChatMessageHistory

# v1: retrievers moved to langchain-classic
from langchain_classic.retrievers import MultiQueryRetriever, EnsembleRetriever


import psycopg
from langchain_postgres import PostgresChatMessageHistory
import uuid

def _normalize_pg_url(db_url: str) -> str:
    # If you ever used SQLAlchemy style, normalize for psycopg
    return (
        db_url.replace("postgresql+psycopg://", "postgresql://")
              .replace("postgresql+psycopg2://", "postgresql://")
    )

def _session_to_uuid(session_id: str) -> str:
    try:
        return str(uuid.UUID(session_id))
    except ValueError:
        # Deterministic UUID from an arbitrary string
        return str(uuid.uuid5(uuid.NAMESPACE_URL, session_id))



# --- PHASE 1: Epistemic Schemas ---

class BeliefReport(BaseModel):
    """The engine's self-audit of its own retrieval and reasoning."""
    epistemic_score: float = Field(description="Confidence score between 0.0 and 1.0.")
    evidence_quality: str = Field(description="Assessment of whether the retrieved chunks were relevant or noisy.")
    hallucination_risk: str = Field(description="Self-identified gaps where the model had to infer beyond the text.")
    reasoning_process: str = Field(description="Internal monologue of how the retrieved facts led to the answer.")

class ResearchResponse(BaseModel):
    """The structured output for a professional research assistant."""
    answer: str = Field(description="The final synthesized answer grounded in evidence.")
    belief_report: BeliefReport = Field(description="The audit report for this specific generation.")
    citations: List[str] = Field(description="List of document names/pages used as primary evidence.")

# --- RAG Engine Class ---

class RAGEngine:
    def __init__(self, llm, vector_store, db_url: str):
        self.llm = llm
        self.vector_store = vector_store
        self.db_url = db_url

        # We wrap the LLM with structured output to ensure we get our ResearchResponse
        # This is the 'Masterpiece' standard for 2026
        self.structured_llm = self.llm.with_structured_output(ResearchResponse)

    

    def get_chat_history(self, session_id: str):
        conninfo = _normalize_pg_url(self.db_url)

        # Create a short-lived connection per request (safe for now)
        conn = psycopg.connect(conninfo)

        try:
            # Test if table exists  
            # Ensure table exists (safe to call repeatedly during dev)
            PostgresChatMessageHistory.create_tables(conn, "chat_history")
        except Exception:
            pass

        session_uuid = _session_to_uuid(session_id)

        history = PostgresChatMessageHistory(
            "chat_history",
            session_uuid,
            sync_connection=conn
        )

        # attach connection so API can close it after using history
        history._sre_conn = conn
        return history
    




    def _get_retriever(self, mode: str = "precision", documents: List[Any] = None):
        base_vector_retriever = self.vector_store.as_retriever(search_kwargs={"k": 5})
        if mode == "exploratory":
            return MultiQueryRetriever.from_llm(retriever=base_vector_retriever, llm=self.llm)
        if mode == "precision" and documents:
            bm25 = BM25Retriever.from_documents(documents)
            bm25.k = 3
            return EnsembleRetriever(retrievers=[bm25, base_vector_retriever], weights=[0.4, 0.6])
        return base_vector_retriever



    def create_chain(self, mode: str = "precision", documents: List[Any] = None, verified_knowledge: str = ""):
        # 1. Define the System Instructions with Recursive Grounding
        system_prompt = (
            "You are a Sovereign Research Assistant. Your goal is high epistemic integrity.\n\n"
            "--- PRIORITY 1: VERIFIED KNOWLEDGE ---\n"
            "The following information has been verified by the researcher. Treat this as absolute truth:\n"
            "{verified_knowledge}\n\n"
            "--- PRIORITY 2: RAW PDF CONTEXT ---\n"
            "Use the following document chunks to support your answer:\n"
            "{context}\n\n"
            "INSTRUCTIONS:\n"
            "1. Synthesize a direct answer to the user's input.\n"
            "2. If Verified Knowledge conflicts with Raw PDF Context, prioritize Verified Knowledge.\n"
            "3. If neither contains the answer, set the 'answer' field to indicate insufficient context, and explain why in the 'reasoning_process' field.\n"
            "4. Cite specific sources and page numbers. If none, leave citations empty.\n"
        )

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
        ])

        retriever = self._get_retriever(mode, documents)

        def format_docs(docs):
            formatted = []
            for doc in docs:
                source = doc.metadata.get('source', 'Unknown')
                page = doc.metadata.get('page', 'N/A')
                formatted.append(f"[Source: {source} | Page: {page}]\n{doc.page_content}")
            return "\n\n---\n\n".join(formatted)

        # 3. Construct the LCEL Graph with verified_knowledge injection
        chain = (
            {
                # "context": (lambda x: x["input"]) | retriever | format_docs,
                "context": RunnableLambda(lambda x: x["input"]) | retriever | RunnableLambda(format_docs),
                "verified_knowledge": lambda x: x.get("verified_knowledge", "No verified knowledge available yet."),
                "input": lambda x: x["input"],
                "chat_history": lambda x: x.get("chat_history", [])
            }
            | prompt
            | self.structured_llm
        )

        return chain