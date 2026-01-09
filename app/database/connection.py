import psycopg2
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

def get_indexed_files(db_url):
    """
    Queries the underlying LangChain Postgres table to find 
    unique document sources.
    """
    try:
        # Connect directly via psycopg2 for a quick raw SQL query
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()
        
        # LangChain's PGVector uses 'langchain_pg_embedding' as the default table.
        # It stores metadata in a JSONB column named 'cmetadata'.
        query = "SELECT DISTINCT cmetadata->>'source' FROM langchain_pg_embedding;"
        
        cur.execute(query)
        # Fetch all results and filter out None
        results = [row[0] for row in cur.fetchall() if row[0]]
        
        cur.close()
        conn.close()
        return results
    except Exception as e:
        print(f"Error fetching indexed files from DB: {e}")
        return []