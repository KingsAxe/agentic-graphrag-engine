import logging
from src.core.config import settings
from src.models.graph import GraphExtraction
from src.services.llm.factory import build_chat_llm, get_llm_display_name, llm_is_configured
from src.services.llm.mock import extract_graph_from_text

logger = logging.getLogger(__name__)

class GraphExtractorService:
    def __init__(self):
        self.use_mock = settings.LLM_PROVIDER.lower() == "mock"

        if self.use_mock:
            self.extractor = None
            logger.info("Initializing graph extractor in mock mode")
            return

        if llm_is_configured():
            logger.info("Initializing graph extractor with %s", get_llm_display_name())
            self.llm = build_chat_llm(temperature=0)
            # Use LangChain structured output
            self.extractor = self.llm.with_structured_output(GraphExtraction)
        else:
            self.extractor = None
            logger.warning("LLM is not configured. Graph extraction will fail.")

    def extract_from_text(self, text: str) -> GraphExtraction:
        if self.use_mock:
            logger.info("Running mock graph extraction")
            return extract_graph_from_text(text)

        if not self.extractor:
            logger.error("Skipping extraction because no LLM client is initialized.")
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
            logger.info("Submitting text chunk for graph extraction via %s", settings.LLM_PROVIDER)
            extraction = self.extractor.invoke(prompt)
            logger.info(
                "Graph extraction completed with %s entities, %s relationships, %s claims",
                len(extraction.entities),
                len(extraction.relationships),
                len(extraction.claims),
            )
            return extraction
        except Exception as e:
            logger.exception("Graph extraction failed")
            return GraphExtraction()

# Singleton
extractor = None

def get_graph_extractor() -> GraphExtractorService:
    global extractor
    if extractor is None:
        extractor = GraphExtractorService()
    return extractor
