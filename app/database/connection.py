import psycopg2
from langchain_postgres import PGVector
from langchain_huggingface import HuggingFaceEmbeddings


def normalize_pg_url(db_url: str) -> str:
    return (
        db_url.replace("postgresql+psycopg://", "postgresql://")
              .replace("postgresql+psycopg2://", "postgresql://")
    )


def get_vector_store(db_url: str, embedding_path: str):
    db_url = normalize_pg_url(db_url)

    embeddings = HuggingFaceEmbeddings(
        model_name=embedding_path,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )

    return PGVector(
        embeddings=embeddings,
        collection_name="pdf_knowledge",
        connection=db_url,
        use_jsonb=True,
    )


def get_indexed_files(db_url: str):
    db_url = normalize_pg_url(db_url)
    try:
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()

        query = "SELECT DISTINCT cmetadata->>'source' FROM langchain_pg_embedding;"
        cur.execute(query)

        results = [row[0] for row in cur.fetchall() if row[0]]

        cur.close()
        conn.close()
        return results
    except Exception as e:
        print(f"Error fetching indexed files from DB: {e}")
        return []
