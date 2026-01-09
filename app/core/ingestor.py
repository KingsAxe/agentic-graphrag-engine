import hashlib
from langchain_community.embeddings import HuggingFaceBgeEmbeddings
from langchain_community.document_loaders import PyMuPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter

class DocumentIngestor:
    def __init__(self, model_folder: str):
        # Pointing to your local folder
        self.embeddings = HuggingFaceBgeEmbeddings(
            model_name=model_folder,
            model_kwargs={'device': 'cpu'}, # Switch to 'cuda' if you have a GPU
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
        chunks = self.text_splitter.split_documents(documents)
        return chunks