import logging
from langchain_groq import ChatGroq
from src.core.config import settings
from src.models.graph import GraphExtraction

logger = logging.getLogger(__name__)

class GraphExtractorService:
    def __init__(self):
        if settings.GROQ_API_KEY:
            self.llm = ChatGroq(
                groq_api_key=settings.GROQ_API_KEY,
                model_name=settings.LLM_MODEL,
                temperature=0
            )
            # Use LangChain structured output
            self.extractor = self.llm.with_structured_output(GraphExtraction)
        else:
            self.extractor = None
            logger.warning("GROQ_API_KEY not set. Graph extraction will fail.")

    def extract_from_text(self, text: str) -> GraphExtraction:
        if not self.extractor:
            logger.error("Skipping extraction: No Groq client initialized (missing GROQ_API_KEY).")
            return GraphExtraction()

        prompt = f"""
        Analyze the following text fragment. 
        Extract all concrete Entities, the Relationships between those entities, and key factual Claims.
        Be highly precise and objective. 
        Text chunk:
        '''
        {text}
        '''
        """

        try:
            extraction = self.extractor.invoke(prompt)
            return extraction
        except Exception as e:
            logger.error(f"Groq Extraction failed: {e}")
            return GraphExtraction()

# Singleton
extractor = None

def get_graph_extractor() -> GraphExtractorService:
    global extractor
    if extractor is None:
        extractor = GraphExtractorService()
    return extractor
