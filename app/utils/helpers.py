import hashlib
import re

def generate_file_hash(file_path: str) -> str:
    """
    Generates a SHA-256 hash of a file's content.
    Used for idempotency: ensuring we don't index the same PDF twice.
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        # Read file in 4KB chunks to handle large PDFs without RAM spikes
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def clean_text(text: str) -> str:
    """
    Cleans extracted PDF text for better embedding quality.
    Removes redundant whitespaces, newlines, and artifacts.
    """
    # Replace multiple newlines with a single space
    text = re.sub(r'\n+', ' ', text)
    # Remove extra spaces
    text = re.sub(r'\s+', ' ', text)
    return text.strip()