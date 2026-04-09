from src.core.config import settings


def _is_present(value: str) -> bool:
    return bool(value and value.strip())


def get_launch_readiness() -> dict:
    llm_provider = settings.LLM_PROVIDER.lower()
    missing = []

    if llm_provider == "groq":
        configured = _is_present(settings.GROQ_API_KEY)
        if not configured:
            missing.append("GROQ_API_KEY")
    elif llm_provider == "mock":
        configured = True
    elif llm_provider == "ollama":
        configured = _is_present(settings.LLM_BASE_URL) and _is_present(settings.LLM_MODEL)
        if not _is_present(settings.LLM_BASE_URL):
            missing.append("LLM_BASE_URL")
        if not _is_present(settings.LLM_MODEL):
            missing.append("LLM_MODEL")
    else:
        configured = False
        missing.append("LLM_PROVIDER")

    return {
        "project_name": settings.PROJECT_NAME,
        "api_prefix": settings.API_V1_STR,
        "llm": {
            "provider": llm_provider,
            "model": settings.LLM_MODEL,
            "base_url": settings.LLM_BASE_URL if llm_provider == "ollama" else None,
            "configured": configured,
            "blocking": not configured,
            "missing": missing,
        },
        "services": {
            "postgres": {
                "host": settings.POSTGRES_SERVER,
                "port": settings.POSTGRES_PORT,
                "configured": _is_present(settings.POSTGRES_SERVER),
            },
            "neo4j": {
                "uri": settings.NEO4J_URI,
                "configured": _is_present(settings.NEO4J_URI),
            },
            "qdrant": {
                "host": settings.QDRANT_HOST,
                "port": settings.QDRANT_PORT,
                "configured": _is_present(settings.QDRANT_HOST),
            },
            "redis": {
                "host": settings.REDIS_HOST,
                "port": settings.REDIS_PORT,
                "configured": _is_present(settings.REDIS_HOST),
            },
        },
    }
