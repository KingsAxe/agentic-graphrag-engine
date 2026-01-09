from langchain_classic.chains import create_history_aware_retriever, create_retrieval_chain
from langchain_classic.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_postgres import PostgresChatMessageHistory

class RAGEngine:
    def __init__(self, llm, vector_store, db_connection_str):
        self.llm = llm
        self.vector_store = vector_store
        self.db_conn = db_connection_str

    def get_chat_history(self, session_id: str):
        return PostgresChatMessageHistory(
            connection_string=self.db_conn,
            session_id=session_id,
            table_name="chat_history"
        )

    def create_chain(self, session_id: str):
        # Setup the Contextualizer (Rewrites query based on history)
        contextualize_system_prompt = (
            "Given a chat history and the latest user question "
            "which might reference context in the chat history, "
            "formulate a standalone question which can be understood "
            "without the chat history."
        )
        contextualize_prompt = ChatPromptTemplate.from_messages([
            ("system", contextualize_system_prompt),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
        ])
        
        history_aware_retriever = create_history_aware_retriever(
            self.llm, self.vector_store.as_retriever(), contextualize_prompt
        )

        # Setup the Q&A Chain (Generates final answer)
        system_prompt = (
            "You are an assistant for question-answering tasks. "
            "Use the following pieces of retrieved context to answer the question. "
            "\n\n"
            "{context}"
        )
        qa_prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
        ])
        
        question_answer_chain = create_stuff_documents_chain(self.llm, qa_prompt)

        # Combine into final Retrieval Chain
        return create_retrieval_chain(history_aware_retriever, question_answer_chain)