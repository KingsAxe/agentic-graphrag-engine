import fitz  # PyMuPDF
import os

class DocumentParser:
    @staticmethod
    def parse_file(file_path: str, mime_type: str) -> str:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File {file_path} not found.")

        if mime_type == "application/pdf":
            return DocumentParser._parse_pdf(file_path)
        elif mime_type == "text/plain":
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        else:
            raise ValueError(f"Unsupported mime type: {mime_type}")

    @staticmethod
    def _parse_pdf(file_path: str) -> str:
        doc = fitz.open(file_path)
        text_content = []
        for page in doc:
            text_content.append(page.get_text())
        doc.close()
        return "\n".join(text_content)
