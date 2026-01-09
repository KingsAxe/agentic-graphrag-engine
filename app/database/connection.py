from langchain_postgres import PGVector
from langchain_huggingface import HuggingFaceEmbeddings

def get_vector_store(db_url, embedding_path):
    embeddings = HuggingFaceEmbeddings(
        model_name=embedding_path,
        model_kwargs={'device': 'cpu'}
    )
    
    return PGVector(
        embeddings=embeddings,
        collection_name="pdf_knowledge",
        connection=db_url,
        use_jsonb=True,
    )