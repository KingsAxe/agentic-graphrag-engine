class TextChunker:
    @staticmethod
    def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
        """
        Simple word-based chunker with overlap.
        For production, a recursive character text splitter or semantic splitter is preferred.
        """
        words = text.split()
        chunks = []
        
        i = 0
        while i < len(words):
            end = min(i + chunk_size, len(words))
            chunk = " ".join(words[i:end])
            if chunk.strip():
                chunks.append(chunk)
            i += (chunk_size - overlap)
            
        return chunks
