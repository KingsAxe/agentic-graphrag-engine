import logging
from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI
from src.core.config import settings


logger = logging.getLogger(__name__)


def llm_is_configured() -> bool:
    provider = settings.LLM_PROVIDER.lower()

    if provider == "mock":
        return True

    if provider == "groq":
        return bool(settings.GROQ_API_KEY.strip())

    if provider == "ollama":
        return bool(settings.LLM_BASE_URL.strip()) and bool(settings.LLM_MODEL.strip())

    return False


def get_llm_display_name() -> str:
    return f"{settings.LLM_PROVIDER}:{settings.LLM_MODEL}"


def build_chat_llm(temperature: float = 0):
    provider = settings.LLM_PROVIDER.lower()

    if provider == "groq":
        if not settings.GROQ_API_KEY:
            raise ValueError("LLM provider is groq but GROQ_API_KEY is not set.")

        logger.info("Initializing Groq chat model %s", settings.LLM_MODEL)
        return ChatGroq(
            groq_api_key=settings.GROQ_API_KEY,
            model_name=settings.LLM_MODEL,
            temperature=temperature,
        )

    if provider == "ollama":
        logger.info(
            "Initializing Ollama chat model %s via %s",
            settings.LLM_MODEL,
            settings.LLM_BASE_URL,
        )
        return ChatOpenAI(
            model=settings.LLM_MODEL,
            temperature=temperature,
            base_url=settings.LLM_BASE_URL,
            api_key=settings.LLM_API_KEY,
        )

    raise ValueError(f"Unsupported LLM_PROVIDER: {settings.LLM_PROVIDER}")
