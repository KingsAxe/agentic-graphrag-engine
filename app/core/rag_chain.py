from langchain.chains import ConversationalRetrievalChain
from langchain.memory import PostgresChatMessageHistory

class RAGEngine:
    def __init__(self, llm, vector_store, db_connection_str):
        self.llm = llm
        self.vector_store = vector_store
        self.db_conn = db_connection_str

    def get_chat_history(self, session_id: str):
        """Retrieves history directly from Postgres."""
        return PostgresChatMessageHistory(
            connection_string=self.db_conn,
            session_id=session_id
        )

    def create_chain(self, session_id: str):
        history = self.get_chat_history(session_id)
        
        # This chain automatically handles:
        # 1. Rewriting the question based on history
        # 2. Searching pgvector
        # 3. Generating the final answer
        return ConversationalRetrievalChain.from_llm(
            llm=self.llm,
            retriever=self.vector_store.as_retriever(search_kwargs={"k": 3}),
            memory=history,
            return_source_documents=True,
            verbose=True
        )