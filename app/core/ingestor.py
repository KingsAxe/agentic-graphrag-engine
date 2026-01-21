import hashlib
import os
from typing import List, Any

from langchain_community.document_loaders import PyMuPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

try:
    from utils.helpers import clean_text
except ImportError:
    from app.utils.helpers import clean_text

from app.database.connection import get_vector_store


class DocumentIngestor:
    def __init__(
        self,
        db_url: str,
        embedding_path: str,
        chunk_size: int = 1000,
        chunk_overlap: int = 100,
    ):
        if not db_url:
            raise ValueError("db_url cannot be empty. Check DATABASE_URL.")
        if not embedding_path:
            raise ValueError("embedding_path cannot be empty. Check EMBEDDING_MODEL_PATH.")

        self.db_url = db_url
        self.embedding_path = embedding_path

        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )

        # Create vector store once for this ingestor instance
        self.vector_store = get_vector_store(self.db_url, self.embedding_path)

    def calculate_hash(self, file_path: str) -> str:
        """Generate a SHA-256 hash of the file to prevent duplicates."""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def process_pdf(self, file_path: str) -> List[Any]:
        """Extract text and split into chunks."""
        loader = PyMuPDFLoader(file_path)
        documents = loader.load()

        # Clean text in each document
        for doc in documents:
            doc.page_content = clean_text(doc.page_content)

        chunks = self.text_splitter.split_documents(documents)

        # Ensure metadata has source + page for citations
        for c in chunks:
            c.metadata = c.metadata or {}
            c.metadata["source"] = c.metadata.get("source") or os.path.basename(file_path)
            # PyMuPDFLoader commonly uses 'page' in metadata; keep it if present
            if "page" not in c.metadata and "page_number" in c.metadata:
                c.metadata["page"] = c.metadata["page_number"]

        return chunks

    def ingest(self, file_path: str) -> bool:
        """
        Ingest a PDF into PGVector.
        - Splits into chunks
        - Adds to vectorstore with metadata
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        file_hash = self.calculate_hash(file_path)
        chunks = self.process_pdf(file_path)

        # Tag chunks with a stable file hash so you can dedupe later if you want
        for c in chunks:
            c.metadata["file_hash"] = file_hash

        # This writes into langchain_pg_embedding + langchain_pg_collection
        self.vector_store.add_documents(chunks)

        return True
