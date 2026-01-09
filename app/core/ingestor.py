import hashlib
import os
from langchain_community.embeddings import HuggingFaceBgeEmbeddings
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter


try:
    from utils.helpers import clean_text
except ImportError:
    from app.utils.helpers import clean_text

# from app.utils.helpers import clean_text


class DocumentIngestor:
    def __init__(self, model_folder: str = None):

        # Convert to absolute path so HuggingFace knows it's a local folder
        abs_path = os.path.abspath(model_folder)

        # Fail-safe: if None is passed, use a hardcoded fallback or raise a clearer error
        if abs_path is None:
            raise ValueError("model_folder path cannot be None. Check your .env file.")
            
        self.embeddings = HuggingFaceBgeEmbeddings(
            model_name=model_folder,
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=100
        )

    def calculate_hash(self, file_path: str):
        """Generate a SHA-256 hash of the file to prevent duplicates."""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def process_pdf(self, file_path: str):
        """Extracts text and splits into chunks."""
        loader = PyMuPDFLoader(file_path)
        documents = loader.load()

        # CLEAN THE TEXT IN EACH DOCUMENT OBJECT
        for doc in documents:
            doc.page_content = clean_text(doc.page_content)

        chunks = self.text_splitter.split_documents(documents)
        return chunks