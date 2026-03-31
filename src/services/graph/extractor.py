import logging
from openai import OpenAI
from src.core.config import settings
from src.models.graph import GraphExtraction

logger = logging.getLogger(__name__)

class GraphExtractorService:
    def __init__(self):
        if settings.OPENAI_API_KEY:
            self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        else:
            self.client = None
            logger.warning("OPENAI_API_KEY not set. Graph extraction will fail.")

    def extract_from_text(self, text: str) -> GraphExtraction:
        if not self.client:
            logger.error("Skipping extraction: No OpenAI client initialized (missing OPENAI_API_KEY).")
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
            response = self.client.beta.chat.completions.parse(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an analytical data extraction engine. You strictly output factual, structural data."},
                    {"role": "user", "content": prompt}
                ],
                response_format=GraphExtraction,
                temperature=0.0
            )

            extraction = response.choices[0].message.parsed
            return extraction
        except Exception as e:
            logger.error(f"LLM Extraction failed: {e}")
            return GraphExtraction()

# Singleton
extractor = None

def get_graph_extractor() -> GraphExtractorService:
    global extractor
    if extractor is None:
        extractor = GraphExtractorService()
    return extractor
